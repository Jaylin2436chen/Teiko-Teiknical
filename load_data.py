
# This allows you to initialize the SQLite database scheme and 
# load in data from data/cell-count.csv

import csv
import sqlite3
import os

DB_PATH = "immune_trial.db"
CSV_PATH = "data/cell-count.csv"

# Adding the five immune-cell population
POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]


def init_db(conn):
    """Create the normalized relational database tables."""

    cursor = conn.cursor()

    # Creating one row for each patient
    cursor.execute("""
        CREATE TABLE subjects (
            subject_id      TEXT PRIMARY KEY,
            project         TEXT NOT NULL,
            condition       TEXT NOT NULL,
            age             INTEGER NOT NULL,
            sex             TEXT NOT NULL,
            treatment       TEXT NOT NULL,
            response        TEXT
        )
    """)

    # Creating one row for each sample and adding foreign key
    cursor.execute("""
        CREATE TABLE samples (
            sample_id                 TEXT PRIMARY KEY,
            subject_id                TEXT NOT NULL,
            sample_type               TEXT NOT NULL,
            time_from_treatment_start INTEGER NOT NULL,
            FOREIGN KEY (subject_id)
                REFERENCES subjects(subject_id)
        )
    """)

    # Adding five rows per sample, one for each cell population
    cursor.execute("""
        CREATE TABLE cell_counts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id   TEXT NOT NULL,
            population  TEXT NOT NULL,
            count       INTEGER NOT NULL,
            FOREIGN KEY (sample_id)
                REFERENCES samples(sample_id),
            UNIQUE (sample_id, population)
        )
    """)

    # Indexes speed up common filters and joins
    cursor.execute("CREATE INDEX idx_cell_counts_sample     ON cell_counts(sample_id)")
    cursor.execute("CREATE INDEX idx_cell_counts_population ON cell_counts(population)")
    cursor.execute("CREATE INDEX idx_samples_subject        ON samples(subject_id)")
    conn.commit()


def load_csv(conn, csv_path):
    """Loads the cell-count.csv and insert its data into the database."""
    cursor = conn.cursor()

    with open(csv_path, "r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            # Stores blank values as NULL (SQL)
            response = row["response"].strip() or None

            # A subject can appears in multiple samples, so ignore duplicates
            cursor.execute("""
                INSERT OR IGNORE INTO subjects 
                    (subject_id, project, condition, age, sex, treatment, response)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                row["subject"],
                row["project"],
                row["condition"],
                int(row["age"]),
                row["sex"],
                row["treatment"],
                response,
            ))

            # Every row within the dataset represents a sample
            cursor.execute("""
                INSERT INTO samples (sample_id, subject_id, sample_type, time_from_treatment_start)
                VALUES (?, ?, ?, ?)
            """, (
                row["sample"],
                row["subject"],
                row["sample_type"],
                int(row["time_from_treatment_start"]),
            ))

            # Converting the five population columns into five database rows
            for population in POPULATIONS:
                cursor.execute("""
                    INSERT INTO cell_counts (
                        sample_id,
                        population,
                        count
                    )
                    VALUES (?, ?, ?)
                """, (
                    row["sample"],
                    population,
                    int(row[population]),
                ))
    conn.commit()


def main():
    # Deletes the old database so everything is updated
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)

    try:
        # Turning on foreign key check to make sure data is acccurate
        conn.execute("PRAGMA foreign_keys = ON")

        init_db(conn)
        load_csv(conn, CSV_PATH)
        # Making sure ALL the data is loaded correctly and is there
        subject_count = conn.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
        sample_count = conn.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
        cell_count_rows = conn.execute("SELECT COUNT(*) FROM cell_counts").fetchone()[0]
        print(f"Database created: {DB_PATH}")
        print(f"Subjects loaded: {subject_count:,}")
        print(f"Samples loaded: {sample_count:,}")
        print(f"Cell-count rows loaded: {cell_count_rows:,}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()