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
API_KEY = st.secrets["JSEARCH_API_KEY"]
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
                "Job Title": job.get("job_title", "Not Specified"),
                "Company": job.get("employer_name", "Not Specified"),
                "Location": job.get("job_city", "Not Specified"),
                "Posted": job.get("job_posted_at_datetime_utc", "Not Specified"),
                "Job Type": job.get("job_employment_type", "Not Specified"),
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

            # Data Cleaning
            df = df.drop_duplicates()
            for col in ["Job Title", "Company", "Location", "Job Type"]:
                df[col] = df[col].fillna("Not Specified").astype(str).str.strip().str.title()
            df["Posted"] = pd.to_datetime(df["Posted"], errors="coerce")

            st.session_state["job_data"] = df.copy()

            # Save fallback
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            df.to_csv(fallback_path, index=False)
            st.success("✅ Job results saved.")

        else:
            # Fallback
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            if os.path.exists(fallback_path):
                fallback_df = pd.read_csv(fallback_path)
                for col in ["Job Title", "Company", "Location", "Job Type"]:
                    fallback_df[col] = fallback_df[col].fillna("Not Specified").astype(str).str.strip().str.title()

                fallback_df = fallback_df.drop_duplicates(subset=["Job Title", "Company", "Location", "Posted"])

                filtered_fallback = fallback_df.copy()
                if job_title:
                    filtered_fallback = filtered_fallback[
                        filtered_fallback["Job Title"].str.contains(job_title, case=False, na=False)
                    ]
                if location:
                    filtered_fallback = filtered_fallback[
                        filtered_fallback["Location"].str.contains(location, case=False, na=False)
                    ]
                if job_type_filter != "All":
                    filtered_fallback = filtered_fallback[
                        filtered_fallback["Job Type"].str.contains(job_type_filter, case=False, na=False)
                    ]

                if not filtered_fallback.empty:
                    st.session_state["job_data"] = filtered_fallback
                    st.success("⚠️ Loaded from fallback — results may be outdated.")
                else:
                    st.warning("😕 No matching jobs found in fallback.")
            else:
                st.warning("⚠️ No fallback file found.")

# ------------------ Display and EDA ------------------
if st.session_state["job_data"] is not None:
    df = st.session_state["job_data"]
    st.success(f"Showing {len(df)} jobs.")
    st.markdown("### 📋 Job Listings")
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    if not df.empty:
        st.markdown("## 📊 Exploratory Data Analysis & Job Market Trends")

        # Remove 'Not Specified' for plotting
        df_plot = df.copy()
        df_plot = df_plot[df_plot["Location"] != "Not Specified"]
        df_plot = df_plot[df_plot["Company"] != "Not Specified"]
        df_plot = df_plot[df_plot["Job Type"] != "Not Specified"]

        # ------------------ 1. Daily Trend ------------------
        st.markdown("### 📈 Job Posting Trend Over Time")
        df_plot["Posted"] = pd.to_datetime(df_plot["Posted"], errors="coerce")
        trend_df = df_plot.dropna(subset=["Posted"]).copy()
        trend_df["Posted_Date"] = trend_df["Posted"].dt.date
        daily_trend = trend_df.groupby("Posted_Date").size().sort_index()
        st.line_chart(daily_trend)

        # ------------------ 2. Top Locations ------------------
        st.markdown("### 🏙 Top Hiring Locations")
        top_locations = df_plot["Location"].value_counts().head(5)
        fig, ax = plt.subplots(figsize=(8,5))
        sns.barplot(y=top_locations.index, x=top_locations.values, ax=ax, palette="coolwarm")
        ax.set_xlabel("Number of Jobs")
        ax.set_ylabel("City")
        ax.set_title("Top 5 Job Locations")
        st.pyplot(fig)

        # ------------------ 3. Top Companies ------------------
        st.markdown("### 🏢 Top Companies Hiring")
        top_companies = df_plot["Company"].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(8,5))
        sns.barplot(y=top_companies.index, x=top_companies.values, ax=ax, palette="crest")
        ax.set_xlabel("Number of Jobs")
        ax.set_ylabel("Company")
        ax.set_title("Top 10 Companies Hiring")
        st.pyplot(fig)

        # ------------------ 4. Job Type Distribution ------------------
        st.markdown("### 💼 Job Type Distribution")
        job_type_counts = df_plot["Job Type"].value_counts()
        fig, ax = plt.subplots(figsize=(6,5))
        job_type_counts.plot.pie(autopct="%1.1f%%", startangle=90, ax=ax)
        ax.set_ylabel("")
        ax.set_title("Job Type Distribution")
        st.pyplot(fig)

        # ------------------ 5. Weekly Trend ------------------
        st.markdown("### 📅 Weekly Job Posting Trend")
        trend_df["Year_Week"] = trend_df["Posted"].dt.strftime("%Y-%U")
        weekly_trend = trend_df.groupby("Year_Week").size().sort_index()
        weekly_trend.index = pd.to_datetime([f"{d}-1" for d in weekly_trend.index], format="%Y-%U-%w")
        weekly_trend = weekly_trend.asfreq('W-MON', fill_value=0)
        st.line_chart(weekly_trend)

        # ------------------ 6. Monthly Trend ------------------
        st.markdown("### 📅 Monthly Job Posting Trend")
        trend_df["Year_Month"] = trend_df["Posted"].dt.to_period("M")
        monthly_trend = trend_df.groupby("Year_Month").size().sort_index()
        monthly_trend.index = monthly_trend.index.to_timestamp()
        monthly_trend = monthly_trend.asfreq('MS', fill_value=0)
        st.line_chart(monthly_trend)