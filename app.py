import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
from datetime import datetime
import os

# ------------------ Streamlit Setup ------------------
st.set_page_config(page_title="Job Skill Finder - India", layout="wide")
st.title("💼 Real-Time Job Search with Skills & Trends (Internshala)")

# ------------------ Session State Init ------------------
if "job_data" not in st.session_state:
    st.session_state["job_data"] = None

# ------------------ User Input ------------------
st.markdown("## 🔍 Enter Search Criteria")
job_title = st.text_input("Job Title:", "Data Analyst")
location = st.text_input("Location:", "India")
skill = st.text_input("Required Skill (optional):", "")

# ------------------ Scraper Function ------------------
def scrape_internshala(query, location):
    jobs = []
    try:
        formatted_query = query.lower().replace(" ", "-")
        url = f"https://internshala.com/jobs/{formatted_query}-jobs"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.content, "html5lib")
        job_cards = soup.find_all("div", class_="individual_internship")

        for post in job_cards:
            title_elem = post.find("div", class_="heading_4_5")
            company_elem = post.find("a", class_="link_display_like_text")
            location_elem = post.find("a", class_="location_link")
            start_date_elem = post.find("div", class_="item_body", text=True)
            date_elem = post.find("div", class_="posted_by_container")

            jobs.append({
                "Job Title": title_elem.text.strip() if title_elem else "N/A",
                "Company": company_elem.text.strip() if company_elem else "N/A",
                "Location": location_elem.text.strip() if location_elem else "Not Specified",
                "Posted": datetime.today().strftime("%Y-%m-%d"),
                "Skills": skill if skill else "N/A",
                "Apply Link": "https://internshala.com" + post.a['href'] if post.a and post.a.get('href') else "N/A"
            })
    except Exception as e:
        st.error(f"Error fetching jobs: {e}")
    return jobs

# ------------------ Job Search ------------------
if st.button("🔍 Search Jobs"):
    with st.spinner("Scraping jobs from Internshala..."):
        jobs = scrape_internshala(job_title, location)

        if jobs:
            df = pd.DataFrame(jobs)
            df['Posted'] = pd.to_datetime(df['Posted'], errors='coerce').dt.date
            df['Apply Link'] = df['Apply Link'].apply(lambda x: f"[Apply]({x})")
            st.session_state["job_data"] = df.copy()

            # Save fallback
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            df.to_csv(fallback_path, index=False)
            st.success("✅ Job results updated and fallback saved.")
        else:
            st.warning("😕 No jobs found.")

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

    # Filters
    filtered_df = df.copy()
    if selected_city != "All":
        filtered_df = filtered_df[filtered_df["Location"] == selected_city]
    if selected_skill != "All":
        filtered_df = filtered_df[filtered_df["Skills"].str.contains(selected_skill)]

    st.success(f"Showing {len(filtered_df)} jobs after filtering.")
    st.markdown("### 📋 Filtered Job Listings")
    st.write(filtered_df.to_markdown(index=False), unsafe_allow_html=True)

    # ------------------ Charts ------------------
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
    else:
        st.warning("No data available after filtering.")