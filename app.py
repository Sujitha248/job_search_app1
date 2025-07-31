import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
from datetime import datetime
from prophet import Prophet
import os

# ------------------ Streamlit Setup ------------------

st.set_page_config(page_title="Job Explorer", layout="wide")
st.title("💼 Real-Time Job Explorer")

# ------------------ Session State Init ------------------

if "job_data" not in st.session_state:
    st.session_state["job_data"] = None

# ------------------ User Input Section ------------------

st.markdown("## 🔍 Enter Search Criteria")
job_title = st.text_input("Job Title:", "")
location = st.text_input("Location:", "India")

st.markdown("### 🎯 Optional Filters")
skill = st.text_input("Required Skill (optional):", "")
experience = st.selectbox("Experience Level:", ["", "Entry level", "Mid-Senior level", "Manager", "Director"])
industry = st.text_input("Industry (optional):", "")

# ------------------ Web Scraping Function ------------------

def scrape_jobs(query):
    jobs = []
    try:
        search_query = query.replace(" ", "+")
        url = f"https://www.simplyhired.co.in/search?q={search_query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        listings = soup.find_all("div", class_="SerpJob-jobCard")

        for post in listings:
            title = post.find("a", class_="SerpJob-linkCard").text.strip() if post.find("a", class_="SerpJob-linkCard") else "N/A"
            company = post.find("span", class_="JobPosting-labelWithIcon").text.strip() if post.find("span", class_="JobPosting-labelWithIcon") else "N/A"
            loc = post.find("span", class_="JobPosting-labelWithIcon jobposting-location").text.strip() if post.find("span", class_="JobPosting-labelWithIcon jobposting-location") else "Not Specified"
            posted = post.find("time")['datetime'] if post.find("time") else datetime.today().isoformat()
            link = "https://www.simplyhired.co.in" + post.find("a", class_="SerpJob-linkCard")['href'] if post.find("a", class_="SerpJob-linkCard") else "N/A"
            jobs.append({
                "Job Title": title,
                "Company": company,
                "Location": loc,
                "Posted": posted[:10],
                "Skills": "N/A",
                "Apply Link": link
            })

    except Exception as e:
        st.error(f"Scraping failed: {e}")
    return jobs

# ------------------ Search Button ------------------

if st.button("🔍 Search Jobs"):
    with st.spinner("Scraping jobs..."):
        query = f"{job_title} {location} {skill} {experience} {industry}"
        jobs = scrape_jobs(query)

        if jobs:
            df = pd.DataFrame(jobs)
            df["Posted"] = pd.to_datetime(df["Posted"]).dt.date
            df['Apply Link'] = df['Apply Link'].apply(lambda x: f"[Apply]({x})")
            st.session_state["job_data"] = df.copy()

            # Save fallback
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            df.to_csv(fallback_path, index=False)
            st.success("✅ Job results updated and fallback saved.")
        else:
            st.warning("😕 No jobs found.")
            st.write("Debug Info: No listings returned from the site.")
            st.code(query)

# ------------------ Show Filters and Charts ------------------

if st.session_state["job_data"] is not None:
    df = st.session_state["job_data"]

    st.markdown("## 🎛 Filter Results")
    available_cities = df["Location"].dropna().unique().tolist()
    if "Not Specified" in available_cities:
        available_cities.remove("Not Specified")
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

    st.markdown("## 📊 Job Market Insights")
    if not filtered_df.empty:
        top_cities = filtered_df["Location"].value_counts().head(10)
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_cities.values, y=top_cities.index, ax=ax1, palette="coolwarm")
        ax1.set_title("Top Job Locations")
        ax1.set_xlabel("Job Count")
        ax1.set_ylabel("City")
        st.pyplot(fig1)

        top_titles = filtered_df["Job Title"].value_counts().head(10)
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_titles.values, y=top_titles.index, ax=ax2, palette="light:#5A9")
        ax2.set_title("Most Common Job Titles")
        st.pyplot(fig2)

        top_companies = filtered_df["Company"].value_counts().head(10)
        fig4, ax4 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_companies.values, y=top_companies.index, ax=ax4, palette="crest")
        ax4.set_title("Top Companies Hiring")
        ax4.set_xlabel("Number of Jobs")
        ax4.set_ylabel("Company")
        st.pyplot(fig4)

        trend_df = filtered_df.groupby("Posted").size().reset_index(name="Job Count")
        fig5, ax5 = plt.subplots(figsize=(8, 5))
        sns.lineplot(data=trend_df, x="Posted", y="Job Count", marker="o", ax=ax5)
        ax5.set_title("Job Posting Trend Over Time")
        st.pyplot(fig5)

        st.markdown("## 🔮 Job Forecast (Next 7 Days)")
        prophet_df = trend_df.rename(columns={"Posted": "ds", "Job Count": "y"})
        model = Prophet()
        model.fit(prophet_df)
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)
        fig6 = model.plot(forecast)
        st.pyplot(fig6)
    else:
        st.warning("No data available after filtering.")