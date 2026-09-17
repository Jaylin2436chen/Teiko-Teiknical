# Immune Cell Trial Analysis

For this project, I created a Python program that analyzes immune-cell population data clinical trial for Bob Loblaw. I used SQLite to store the data, pandas and SciPy to analyze it, Matplotlib to create the the visualizations (boxplots), and Streamlit to create an interactive dashboard/page.

## Dashboard

My interactive dashboard can be viewed here:

[Open the Immune Cell Analysis Dashboard](https://teiko-teiknical-hh4wh4vonxjpcwnxbcctqk.streamlit.app)

My dashboard displays the results from Parts 2, 3, and 4 of the analysis.

## Project Files List

```text
Teiko-Teiknical/
├── data/
│   └── cell-count.csv
├── outputs/
│   ├── baseline_samples.csv
│   ├── cell_frequencies.csv
│   ├── response_boxplot.png
│   ├── response_statistics.csv
│   ├── samples_by_project.csv
│   ├── subjects_by_response.csv
│   └── subjects_by_sex.csv
├── analysis.py
├── dashboard.py
├── load_data.py
├── Makefile
├── README.md
└── requirements.txt
```

The `immune_trial.db` database is created automatically when the pipeline is run.

## How to Run the Project

The project can be ran through GitHub Codespaces.


### 1. Install the requirements

Run:

```bash
make setup
```

This installs the Python packages from `requirements.txt`.

### 2. Run the data pipeline

Run:

```bash
make pipeline
```

This runs:

```bash
python load_data.py
python analysis.py
```

The first script creates and loads the SQLite database. The second script will complete the analysis and saves the results into the `outputs` directory.

### 3. Start the dashboard

Run:

```bash
make dashboard
```

After the dashboard starts, open the forwarded Streamlit link provided by GitHub Codespaces.

Or open it through the link downbelow.
(https://teiko-teiknical-hh4wh4vonxjpcwnxbcctqk.streamlit.app/)

To stop the dashboard, you can press `Control + C` in the terminal.

## Part 1: Data Management

For Part 1, I created `load_data.py`. This script reads `data/cell-count.csv` then creates the database tables, and loads the data into a SQLite database named `immune_trial.db`.

The loader can also be run separately using the command downbelow:

```bash
python load_data.py
```

## Database Schema

I separated the data into three different tables:

```text
subjects
    subject_id     TEXT      PRIMARY KEY
    project        TEXT
    condition      TEXT
    age            INTEGER
    sex            TEXT
    treatment      TEXT
    response       TEXT

samples
    sample_id                  TEXT      PRIMARY KEY
    subject_id                 TEXT      FOREIGN KEY
    sample_type                TEXT
    time_from_treatment_start  INTEGER

cell_counts
    id            INTEGER   PRIMARY KEY AUTOINCREMENT
    sample_id     TEXT      FOREIGN KEY
    population    TEXT
    count         INTEGER
```

The relationships between the tables are:

```text
subjects  1 ─── many  samples
samples   1 ─── many  cell_counts
```

This means that one subject can be linked to multiple samples, and one sample can also be linked to multiple cell-count records.

### Why I Used This Design

The original CSV repeats information about each subject, such as sex, age, treatment, and response. So I decided to normalized the original CSV data into three related SQLite tables: subjects, samples, and cell_counts.

I placed sample information in the `samples` table and 'joined' each sample to its subject using `subject_id`.

I used a long format as well for `cell_counts`, so that all population is stored as a separate row. For example:

This allows for easier grouping, filtering, and allows you to compare the different cell populations.

The primary and foreign keys connect the three tables together. I also created indexes for columns that are used when joining or filtering the tables.

## Part 2: Cell-Population Frequencies

For Part 2, I calculated the relative frequency of each cell population in every sample.

First, I decided to add the counts of the five populations to find the total cell count for each sample. Then I calculated each percentage using this formula:

```text
percentage = cell population count / total cell count × 100
```

The completed summary table is saved as:

```text
outputs/cell_frequencies.csv
```

In the dashboard you can select a sample and view its total count, population table, and relative frequency chart.

## Part 3: Statistical Analysis

For Part 3, I compared responders to non-responders using only records that met these requirements:

- The condition was melanoma
- The treatment was miraclib
- The response was either a `yes` or `no`
- The sample type was PBMC

Additionally, I created boxplots to compare the relative frequencies of all the five cell populations between responders and non responders.

The boxplot is saved in:

```text
outputs/response_boxplot.png
```

### Statistical Test

I used a two-sided Mann–Whitney U test for each population. I used this test because it allows me to compare the responder and non responder groups without assuming that the data is following a normal distribution.

Since I also tested five different populations, I applied a Bonferroni correction to the p-values. A result is significant when the p-value was less than `0.05`.

The statistical results are saved in:

```text
outputs/response_statistics.csv
```

After changing the p-values, none of the five populations had a significant difference between responders and non responders.

## Part 4: Baseline Sample Analysis

For Part 4, I filtered the database for samples that met the following conditions:

- The condition was melanoma
- The treatment was miraclib
- The sample type was PBMC
- The time from treatment start was `0`

I then calculated for the number of samples from each project, then number of unique responders and non responders, and lastly the number of unique male and female subjects.

The files for Part 4 are saved in:

```text
outputs/baseline_samples.csv
outputs/samples_by_project.csv
outputs/subjects_by_response.csv
outputs/subjects_by_sex.csv
```

## Average B-Cell Count

After calculating the average number of B cells for male melanoma responders when time is 0, the final result was 10206.15. This calculation includes all sample types and treatment types.

The average B-cell count was:
```text
10206.15
```
I also put a display of the result in the Part 4 dashboard tab.

### Part 2: Frequencies

This tab allows the you to select a sample and views:

- Its total cell count
- Its population counts
- Its relative frequencies
- A bar chart of the percentages

### Part 3: Treatment Response

This tab displays:

- The number of responder and non-responder samples
- The Miraclib Responders vs. Non-Responders boxplots
- The statistical results
- The final significance conclusion

### Part 4: Baseline Samples

This tab displays data such as:

- The number of baseline samples
- The number of unique subjects
- The average B-cell count
- Samples from each project
- Subjects by response
- Subjects by sex
- The filtered baseline records

## Output Files

| Output | Description |
|---|---|
| `cell_frequencies.csv` | Frequencies for every sample and population |
| `response_boxplot.png` | Boxplots comparing responses |
| `response_statistics.csv` | Statistical test results |
| `baseline_samples.csv` | Filtered baseline samples |
| `samples_by_project.csv` | Sample counts for each project |
| `subjects_by_response.csv` | Subject counts for each response |
| `subjects_by_sex.csv` | Subject counts for each sex |

## You can use these functions down below to run the Files Separately!

Create the database:

```bash
python load_data.py
```

Run the analysis:

```bash
python analysis.py
```

Start the dashboard:

```bash
python -m streamlit run dashboard.py
```

## Repository Link

[View my GitHub repository](https://github.com/Jaylin2436chen/Teiko-Teiknical)