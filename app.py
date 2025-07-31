import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt
import seaborn as sns
from prophet import Prophet

# ------------------ Streamlit Setup ------------------
st.set_page_config(page_title="Job Explorer", layout="wide")
st.title("💼 Real-Time Job Explorer")

# ------------------ Session State Init ------------------
if "job_data" not in st.session_state:
    st.session_state["job_data"] = None

# ------------------ User Input ------------------
st.markdown("## 🔍 Enter Search Criteria")
job_title = st.text_input("Job Title:", "")
location = st.text_input("Location (optional):", "")
skill = st.text_input("Required Skill (optional):", "")

# ------------------ Scraping Functions ------------------
def scrape_weworkremotely(query):
    jobs = []
    try:
        search_query = query.replace(" ", "+")
        url = f"https://weworkremotely.com/remote-jobs/search?term={search_query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        sections = soup.find_all("section", class_="jobs")
        for section in sections:
            listings = section.find_all("li", class_=lambda x: x != "view-all")
            for job in listings:
                link_tag = job.find("a", href=True)
                if link_tag:
                    title = job.find("span", class_="title").text.strip() if job.find("span", class_="title") else "N/A"
                    company = job.find("span", class_="company").text.strip() if job.find("span", class_="company") else "N/A"
                    location = job.find("span", class_="region company").text.strip() if job.find("span", class_="region company") else "Remote"
                    link = "https://weworkremotely.com" + link_tag["href"]
                    jobs.append({
                        "Job Title": title,
                        "Company": company,
                        "Location": location,
                        "Posted": datetime.today().date(),
                        "Skills": "N/A",
                        "Apply Link": link
                    })
    except Exception as e:
        st.error(f"Scraping WeWorkRemotely failed: {e}")
    return jobs

def scrape_remoteok(query):
    jobs = []
    try:
        search_query = query.replace(" ", "-")
        url = f"https://remoteok.com/remote-{search_query}-jobs"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.find_all("tr", class_="job")
        for job in rows:
            title = job.find("h2").text.strip() if job.find("h2") else "N/A"
            company = job.find("h3").text.strip() if job.find("h3") else "N/A"
            location = job.find("div", class_="location").text.strip() if job.find("div", class_="location") else "Remote"
            link_tag = job.find("a", class_="preventLink", href=True)
            link = "https://remoteok.com" + link_tag["href"] if link_tag else "N/A"
            jobs.append({
                "Job Title": title,
                "Company": company,
                "Location": location,
                "Posted": datetime.today().date(),
                "Skills": "N/A",
                "Apply Link": link
            })
    except Exception as e:
        st.error(f"Scraping RemoteOK failed: {e}")
    return jobs

# ------------------ Trigger Search ------------------
if st.button("🔍 Search Jobs"):
    with st.spinner("Scraping job listings..."):
        query = f"{job_title} {location} {skill}".strip()
        jobs = scrape_weworkremotely(query) + scrape_remoteok(query)

        if jobs:
            df = pd.DataFrame(jobs)
            df['Apply Link'] = df['Apply Link'].apply(lambda x: f"[Apply]({x})")
            st.session_state["job_data"] = df.copy()
            # Save fallback
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            df.to_csv(fallback_path, index=False)
            st.success("✅ Job results updated and fallback saved.")
        else:
            # Try fallback
            if os.path.exists("fallback_jobs.csv"):
                df = pd.read_csv("fallback_jobs.csv")
                st.session_state["job_data"] = df.copy()
                st.warning("⚠ Showing fallback data as no jobs were scraped.")
            else:
                st.error("❌ No jobs found and no fallback available.")

# ------------------ Filter + Display ------------------
if st.session_state["job_data"] is not None:
    df = st.session_state["job_data"]
    st.markdown("## 🎛 Filter Results")

    available_cities = df["Location"].dropna().unique().tolist()
    if "Remote" in available_cities:
        available_cities.remove("Remote")
    selected_city = st.selectbox("📍 Filter by City:", ["All"] + sorted(available_cities))

    available_skills = sorted(set(
        skill.strip() for skills in df["Skills"] if skills != "N/A"
        for skill in skills.split(",")
    ))
    selected_skill = st.selectbox("🛠 Filter by Skill:", ["All"] + available_skills)

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
        sns.barplot(x=top_titles.values, y=top_titles.index, ax=ax2, palette="pastel")
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

        st.markdown("## 🔮 Job Forecast (Next 7 Days)")
        prophet_df = trend_df.rename(columns={"Posted": "ds", "Job Count": "y"})
        model = Prophet()
        model.fit(prophet_df)
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)
        fig5 = model.plot(forecast)
        st.pyplot(fig5)
    else:
        st.warning("No data available after filtering.")