import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# ------------------ Streamlit Setup ------------------
st.set_page_config(page_title="Job Explorer", layout="wide")
st.title("💼 Real-Time Job Explorer")

# ------------------ Session State Init ------------------
if "job_data" not in st.session_state:
    st.session_state["job_data"] = None

# ------------------ User Input ------------------
st.markdown("## 🔍 Enter Search Criteria")
job_title = st.text_input("Job Title:", "")
location = st.text_input("Location:", "India")

st.markdown("### 🎯 Optional Filters")
skill = st.text_input("Required Skill (optional):", "")

# ------------------ API Key from Secrets ------------------
API_KEY = st.secrets["JSEARCH_API_KEY"]  # stored in .streamlit/secrets.toml
API_URL = "https://jsearch.p.rapidapi.com/search"

# ------------------ Job Fetch Function ------------------
def fetch_jobs(query, location):
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }
    params = {"query": f"{query} in {location}", "page": "1", "num_pages": "1"}
    try:
        response = requests.get(API_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for job in data.get("data", []):
            jobs.append({
                "Job Title": job.get("job_title", "N/A"),
                "Company": job.get("employer_name", "N/A"),
                "Location": job.get("job_city", "N/A"),
                "Posted": job.get("job_posted_at_datetime_utc", "N/A"),
                "Skills": skill if skill else "N/A",
                "Apply Link": job.get("job_apply_link", "N/A")
            })
        return jobs
    except Exception as e:
        st.error(f"⚠ Error fetching jobs: {e}")
        return None

# ------------------ Job Search ------------------
if st.button("🔍 Search Jobs"):
    with st.spinner("Fetching jobs..."):
        jobs = fetch_jobs(job_title, location)

        if jobs:  # ✅ If API works
            df = pd.DataFrame(jobs)
            df['Posted'] = pd.to_datetime(df['Posted'], errors='coerce').dt.date
            df['Apply Link'] = df['Apply Link'].apply(lambda x: f"[Apply Here]({x})" if x != "N/A" else "N/A")
            st.session_state["job_data"] = df.copy()

            # Save fallback
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            df.to_csv(fallback_path, index=False)
            st.success("✅ Job results updated and fallback saved.")
        else:
            # ------------------ Fallback Logic ------------------
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            if os.path.exists(fallback_path):
                fallback_df = pd.read_csv(fallback_path)

                # ✅ Apply filters: Job Title + Location
                filtered_fallback = fallback_df.copy()
                if job_title:
                    filtered_fallback = filtered_fallback[
                        filtered_fallback["Job Title"].str.contains(job_title, case=False, na=False)
                    ]
                if location:
                    filtered_fallback = filtered_fallback[
                        filtered_fallback["Location"].str.contains(location, case=False, na=False)
                    ]

                if not filtered_fallback.empty:
                    st.session_state["job_data"] = filtered_fallback
                    st.success("⚠ Loaded from fallback — results may be outdated.")
                else:
                    st.warning("😕 No matching jobs found in fallback.")
            else:
                st.warning("⚠ No fallback file found.")

# ------------------ Display and Insights ------------------
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

    # Apply Filters
    filtered_df = df.copy()
    if selected_city != "All":
        filtered_df = filtered_df[filtered_df["Location"] == selected_city]
    if selected_skill != "All":
        filtered_df = filtered_df[filtered_df["Skills"].str.contains(selected_skill)]

    st.success(f"Showing {len(filtered_df)} jobs after filtering.")
    st.markdown("### 📋 Job Listings")
    st.dataframe(filtered_df)

    # ------------------ Charts ------------------
    if not filtered_df.empty:
        st.markdown("## 📊 Job Market Insights")

        # Top Cities
        top_cities = filtered_df["Location"].value_counts().head(10)
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_cities.values, y=top_cities.index, ax=ax1, palette="coolwarm")
        ax1.set_title("Top Job Locations")
        st.pyplot(fig1)

        # Top Job Titles
        top_titles = filtered_df["Job Title"].value_counts().head(10)
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_titles.values, y=top_titles.index, ax=ax2, palette="Blues_d")
        ax2.set_title("Most Common Job Titles")
        st.pyplot(fig2)

        # Top Companies
        top_companies = filtered_df["Company"].value_counts().head(10)
        fig3, ax3 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_companies.values, y=top_companies.index, ax=ax3, palette="crest")
        ax3.set_title("Top Companies Hiring")
        st.pyplot(fig3)
    else:
        st.warning("No data available after filtering.")