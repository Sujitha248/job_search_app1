import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from prophet import Prophet
import os

# Streamlit Setup
st.set_page_config(page_title="India Job Skill Finder", layout="wide")
st.title("💼 Real-Time Job Search with Skills & Trends (WorkIndia + Jobicy)")

# Session State Init
if "job_data" not in st.session_state:
    st.session_state["job_data"] = None

# User Input
st.markdown("## 🔍 Enter Search Criteria")
job_title = st.text_input("Job Title:", "Software Engineer")
location = st.text_input("Location:", "India")
skill = st.text_input("Required Skill (optional):", "")

# Scraper Function
def fetch_jobs(job_title):
    job_results = []

    # Jobicy API
    try:
        jobicy_url = f"https://jobicy.com/api/v2/remote-jobs?search={job_title}"
        response = requests.get(jobicy_url)
        data = response.json()
        for job in data.get("jobs", []):
            job_results.append({
                "Job Title": job.get("title", "N/A"),
                "Company": job.get("company", "N/A"),
                "Location": job.get("location", "Remote"),
                "Experience": "N/A",
                "Salary": job.get("salary", "N/A"),
                "Posted": job.get("posted", datetime.today().strftime("%Y-%m-%d")),
                "Skills": skill if skill else "N/A",
                "Apply Link": job.get("url", "N/A")
            })
    except Exception as e:
        st.warning(f"Jobicy scraping failed: {e}")

    # WorkIndia Scraping
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        html = requests.get("https://www.workindia.in/jobs/", headers=headers).text
        df = pd.read_html(html)[0]
        for _, row in df.iterrows():
            job_results.append({
                "Job Title": row.get("Job Title", "N/A"),
                "Company": row.get("Company Name", "N/A"),
                "Location": row.get("Location", "India"),
                "Experience": "N/A",
                "Salary": row.get("Salary", "N/A"),
                "Posted": datetime.today().strftime("%Y-%m-%d"),
                "Skills": skill if skill else "N/A",
                "Apply Link": "https://www.workindia.in/jobs/"
            })
    except Exception as e:
        st.warning(f"WorkIndia scraping failed: {e}")

    return job_results

# Job Search
if st.button("🔍 Search Jobs"):
    with st.spinner("Fetching jobs..."):
        jobs = fetch_jobs(job_title)
        if jobs:
            df = pd.DataFrame(jobs)
            df["Posted"] = pd.to_datetime(df["Posted"], errors="coerce").dt.date
            df["Apply Link"] = df["Apply Link"].apply(lambda x: f"[Apply]({x})")
            st.session_state["job_data"] = df.copy()
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            df.to_csv(fallback_path, index=False)
            st.success("✅ Job results updated and fallback saved.")
        else:
            st.warning("😕 No jobs found.")

# Filter & Display
if st.session_state["job_data"] is not None:
    df = st.session_state["job_data"]

    st.markdown("## 🎛 Filter Results")
    cities = sorted(df["Location"].dropna().unique())
    selected_city = st.selectbox("📍 Filter by City:", ["All"] + cities)

    skills_list = sorted(set(
        sk.strip() for s in df["Skills"] if s != "N/A"
        for sk in s.split(",")
    ))
    selected_skill = st.selectbox("🛠 Filter by Skill:", ["All"] + skills_list)

    filtered_df = df.copy()
    if selected_city != "All":
        filtered_df = filtered_df[filtered_df["Location"] == selected_city]
    if selected_skill != "All":
        filtered_df = filtered_df[filtered_df["Skills"].str.contains(selected_skill)]

    st.success(f"Showing {len(filtered_df)} jobs after filtering.")
    st.markdown("### 📋 Filtered Job Listings")
    st.write(filtered_df.to_markdown(index=False), unsafe_allow_html=True)

    if not filtered_df.empty:
        st.markdown("## 📊 Job Market Insights")

        top_cities = filtered_df["Location"].value_counts().head(10)
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_cities.values, y=top_cities.index, ax=ax1, palette="coolwarm")
        ax1.set_title("Top Job Locations")
        st.pyplot(fig1)

        top_titles = filtered_df["Job Title"].value_counts().head(10)
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_titles.values, y=top_titles.index, ax=ax2, palette="Blues_d")
        ax2.set_title("Most Common Job Titles")
        st.pyplot(fig2)

        top_companies = filtered_df["Company"].value_counts().head(10)
        fig3, ax3 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_companies.values, y=top_companies.index, ax=ax3, palette="crest")
        ax3.set_title("Top Companies Hiring")
        st.pyplot(fig3)

        trend_df = filtered_df.groupby("Posted").size().reset_index(name="Job Count")
        fig4, ax4 = plt.subplots(figsize=(8, 5))
        sns.lineplot(data=trend_df, x="Posted", y="Job Count", marker="o", ax=ax4)
        ax4.set_title("Job Posting Trend Over Time")
        st.pyplot(fig4)

        st.markdown("## 🔮 Forecast (Next 7 Days)")
        prophet_df = trend_df.rename(columns={"Posted": "ds", "Job Count": "y"})
        model = Prophet()
        model.fit(prophet_df)
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)
        fig5 = model.plot(forecast)
        st.pyplot(fig5)
    else:
        st.warning("No data available after filtering.")