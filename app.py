import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
from datetime import datetime
from prophet import Prophet
import os

st.set_page_config(page_title="Job Skill Finder - India", layout="wide")
st.title("💼 Real-Time Job Search with Skills & Trends (WorkIndia)")

# Initialize session
if "job_data" not in st.session_state:
    st.session_state["job_data"] = None

# User Input
st.markdown("Enter Search Criteria")
job_title = st.text_input("Job Title:", "Data Scientist")
location = st.text_input("Location:", "India")

st.markdown("Optional Filters")
skill = st.text_input("Required Skill (optional):", "")
experience = st.selectbox("Experience Level (Years):", ["", "0", "1", "2", "3", "4", "5+"])
salary = st.selectbox("Minimum Salary (LPA):", ["", "2", "4", "6", "10", "15"])

# Scraper Function
def scrape_workindia(query):
    jobs = []
    try:
        url = "https://www.workindia.in/jobs-search/search.php"
        params = {"q": query}
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, params=params, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")

        listings = soup.find_all("div", class_="job-container")
        for post in listings:
            title = post.find("h2").text.strip() if post.find("h2") else "N/A"
            company = post.find("p", class_="company").text.strip() if post.find("p", class_="company") else "N/A"
            loc = post.find("p", class_="location").text.strip() if post.find("p", class_="location") else "Not Specified"
            exp = post.find("p", class_="experience").text.strip() if post.find("p", class_="experience") else "N/A"
            sal = post.find("p", class_="salary").text.strip() if post.find("p", class_="salary") else "N/A"
            link_tag = post.find("a", href=True)
            link = "https://www.workindia.in" + link_tag['href'] if link_tag else "N/A"
            posted = datetime.today().strftime("%Y-%m-%d")

            jobs.append({
                "Job Title": title,
                "Company": company,
                "Location": loc,
                "Experience": exp,
                "Salary": sal,
                "Posted": posted,
                "Skills": skill if skill else "N/A",
                "Apply Link": link
            })
    except Exception as e:
        st.error(f"Error fetching jobs: {e}")
    return jobs

# Job Search
if st.button("Search Jobs"):
    with st.spinner("Scraping jobs from WorkIndia..."):
        jobs = scrape_workindia(job_title)
        if jobs:
            df = pd.DataFrame(jobs)
            df["Posted"] = pd.to_datetime(df["Posted"], errors='coerce').dt.date
            df['Apply Link'] = df['Apply Link'].apply(lambda x: f"[Apply]({x})")
            st.session_state["job_data"] = df.copy()
            fallback_path = os.path.join(os.getcwd(), "fallback_jobs.csv")
            df.to_csv(fallback_path, index=False)
            st.success("✅ Job results updated and fallback saved.")
        else:
            st.warning("😕 No jobs found.")

# Display and Filters
if st.session_state["job_data"] is not None:
    df = st.session_state["job_data"]

    st.markdown("Filter Results")
    cities = sorted(df["Location"].dropna().unique())
    selected_city = st.selectbox("Filter by City:", ["All"] + cities)

    skills_list = sorted(set(
        sk.strip() for s in df["Skills"] if s != "N/A"
        for sk in s.split(",")
    ))
    selected_skill = st.selectbox("Filter by Skill:", ["All"] + skills_list)

    filtered_df = df.copy()
    if selected_city != "All":
        filtered_df = filtered_df[filtered_df["Location"] == selected_city]
    if selected_skill != "All":
        filtered_df = filtered_df[filtered_df["Skills"].str.contains(selected_skill)]

    st.success(f"Showing {len(filtered_df)} jobs after filtering.")
    st.markdown("Filtered Job Listings")
    st.write(filtered_df.to_markdown(index=False), unsafe_allow_html=True)

    if not filtered_df.empty:
        st.markdown("Job Market Insights")

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

        st.markdown("Forecast (Next 7 Days)")
        prophet_df = trend_df.rename(columns={"Posted": "ds", "Job Count": "y"})
        model = Prophet()
        model.fit(prophet_df)
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)
        fig5 = model.plot(forecast)
        st.pyplot(fig5)
    else:
        st.warning("No data available after filtering.")