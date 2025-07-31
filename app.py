import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
from datetime import datetime
from prophet import Prophet
import os

# ---------------------- Streamlit Setup ----------------------
st.set_page_config(page_title="Internship & Fresher Job Finder - India", layout="wide")
st.title("💼 Real-Time Internship & Fresher Job Search (Internshala)")

# ---------------------- Session State ----------------------
if "job_data" not in st.session_state:
    st.session_state["job_data"] = None

# ---------------------- User Input ----------------------
st.markdown("## 🔍 Enter Search Criteria")
job_title = st.text_input("Job Title:", "Python Developer")
location = st.text_input("Location:", "India")

# ---------------------- Scraper Function ----------------------
def scrape_internshala(query, location):
    jobs = []
    try:
        base_url = "https://internshala.com/internships/"
        query_url = f"{base_url}{query.replace(' ', '-')}-internship-in-{location.replace(' ', '-')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(query_url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        listings = soup.find_all("div", class_="individual_internship")

        for post in listings:
            title_tag = post.find("div", class_="heading_4_5")
            title = title_tag.text.strip() if title_tag else "N/A"
            link = "https://internshala.com" + title_tag.a["href"] if title_tag and title_tag.a else "N/A"

            company_tag = post.find("div", class_="company_name")
            company = company_tag.text.strip() if company_tag else "N/A"

            location_tag = post.find("a", class_="location_link")
            job_location = location_tag.text.strip() if location_tag else "N/A"

            start_date = post.find("div", class_="start-date")
            posted = start_date.text.strip() if start_date else datetime.today().strftime("%Y-%m-%d")

            jobs.append({
                "Job Title": title,
                "Company": company,
                "Location": job_location,
                "Experience": "Intern/Fresher",
                "Salary": "N/A",
                "Posted": posted,
                "Skills": "N/A",
                "Apply Link": link
            })
    except Exception as e:
        st.error(f"Scraping failed: {e}")
    return jobs

# ---------------------- Job Search ----------------------
if st.button("🔍 Search Jobs"):
    with st.spinner("Scraping Internshala..."):
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

# ---------------------- Display Results & Insights ----------------------
if st.session_state["job_data"] is not None:
    df = st.session_state["job_data"]

    st.markdown("## 🎛 Filter Results")
    cities = sorted(df["Location"].dropna().unique())
    selected_city = st.selectbox("📍 Filter by City:", ["All"] + cities)

    filtered_df = df.copy()
    if selected_city != "All":
        filtered_df = filtered_df[filtered_df["Location"] == selected_city]

    st.success(f"Showing {len(filtered_df)} jobs after filtering.")
    st.markdown("### 📋 Filtered Job Listings")
    st.write(filtered_df.to_markdown(index=False), unsafe_allow_html=True)

    # ---------------------- Charts ----------------------
    if not filtered_df.empty:
        st.markdown("## 📊 Job Market Insights")

        top_cities = filtered_df["Location"].value_counts().head(10)
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_cities.values, y=top_cities.index, ax=ax1, palette="coolwarm")
        ax1.set_title("Top Internship Locations")
        st.pyplot(fig1)

        top_titles = filtered_df["Job Title"].value_counts().head(10)
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_titles.values, y=top_titles.index, ax=ax2, palette="Blues_d")
        ax2.set_title("Most Common Internship Titles")
        st.pyplot(fig2)

        trend_df = filtered_df.groupby("Posted").size().reset_index(name="Job Count")
        st.markdown("## 🔮 Forecast (Next 7 Days)")
        prophet_df = trend_df.rename(columns={"Posted": "ds", "Job Count": "y"})
        model = Prophet()
        model.fit(prophet_df)
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)
        fig3 = model.plot(forecast)
        st.pyplot(fig3)
    else:
        st.warning("No data available after filtering.")