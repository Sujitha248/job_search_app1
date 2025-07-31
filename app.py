import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
from datetime import datetime
import os

# ------------------ Streamlit Setup ------------------
st.set_page_config(page_title="Indeed Job Scraper", layout="wide")
st.title("💼 Real-Time Job Search (Indeed India)")

# ------------------ Session Init ------------------
if "job_data" not in st.session_state:
    st.session_state["job_data"] = None

# ------------------ User Input ------------------
st.markdown("## 🔍 Enter Search Criteria")
job_title = st.text_input("Job Title:", "Data Analyst")
location = st.text_input("Location:", "India")
skill = st.text_input("Required Skill (optional):", "")

# ------------------ Scraper Function ------------------
def scrape_indeed(title, loc):
    jobs = []
    try:
        base_url = "https://in.indeed.com"
        search_url = f"{base_url}/jobs?q={title.replace(' ', '+')}&l={loc.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        job_cards = soup.find_all("a", class_="jcs-JobTitle")

        for card in job_cards:
            parent = card.find_parent("h2", class_="jobTitle")
            company_span = soup.find("span", {"data-testid": "company-name"})
            location_div = soup.find("div", {"data-testid": "text-location"})

            jobs.append({
                "Job Title": card.text.strip() if card else "N/A",
                "Company": company_span.text.strip() if company_span else "N/A",
                "Location": location_div.text.strip() if location_div else "N/A",
                "Posted": datetime.today().strftime("%Y-%m-%d"),
                "Skills": skill if skill else "N/A",
                "Apply Link": base_url + card["href"] if card and card.has_attr("href") else "N/A"
            })
    except Exception as e:
        st.error(f"Error fetching jobs: {e}")
    return jobs

# ------------------ Job Search ------------------
if st.button("🔍 Search Jobs"):
    with st.spinner("Scraping jobs from Indeed..."):
        job_results = scrape_indeed(job_title, location)

        if job_results:
            df = pd.DataFrame(job_results)
            df["Posted"] = pd.to_datetime(df["Posted"], errors="coerce").dt.date
            df["Apply Link"] = df["Apply Link"].apply(lambda x: f"[Apply]({x})")
            st.session_state["job_data"] = df.copy()

            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            df.to_csv(fallback_path, index=False)
            st.success("✅ Job results updated and fallback saved.")
        else:
            st.warning("😕 No jobs found.")

# ------------------ Display Results ------------------
if st.session_state["job_data"] is not None:
    df = st.session_state["job_data"]

    st.markdown("## 🎛 Filter Results")
    cities = sorted(df["Location"].dropna().unique())
    selected_city = st.selectbox("📍 Filter by City:", ["All"] + cities)

    skills = sorted(set(
        sk.strip() for s in df["Skills"] if s != "N/A"
        for sk in s.split(",")
    ))
    selected_skill = st.selectbox("🛠 Filter by Skill:", ["All"] + skills)

    filtered_df = df.copy()
    if selected_city != "All":
        filtered_df = filtered_df[filtered_df["Location"] == selected_city]
    if selected_skill != "All":
        filtered_df = filtered_df[filtered_df["Skills"].str.contains(selected_skill)]

    st.success(f"Showing {len(filtered_df)} jobs after filtering.")
    st.markdown("### 📋 Job Listings")
    st.write(filtered_df.to_markdown(index=False), unsafe_allow_html=True)

    if not filtered_df.empty:
        st.markdown("## 📊 Job Insights")

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
    else:
        st.warning("No data to visualize.")