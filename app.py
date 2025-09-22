import streamlit as st
import requests
import pandas as pd
import plotly.express as px
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

experience_filter = st.selectbox(
    "Experience Level (optional):",
    ["All", "Internship", "Entry level", "Mid level", "Senior level", "Executive"]
)
job_type_filter = st.selectbox(
    "Job Type (optional):",
    ["All", "Full-time", "Part-time", "Contract", "Internship", "Temporary"]
)

# ------------------ API Key from Secrets ------------------
API_KEY = st.secrets["JSEARCH_API_KEY"]
API_URL = "https://jsearch.p.rapidapi.com/search"

# ------------------ Preprocessing ------------------
def preprocess_data(df):
    if df is None or df.empty:
        return df
    df.drop_duplicates(inplace=True)
    if "Posted" in df.columns:
        df["Posted"] = pd.to_datetime(df["Posted"], errors="coerce").dt.date
    for col in ["Job Title", "Company", "Location", "Industry", "Experience", "Job Type"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()
    df.replace(["Not specified", "nan", "NaT"], "Unknown", inplace=True)
    df.fillna("Unknown", inplace=True)
    return df

# ------------------ Fetch Jobs ------------------
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

# ------------------ Search Logic ------------------
if st.button("🔍 Search Jobs"):
    with st.spinner("Fetching jobs..."):
        jobs = fetch_jobs(job_title, location)
        if jobs:
            df = pd.DataFrame(jobs)
            df = preprocess_data(df)
            st.session_state["job_data"] = df.copy()
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            df.to_csv(fallback_path, index=False)
            st.success("✅ Job results updated and fallback saved.")
        else:
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            if os.path.exists(fallback_path):
                fallback_df = pd.read_csv(fallback_path)
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
                filtered_fallback = preprocess_data(filtered_fallback)
                if not filtered_fallback.empty:
                    st.session_state["job_data"] = filtered_fallback
                    st.success("⚠ Loaded from fallback — results may be outdated.")
                else:
                    st.warning("😕 No matching jobs found in fallback.")
            else:
                st.warning("⚠ No fallback file found.")

# ------------------ Display & Tabs ------------------
if st.session_state["job_data"] is not None:
    df = st.session_state["job_data"]
    st.success(f"Showing {len(df)} jobs.")
    st.markdown("### 📋 Job Listings (click links to apply)")
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # ------------------ Tabs for clean layout ------------------
    tabs = st.tabs(["Overview", "Experience & Type", "Industry", "Trends"])

    # Tab 1: Overview
    with tabs[0]:
        st.markdown("### Top Job Locations")
        top_cities = df["Location"].value_counts().head(10)
        fig1 = px.bar(x=top_cities.values, y=top_cities.index, orientation='h',
                      labels={'x':'Number of Jobs','y':'Location'},
                      title='Top Job Locations',
                      color=top_cities.values, color_continuous_scale='Cool')
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("### Most Common Job Titles")
        top_titles = df["Job Title"].value_counts().head(10)
        fig2 = px.bar(x=top_titles.values, y=top_titles.index, orientation='h',
                      labels={'x':'Number of Jobs','y':'Job Title'},
                      title='Most Common Job Titles',
                      color=top_titles.values, color_continuous_scale='Blues')
        st.plotly_chart(fig2, use_container_width=True)

    # Tab 2: Experience & Job Type
    with tabs[1]:
        st.markdown("### Jobs by Experience Level")
        exp_dist = df["Experience"].value_counts()
        fig_exp = px.bar(x=exp_dist.index, y=exp_dist.values,
                         labels={'x':'Experience Level','y':'Number of Jobs'},
                         title='Jobs by Experience Level',
                         color=exp_dist.values, color_continuous_scale='Magma')
        st.plotly_chart(fig_exp, use_container_width=True)

        st.markdown("### Jobs by Job Type")
        job_type_dist = df["Job Type"].value_counts()
        fig_jt = px.bar(x=job_type_dist.index, y=job_type_dist.values,
                        labels={'x':'Job Type','y':'Number of Jobs'},
                        title='Jobs by Job Type',
                        color=job_type_dist.values, color_continuous_scale='Set2')
        st.plotly_chart(fig_jt, use_container_width=True)

    # Tab 3: Industry
    with tabs[2]:
        st.markdown("### Top Industries Hiring")
        industry_dist = df["Industry"].value_counts().head(10)
        fig_ind = px.bar(x=industry_dist.values, y=industry_dist.index, orientation='h',
                         labels={'x':'Number of Jobs','y':'Industry'},
                         title='Jobs by Industry',
                         color=industry_dist.values, color_continuous_scale='Viridis')
        st.plotly_chart(fig_ind, use_container_width=True)

    # Tab 4: Trends
    with tabs[3]:
        if "Posted" in df.columns:
            trend_df = df[df["Posted"] != "Unknown"]
            trend_df["Posted"] = pd.to_datetime(trend_df["Posted"], errors='coerce')
            trend_df = trend_df.dropna(subset=["Posted"])
            trend = trend_df.groupby(trend_df["Posted"].dt.to_period("M")).size()
            trend.index = trend.index.to_timestamp()
            fig_trend = px.line(x=trend.index, y=trend.values,
                                labels={'x':'Date','y':'Number of Jobs'},
                                title='Job Posting Trend Over Time',
                                markers=True)
            st.plotly_chart(fig_trend, use_container_width=True)