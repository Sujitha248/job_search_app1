import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
from datetime import datetime
import os

# ------------------ Streamlit Setup ------------------
st.set_page_config(page_title="Internshala Job Search", layout="wide")
st.title("📘 Real-Time Internships & Jobs - Internshala (India)")

# ------------------ Session State ------------------
if "job_data" not in st.session_state:
    st.session_state["job_data"] = None

# ------------------ User Input ------------------
st.markdown("## 🔍 Enter Search Criteria")
job_title = st.text_input("Job Title:", "Data Science")
location = st.text_input("Location:", "India")
skill = st.text_input("Required Skill (optional):", "")

# ------------------ Scraper ------------------
def scrape_internshala(title):
    jobs = []
    try:
        url = f"https://internshala.com/internships/keywords-{title.replace(' ', '-')}/"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        listings = soup.find_all("div", class_="individual_internship")

        for post in listings:
            title_tag = post.find("div", class_="heading_4_5")
            company_tag = post.find("a", class_="link_display_like_text")
            location_tag = post.find("a", class_="location_link")
            posted_tag = post.find("div", class_="status-container")
            link_tag = post.find("a", class_="view_detail_button")

            jobs.append({
                "Job Title": title_tag.text.strip() if title_tag else "N/A",
                "Company": company_tag.text.strip() if company_tag else "N/A",
                "Location": location_tag.text.strip() if location_tag else "Not Specified",
                "Posted": datetime.today().strftime("%Y-%m-%d"),
                "Skills": skill if skill else "N/A",
                "Apply Link": "https://internshala.com" + link_tag['href'] if link_tag else "N/A"
            })
    except Exception as e:
        st.error(f"Scraping failed: {e}")
    return jobs

# ------------------ Job Search ------------------
if st.button("🔍 Search Jobs"):
    with st.spinner("Fetching from Internshala..."):
        jobs = scrape_internshala(job_title)

        if jobs:
            df = pd.DataFrame(jobs)
            df['Posted'] = pd.to_datetime(df['Posted'], errors='coerce').dt.date
            df['Apply Link'] = df['Apply Link'].apply(lambda x: f"[Apply]({x})")
            st.session_state["job_data"] = df.copy()

            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            df.to_csv(fallback_path, index=False)
            st.success("✅ Job results updated.")
        else:
            st.warning("😕 No jobs found.")

# ------------------ Display Results ------------------
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

    # ------------------ Charts ------------------
    if not filtered_df.empty:
        st.markdown("## 📊 Job Market Insights")

        top_cities = filtered_df["Location"].value_counts().head(10)
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_cities.values, y=top_cities.index, ax=ax1, palette="coolwarm")
        ax1.set_title("Top Locations")
        st.pyplot(fig1)

        top_titles = filtered_df["Job Title"].value_counts().head(10)
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_titles.values, y=top_titles.index, ax=ax2, palette="Blues_d")
        ax2.set_title("Top Job Titles")
        st.pyplot(fig2)

        top_companies = filtered_df["Company"].value_counts().head(10)
        fig3, ax3 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_companies.values, y=top_companies.index, ax=ax3, palette="crest")
        ax3.set_title("Top Companies")
        st.pyplot(fig3)
    else:
        st.warning("No data available after filtering.")