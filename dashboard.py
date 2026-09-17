"""
dashboard.py

Interactive dashboard displaying the results from my parts 2, 3, and 4.

Run:
streamlit run dashboard.py
"""
import subprocess
import sys
import os
import sqlite3
import pandas as pd
import streamlit as st
from analysis import get_frequency_table, response_data


DB_PATH = "immune_trial.db"
OUTPUT_DIR = "outputs"


def database_ready():
    """Making sure that the database exists first and contains data"""

    if not os.path.exists(DB_PATH):
        return False

    try:
        conn = sqlite3.connect(DB_PATH)

        sample_count = conn.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
        conn.close()

        return sample_count > 0

    except sqlite3.Error:
        return False


st.set_page_config(page_title = "Immune Cell Analysis", layout = "wide",)


@st.cache_data
def load_dashboard_data():
    """Load the analysis data from the SQLite database."""

    conn = sqlite3.connect(DB_PATH)

    frequency_df = get_frequency_table(conn)

    baseline_query = """
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

    df_baseline = pd.read_sql_query(baseline_query, conn,)
    conn.close()

    return frequency_df, df_baseline


st.title("Immune Cell Analysis")
st.write("This dashboard shows cell population frequencies, miraclib response comparisons, and baseline sample summaries.")

if not database_ready():
    st.info("Preparing the database and analysis results.")
    subprocess.run([sys.executable, "load_data.py"], check=True,)
    subprocess.run([sys.executable, "analysis.py"], check=True,)

    st.cache_data.clear()


frequency_df, df_baseline = load_dashboard_data()

if frequency_df.empty:
    st.error("The database did not return any sample data.")
    st.stop()

part2_tab, part3_tab, part4_tab = st.tabs(["Part 2: Frequencies", "Part 3: Treatment Response", "Part 4: Baseline Samples",])


# ------------------------------------------------
#  PART 2
# ------------------------------------------------

with part2_tab:
    st.header("Cell-Population Frequencies")
    st.write("Select a sample to view its total cell count and the relative frequency of each cell population.")

    sample_options = sorted(frequency_df["sample"].unique())
    selected_sample = st.selectbox("Select a sample", sample_options,)
    selected_df = frequency_df[frequency_df["sample"] == selected_sample][
        ["sample", "total_count", "population", "count", "percentage",]]

    total_count = int(selected_df["total_count"].iloc[0])

    st.metric("Total cell count", f"{total_count:,}",)
    st.dataframe(selected_df, use_container_width=True, hide_index=True,)

    chart_df = selected_df.set_index("population")[["percentage"]]
    st.bar_chart(chart_df)


# ------------------------------------------------
#  PART 3
# ------------------------------------------------

with part3_tab:
    st.header("Miraclib Responders vs. Non-Responders")

    df_response = response_data(frequency_df)
    selected_population = st.selectbox("Select a cell population",sorted(df_response["population"].unique()),)
    df_selected_response = df_response[df_response["population"] == selected_population]
    responder_count = df_selected_response[df_selected_response["response"] == "yes"]["sample"].nunique()
    non_responder_count = df_selected_response[df_selected_response["response"] == "no"]["sample"].nunique()

    first_column, second_column = st.columns(2)

    first_column.metric("Responder samples",responder_count,)
    second_column.metric("Non-responder samples", non_responder_count,)
    boxplot_path = os.path.join(OUTPUT_DIR, "response_boxplot.png",)

    if os.path.exists(boxplot_path):
        st.image(boxplot_path, caption=("Relative frequencies for responders and non-responders"), 
                 use_container_width=True,)

    statistics_path = os.path.join(OUTPUT_DIR,"response_statistics.csv",)

    if os.path.exists(statistics_path):
        statistics_df = pd.read_csv(statistics_path)
        st.subheader("Statistical results")
        st.dataframe(statistics_df, use_container_width=True, hide_index=True,)
        df_significant = statistics_df[statistics_df["significant"] == "Yes"]

        if df_significant.empty:
            st.info("No cell populations had a statistically significant difference after adjustment.")
        else:
            st.success("Significant populations: "
                + ", ".join(df_significant["population"]))


# ------------------------------------------------
# PART 4
# ------------------------------------------------

with part4_tab:
    st.header("Baseline Sample Analysis")
    st.write("Melanoma PBMC samples collected at treatment time 0 from subjects treated with miraclib.")

    sample_total = df_baseline["sample"].nunique()
    subject_total = df_baseline["subject_id"].nunique()

    first_column, second_column = st.columns(2)
    first_column.metric("Baseline samples", sample_total,)
    second_column.metric("Unique subjects", subject_total,)

    project_counts = (df_baseline.groupby("project")["sample"].nunique().reset_index(name="sample_count"))
    response_counts = (df_baseline.groupby("response")["subject_id"].nunique().reset_index(name="subject_count"))
    sex_counts = (df_baseline.groupby("sex")["subject_id"].nunique().reset_index(name="subject_count"))

    st.subheader("Samples by project")

    st.dataframe(project_counts, use_container_width=True, hide_index=True,)
    st.bar_chart(project_counts.set_index("project"))

    first_column, second_column = st.columns(2)

    with first_column:
        st.subheader("Subjects by response")
        st.dataframe(response_counts, use_container_width=True, hide_index=True,)
        st.bar_chart(response_counts.set_index("response"))

    with second_column:
        st.subheader("Subjects by sex")
        st.dataframe(sex_counts, use_container_width=True, hide_index=True,)
        st.bar_chart(sex_counts.set_index("sex"))

    st.subheader("Baseline sample records")
    st.dataframe(df_baseline, use_container_width=True, hide_index=True,)