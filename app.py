import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ------------------ Streamlit Setup ------------------
st.set_page_config(page_title="Real-Time Job Explorer", layout="wide")
st.title("💼 Real-Time Job Explorer")

# ------------------ Session State Init ------------------
if "job_data" not in st.session_state:
    st.session_state["job_data"] = None

# ------------------ User Input ------------------
st.markdown("## 🔍 Enter Search Criteria")
job_title = st.text_input("Job Title:", "")
location = st.text_input("Location:", "India")

st.markdown("### 🎯 Filters")
job_type_filter = st.selectbox(
    "Job Type (optional):",
    ["All", "Full-time", "Part-time", "Contract", "Internship", "Temporary"]
)

# ------------------ API Key ------------------
API_KEY = st.secrets["JSEARCH_API_KEY"]  # store in .streamlit/secrets.toml
API_URL = "https://jsearch.p.rapidapi.com/search"

# ------------------ Job Fetch Function ------------------
def fetch_jobs(query, location):
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }
    params = {"query": f"{query} in {location}", "page": "1", "num_pages": "3"}
    try:
        response = requests.get(API_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for job in data.get("data", []):
            jobs.append({
                "Job Title": job.get("job_title", "Not specified"),
                "Company": job.get("employer_name", "Not specified"),
                "Location": job.get("job_city", "Not specified"),
                "Posted": job.get("job_posted_at_datetime_utc", "Not specified"),
                "Job Type": job.get("job_employment_type", "Not specified"),
                "Apply Link": f"<a href='{job.get('job_apply_link', '#')}' target='_blank'>Apply Here</a>"
            })
        return jobs
    except Exception as e:
        st.error(f"Error fetching jobs: {e}")
        return None

# ------------------ Job Search ------------------
if st.button("🔍 Search Jobs"):
    with st.spinner("Fetching jobs..."):
        jobs = fetch_jobs(job_title, location)

        if jobs:
            df = pd.DataFrame(jobs)

            # ------------------ Data Cleaning ------------------
            df = df.drop_duplicates()
            for col in ["Job Title", "Company", "Location", "Job Type"]:
                df[col] = df[col].fillna("Not specified").astype(str).str.strip().str.title()
            df["Posted"] = pd.to_datetime(df["Posted"], errors="coerce")

            # Apply Job Type filter
            if job_type_filter != "All":
                df = df[df["Job Type"].str.contains(job_type_filter, case=False, na=False)]

            st.session_state["job_data"] = df.copy()

            # Save fallback
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            df.to_csv(fallback_path, index=False)
            st.success("✅ Job results saved.")

        else:
            # ------------------ Fallback Logic ------------------
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            if os.path.exists(fallback_path):
                fallback_df = pd.read_csv(fallback_path)
                for col in ["Job Title", "Company", "Location", "Job Type"]:
                    fallback_df[col] = fallback_df[col].fillna("Not specified").astype(str).str.strip().str.title()
                fallback_df = fallback_df.drop_duplicates(subset=["Job Title", "Company", "Location", "Posted"])

                filtered_fallback = fallback_df.copy()
                if job_title:
                    filtered_fallback = filtered_fallback[filtered_fallback["Job Title"].str.contains(job_title, case=False, na=False)]
                if location:
                    filtered_fallback = filtered_fallback[filtered_fallback["Location"].str.contains(location, case=False, na=False)]
                if job_type_filter != "All":
                    filtered_fallback = filtered_fallback[filtered_fallback["Job Type"].str.contains(job_type_filter, case=False, na=False)]

                if not filtered_fallback.empty:
                    st.session_state["job_data"] = filtered_fallback
                    st.success("⚠️ Loaded from fallback — results may be outdated.")
                else:
                    st.warning("😕 No matching jobs found in fallback.")
            else:
                st.warning("⚠️ No fallback file found.")

# ------------------ Display Job Listings ------------------
if st.session_state["job_data"] is not None:
    df = st.session_state["job_data"]

    st.success(f"Showing {len(df)} jobs.")
    st.markdown("### 📋 Job Listings")
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

# ------------------ Trend Analysis ------------------
if st.session_state["job_data"] is not None:
    job_data = st.session_state["job_data"].copy()
    st.markdown("## 📈 Trend Analysis")

    job_data["Posted"] = pd.to_datetime(job_data["Posted"], errors="coerce")
    trend_df = job_data.dropna(subset=["Posted"]).copy()

    # ------------------ 1. Job Posting Trend Over Time ------------------
    trend_df["Posted_Date"] = trend_df["Posted"].dt.date
    daily_trend = trend_df.groupby("Posted_Date").size()
    st.markdown("### 🕓 Job Posting Trend Over Time")
    st.line_chart(daily_trend)

    # ------------------ 2. Location-Based Hiring Trend ------------------
    st.markdown("### 🧭 Location-Based Hiring Trend")
    if "Location" in job_data.columns and not job_data["Location"].isna().all():
        top_locations = job_data["Location"].value_counts().head(5)
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_locations.index, y=top_locations.values, ax=ax, palette="coolwarm")
        ax.set_title("Top Hiring Locations")
        st.pyplot(fig)

    # ------------------ 3. Company-Wise Hiring Trend ------------------
    st.markdown("### 🏢 Company-Wise Hiring Trend")
    if "Company" in job_data.columns and not job_data["Company"].isna().all():
        company_trend = job_data.groupby(["Company", job_data["Posted"].dt.date]).size().unstack(fill_value=0)
        top_companies = company_trend.sum().sort_values(ascending=False).head(10).index
        st.line_chart(company_trend[top_companies])

    # ------------------ 4. Job Type Trend Over Time ------------------
    st.markdown("### 🧑‍💻 Job Type Trend Over Time")
    if "Job Type" in job_data.columns and not job_data["Job Type"].isna().all():
        job_type_trend = job_data.groupby(["Job Type", job_data["Posted"].dt.date]).size().unstack(fill_value=0)
        st.line_chart(job_type_trend.T)

    # ------------------ 5. Weekly & Monthly Trends ------------------
    st.markdown("### 📅 Weekly & Monthly Job Posting Trends")
    trend_df["Week"] = trend_df["Posted"].dt.isocalendar().week
    trend_df["Month"] = trend_df["Posted"].dt.month
    weekly_trend = trend_df.groupby("Week").size()
    monthly_trend = trend_df.groupby("Month").size()
    st.line_chart(weekly_trend)
    st.line_chart(monthly_trend)