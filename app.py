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
industry = st.text_input("Industry (optional):", "")

experience_filter = st.selectbox(
    "Experience Level (optional):",
    ["All", "Internship", "Entry level", "Mid level", "Senior level", "Executive"]
)
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
            exp_info = job.get("job_required_experience", {})
            jobs.append({
                "Job Title": job.get("job_title", "Not specified"),
                "Company": job.get("employer_name", "Not specified"),
                "Location": job.get("job_city", "Not specified"),
                "Posted": job.get("job_posted_at_datetime_utc", "Not specified"),
                "Industry": job.get("job_industry", "Not specified"),
                "Experience": exp_info.get("experience_level", "Not specified"),
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
            for col in ["Job Title", "Company", "Location", "Industry", "Experience", "Job Type"]:
                df[col] = df[col].fillna("Not specified").astype(str).str.strip().str.title()
            df["Posted"] = pd.to_datetime(df["Posted"], errors="coerce")
            df["Experience"] = df["Experience"].replace("None", "Not specified")

            st.session_state["job_data"] = df.copy()

            # Save fallback
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            df.to_csv(fallback_path, index=False)
            st.success("✅ Job results saved.")

        else:
            # ------------------ Fallback Logic with Filtering ------------------
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            if os.path.exists(fallback_path):
                fallback_df = pd.read_csv(fallback_path)

                # ---------- Clean and Standardize Columns ----------
                for col in ["Job Title", "Company", "Location", "Industry", "Experience", "Job Type"]:
                    fallback_df[col] = (
                        fallback_df[col]
                        .fillna("Not specified")
                        .astype(str)
                        .str.strip()
                        .str.title()
                    )

                fallback_df = fallback_df.drop_duplicates(subset=["Job Title", "Company", "Location", "Posted"])

                # ---------- Apply Filters ----------
                filtered_fallback = fallback_df.copy()

                if job_title:
                    filtered_fallback = filtered_fallback[
                        filtered_fallback["Job Title"].str.contains(job_title, case=False, na=False)
                    ]
                if location:
                    filtered_fallback = filtered_fallback[
                        filtered_fallback["Location"].str.contains(location, case=False, na=False)
                    ]
                if industry:
                    filtered_fallback = filtered_fallback[
                        filtered_fallback["Industry"].str.contains(industry, case=False, na=False)
                    ]
                if experience_filter != "All":
                    filtered_fallback = filtered_fallback[
                        filtered_fallback["Experience"].str.contains(experience_filter, case=False, na=False)
                    ]
                if job_type_filter != "All":
                    filtered_fallback = filtered_fallback[
                        filtered_fallback["Job Type"].str.contains(job_type_filter, case=False, na=False)
                    ]

                # ---------- Final Cleaned Output ----------
                if not filtered_fallback.empty:
                    st.session_state["job_data"] = filtered_fallback
                    st.success("⚠️ Loaded from fallback — results may be outdated but cleaned and filtered.")
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

        # ---------- Clean & Standardize Columns ----------
        for col in ["Location", "Job Title", "Company", "Job Type", "Experience", "Industry"]:
            df[col] = df[col].fillna("Not specified").astype(str).str.strip().str.title()

        df = df.drop_duplicates(subset=["Job Title", "Company", "Location", "Posted"])

        # ---------- 1. Top Job Locations ----------
        top_cities = df[df["Location"] != "Not specified"]["Location"].value_counts().head(10)
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_cities.values, y=top_cities.index, ax=ax1, palette="coolwarm")
        ax1.set_title("Top Job Locations")
        ax1.set_xlabel("Number of Jobs")
        ax1.set_ylabel("City")
        st.pyplot(fig1)

        # ---------- 2. Most Common Job Titles ----------
        top_titles = df[df["Job Title"] != "Not specified"]["Job Title"].value_counts().head(10)
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_titles.values, y=top_titles.index, ax=ax2, palette="Blues_d")
        ax2.set_title("Most Common Job Titles")
        ax2.set_xlabel("Number of Jobs")
        ax2.set_ylabel("Job Title")
        st.pyplot(fig2)

        # ---------- 3. Top Hiring Companies ----------
        top_companies = df[df["Company"] != "Not specified"]["Company"].value_counts().head(10)
        fig3, ax3 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_companies.values, y=top_companies.index, ax=ax3, palette="crest")
        ax3.set_title("Top Companies Hiring")
        ax3.set_xlabel("Number of Jobs")
        ax3.set_ylabel("Company")
        st.pyplot(fig3)

        # ---------- 4. Job Type Distribution ----------
        job_type_counts = df[df["Job Type"] != "Not specified"]["Job Type"].value_counts()
        fig4, ax4 = plt.subplots(figsize=(6, 5))
        job_type_counts.plot.pie(autopct="%1.1f%%", startangle=90, ax=ax4)
        ax4.set_ylabel("")
        ax4.set_title("Job Type Distribution")
        st.pyplot(fig4)

        # ---------- 5. Experience Level Distribution ----------
        exp_counts = df[df["Experience"] != "Not specified"]["Experience"].value_counts()
        fig5, ax5 = plt.subplots(figsize=(6, 5))
        exp_counts.plot.pie(autopct="%1.1f%%", startangle=90, ax=ax5)
        ax5.set_ylabel("")
        ax5.set_title("Experience Level Distribution")
        st.pyplot(fig5)

        # ---------- 6. Job Posting Trend Over Time ----------
        st.markdown("### 📈 Job Posting Trend Over Time")
        df["Posted"] = pd.to_datetime(df["Posted"], errors="coerce")
        trend_df = df.dropna(subset=["Posted"]).copy()
        if not trend_df.empty:
            trend_df["Posted_Date"] = trend_df["Posted"].dt.date
            trend = trend_df.groupby("Posted_Date").size()
            fig6, ax6 = plt.subplots(figsize=(10, 5))
            trend.plot(ax=ax6, marker='o')
            ax6.set_title("Job Postings Over Time")
            ax6.set_xlabel("Date")
            ax6.set_ylabel("Number of Postings")
            ax6.grid(True)
            st.pyplot(fig6)
        else:
            st.info("📅 No valid posting dates available for trend analysis.")
    else:
        st.warning("No data available after filtering.")