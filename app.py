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
    for col in ["Job Title", "Company", "Location", "Job Type"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()
    df.replace(["Not Specified", "nan", "NaT"], "Unknown", inplace=True)
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
            st.success("✅ Job results updated.")
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

# ------------------ Display Job Listings and Charts ------------------
if st.session_state["job_data"] is not None:
    df = st.session_state["job_data"]

    # ------------------ Job Listings Table ------------------
    st.markdown("### 📋 Job Listings")

    # Keep only relevant columns
    display_df = df[["Job Title", "Company", "Location", "Job Type", "Posted", "Apply Link"]].copy()

    # Format Apply Link as clickable Markdown (original lambda)
    display_df["Apply Link"] = display_df["Apply Link"].apply(
        lambda x: f"[Apply Here]({x.split('href=')[1].split(' ')[0].strip(\"'\")})"
    )

    # Display as interactive dataframe
    st.dataframe(display_df, use_container_width=True)

    # ------------------ Overview Tab ------------------
    tabs = st.tabs(["Overview"])
    with tabs[0]:
        # Top Job Locations
        st.markdown("### Top Job Locations")
        top_cities = df["Location"].value_counts().head(10)
        fig1 = px.bar(
            x=top_cities.values,
            y=top_cities.index,
            orientation='h',
            labels={'x':'Number of Jobs','y':'Location'},
            title='Top Job Locations',
            color=top_cities.values,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig1, use_container_width=True)

        # Most Common Job Titles
        st.markdown("### Most Common Job Titles")
        top_titles = df["Job Title"].value_counts().head(10)
        fig2 = px.bar(
            x=top_titles.values,
            y=top_titles.index,
            orientation='h',
            labels={'x':'Number of Jobs','y':'Job Title'},
            title='Most Common Job Titles',
            color=top_titles.values,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Top Companies Hiring
        st.markdown("### Top Companies Hiring")
        top_companies = df["Company"].value_counts().head(10)
        fig3 = px.bar(
            x=top_companies.values,
            y=top_companies.index,
            orientation='h',
            labels={'x':'Number of Jobs', 'y':'Company'},
            title='Top Companies Hiring',
            color=top_companies.values,
            color_continuous_scale='Plasma'
        )
        st.plotly_chart(fig3, use_container_width=True)