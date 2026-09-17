"""
analysis.py

Parts 2, 3, and 4: Initial Analysis - Statistical Analysis - Data Subset Analysis

Run:
Python analysis.py

"""

import os
import sqlite3
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


#  ------------------------------------------------
#   PART 2 
#  ------------------------------------------------

DB_PATH = "immune_trial.db"
OUTPUT_DIR = "outputs"
SUMMARY_PATH = os.path.join(OUTPUT_DIR,"cell_frequencies.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_frequency_table(conn):
    """
    Part 2: Calculating every sample, total cell count and relative frequency percentage
    of each cell population.
    """

    query = """
        SELECT
            s.sample_id AS sample,
            sub.subject_id,
            sub.project,
            sub.condition,
            sub.treatment,
            sub.response,
            sub.sex,
            s.sample_type,
            s.time_from_treatment_start,
            cc.population,
            cc.count,
            SUM(cc.count) OVER (PARTITION BY s.sample_id) AS total_count
        FROM samples AS s
        JOIN subjects AS sub ON s.subject_id = sub.subject_id 
        JOIN cell_counts AS cc ON cc.sample_id = s.sample_id
        ORDER BY s.sample_id, cc.population
    """

    # Calculations for part 2
    df = pd.read_sql_query(query, conn)
    df["percentage"] = (df["count"] / df["total_count"] * 100).round(4)
    return df



# ------------------------------------------------
#   PART 3 
# ------------------------------------------------

def response_data(df):
    # Creating a filter
    df_response = df[
        (df["condition"] == "melanoma") &
        (df["treatment"] == "miraclib") &
        (df["sample_type"] == "PBMC") &
        (df["response"].isin(["yes", "no"]))].copy()
    return df_response


def response_boxplot(df_response):
    """Creating visualization (boxplots) to compare responders and non-responders."""

    populations = sorted(df_response["population"].unique())

    figure, axes = plt.subplots(1, len(populations), figsize=(16, 5), sharey=True,)

    for axis, population in zip(axes, populations):

        df_population = df_response[df_response["population"] == population]
        responders = df_population[df_population["response"] == "yes"]["percentage"]
        non_responders = df_population[df_population["response"] == "no"]["percentage"]
        axis.boxplot([responders, non_responders], tick_labels=["Yes", "No"],)
        axis.set_title(population.replace("_", " ").title())
        axis.set_xlabel("Response")

    axes[0].set_ylabel("Relative frequency (%)")
    figure.suptitle("Miraclib Responders vs. Non-Responders")
    figure.tight_layout()

    plot_path = os.path.join(OUTPUT_DIR, "response_boxplot.png",)

    figure.savefig(plot_path, dpi=300)
    plt.close(figure)
    print(f"\nBoxplot saved to: {plot_path}")


def stat_tests(df_response):
    """ Comparing responders with non-responders using Mann-Whitney U test for each cell population."""
    results = []
    populations = sorted(
        df_response["population"].unique())

    for population in populations:
        df_population = df_response[df_response["population"] == population]
        responders = df_population[df_population["response"] == "yes"]["percentage"]
        non_responders = df_population[df_population["response"] == "no"]["percentage"]
        test_statistic, p_value = stats.mannwhitneyu(responders, non_responders, alternative="two-sided",)

        # Correct for testing five populations
        adjusted_p_value = min(p_value * len(populations), 1.0,)

        results.append(
            {"population": population, "responder_median": round(responders.median(), 4,),
             "non_responder_median": round(non_responders.median(), 4,),
             "test_statistic": round(test_statistic, 4,),
             "p_value": round(p_value, 6,),
             "adjusted_p_value": round(adjusted_p_value, 6,),
             "significant": ("Yes" if adjusted_p_value < 0.05 else "No"),
             })

    results_df = pd.DataFrame(results)
    stat_path = os.path.join(OUTPUT_DIR, "response_statistics.csv",)
    results_df.to_csv(stat_path, index=False,)

    print("\nPart 3 statistical results:")
    print(results_df.to_string(index=False))
    print(f"\nFile has been saved to: {stat_path}")

    return results_df



# ------------------------------------------------
# PART 4
# ------------------------------------------------

def part4_subset_analysis(conn):
    """
    Finding the baseline melanoma PBMC samples treated through miraclib
    then calculating count by project, response, and sex.
    """
    # filtering the baseline samples for the required treatment.
    query = """
        SELECT
            s.sample_id AS sample,
            sub.subject_id,
            sub.project,
            sub.response,
            sub.sex,
            sub.condition,
            sub.treatment,
            s.sample_type,
            s.time_from_treatment_start
        FROM samples AS s
        JOIN subjects AS sub
            ON s.subject_id = sub.subject_id
        WHERE sub.condition = 'melanoma'
          AND sub.treatment = 'miraclib'
          AND s.sample_type = 'PBMC'
          AND s.time_from_treatment_start = 0
        ORDER BY sub.project, sub.subject_id
    """

    df_baseline = pd.read_sql_query(query, conn)
    average_b_cell_query = """
        SELECT
            ROUND(AVG(cc.count), 2) AS average_b_cells
        FROM samples AS s
        JOIN subjects AS sub
            ON s.subject_id = sub.subject_id
        JOIN cell_counts AS cc
            ON cc.sample_id = s.sample_id
        WHERE sub.condition = 'melanoma'
          AND sub.sex = 'M'
          AND sub.response = 'yes'
          AND s.time_from_treatment_start = 0
          AND cc.population = 'b_cell'
    """

    average_b_cells = pd.read_sql_query(average_b_cell_query, conn,)["average_b_cells"].iloc[0]
    

    # Number of samples from each project
    project_counts = (df_baseline.groupby("project")["sample"].nunique().reset_index(name="sample_count"))

    # Number of subjects who responded with yes or no
    response_counts = (df_baseline.groupby("response")["subject_id"].nunique().reset_index(name="subject_count"))

    # Number of male and female subjects
    sex_counts = (df_baseline.groupby("sex")["subject_id"].nunique().reset_index(name="subject_count"))

    baseline_path = os.path.join(OUTPUT_DIR, "baseline_samples.csv",)
    project_path = os.path.join(OUTPUT_DIR, "samples_by_project.csv",)
    response_path = os.path.join(OUTPUT_DIR, "subjects_by_response.csv",)
    sex_path = os.path.join(OUTPUT_DIR, "subjects_by_sex.csv",)

    df_baseline.to_csv(baseline_path, index=False,)
    project_counts.to_csv(project_path, index=False,)
    response_counts.to_csv(response_path, index=False,)
    sex_counts.to_csv(sex_path, index=False,)

    print("\nPart 4 baseline samples:")
    print(df_baseline.head(10))

    print("\nNumber of samples from each project:")
    print(project_counts.to_string(index=False))

    print("\nNumber of subjects by response:")
    print(response_counts.to_string(index=False))

    print("\nNumber of subjects by sex:")
    print(sex_counts.to_string(index=False))

    print("\nPart 4 results have been saved in the outputs directory.")

    print(
        "\n The average B-cell count for male melanoma "f"responders at time 0: {average_b_cells:.2f}")    
    return (df_baseline, project_counts, response_counts, sex_counts, average_b_cells)


# ------------------------------------------------
# The Analysis
# ------------------------------------------------


def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = get_frequency_table(conn)

        # Selects the five columns required for Part 2
        df_summary = df[["sample", "total_count", "population", "count","percentage",]]
        df_summary.to_csv(SUMMARY_PATH, index=False)

        # Displays the top 10 rows only
        print("Part 2 summary table:")
        print(df_summary.head(10))
        print("\nThe summary table has been saved into the outputs directory as cell_frequencies.csv.")

        df_response = response_data(df)
        response_boxplot(df_response)
        stat_tests(df_response)
        part4_subset_analysis(conn)

    finally:
        conn.close()

if __name__ == "__main__":
    main()