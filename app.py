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

st.markdown("### 🎯 Optional Filters")
industry = st.text_input("Industry (optional):", "")
company = st.text_input("Company (optional):", "")

# ------------------ API Key from Secrets ------------------
API_KEY = st.secrets["JSEARCH_API_KEY"]  # store your key in .streamlit/secrets.toml
API_URL = "https://jsearch.p.rapidapi.com/search"

# ------------------ Job Fetch Function ------------------
def fetch_jobs(query, location):
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }
    params = {"query": f"{query} in {location}", "page": "1", "num_pages": "3"}  # more pages = more jobs
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
                "Industry": job.get("job_industry", "Not specified"),
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
            st.session_state["job_data"] = df.copy()

            # Save fallback
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            df.to_csv(fallback_path, index=False)
            st.success("✅ Job results updated and fallback saved.")
        else:
            # ------------------ Fallback Logic with Filtering ------------------
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            if os.path.exists(fallback_path):
                fallback_df = pd.read_csv(fallback_path)

                # Apply filters
                filtered_fallback = fallback_df.copy()
                if job_title:
                    filtered_fallback = filtered_fallback[
                        filtered_fallback["Job Title"].str.contains(job_title, case=False, na=False)
                    ]
                if location:
                    filtered_fallback = filtered_fallback[
                        filtered_fallback["Location"].str.contains(location, case=False, na=False)
                    ]
                if company:
                    filtered_fallback = filtered_fallback[
                        filtered_fallback["Company"].str.contains(company, case=False, na=False)
                    ]
                if industry:
                    filtered_fallback = filtered_fallback[
                        filtered_fallback["Industry"].str.contains(industry, case=False, na=False)
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

    st.success(f"Showing {len(df)} jobs.")
    st.markdown("### 📋 Job Listings (click links to apply)")
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # ------------------ Charts ------------------
    if not df.empty:
        st.markdown("## 📊 Job Market Insights")

        # Top Cities
        top_cities = df["Location"].value_counts().head(10)
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_cities.values, y=top_cities.index, ax=ax1, palette="coolwarm")
        ax1.set_title("Top Job Locations")
        st.pyplot(fig1)

        # Top Titles
        top_titles = df["Job Title"].value_counts().head(10)
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_titles.values, y=top_titles.index, ax=ax2, palette="Blues_d")
        ax2.set_title("Most Common Job Titles")
        st.pyplot(fig2)

        # Top Companies
        top_companies = df["Company"].value_counts().head(10)
        fig3, ax3 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_companies.values, y=top_companies.index, ax=ax3, palette="crest")
        ax3.set_title("Top Companies Hiring")
        st.pyplot(fig3)
    else:
        st.warning("No data available after filtering.")