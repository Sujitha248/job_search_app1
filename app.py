import streamlit as st import requests import pandas as pd import matplotlib.pyplot as plt import seaborn as sns from bs4 import BeautifulSoup from datetime import datetime from prophet import Prophet import os

------------------ Streamlit Setup ------------------

st.set_page_config(page_title="Job Skill Finder - India", layout="wide") st.title("💼 Real-Time Job Search with Skills & Trends (Naukri)")

------------------ Session State Init ------------------

if "job_data" not in st.session_state: st.session_state["job_data"] = None

------------------ User Input ------------------

st.markdown("## 🔍 Enter Search Criteria") job_title = st.text_input("Job Title:", "Data Scientist") location = st.text_input("Location:", "India")

st.markdown("### 🎯 Optional Filters") skill = st.text_input("Required Skill (optional):", "") experience = st.selectbox("Experience Level (Years):", ["", "0", "1", "2", "3", "4", "5+"]) salary = st.selectbox("Minimum Salary (LPA):", ["", "2", "4", "6", "10", "15"])

------------------ Scraper Function ------------------

def scrape_naukri(query, location): jobs = [] try: search_query = query.replace(" ", "-") loc = location.replace(" ", "-") url = f"https://www.naukri.com/{search_query}-jobs-in-{loc}" headers = {"User-Agent": "Mozilla/5.0"} r = requests.get(url, headers=headers) soup = BeautifulSoup(r.text, "html.parser")

listings = soup.find_all("article", class_="jobTuple")
    for post in listings:
        title = post.find("a", class_="title")
        company = post.find("a", class_="subTitle")
        exp = post.find("li", class_="exp")
        loc = post.find("li", class_="location")
        sal = post.find("li", class_="salary")
        date = post.find("span", class_="job-post-day")

        jobs.append({
            "Job Title": title.text.strip() if title else "N/A",
            "Company": company.text.strip() if company else "N/A",
            "Location": loc.text.strip() if loc else "Not Specified",
            "Experience": exp.text.strip() if exp else "N/A",
            "Salary": sal.text.strip() if sal else "N/A",
            "Posted": date.text.strip() if date else datetime.today().strftime("%Y-%m-%d"),
            "Skills": skill if skill else "N/A",
            "Apply Link": title['href'] if title else "N/A"
        })
except Exception as e:
    st.error(f"Scraping failed: {e}")
return jobs

------------------ Job Search ------------------

if st.button("🔍 Search Jobs"): with st.spinner("Scraping jobs from Naukri.com..."): jobs = scrape_naukri(job_title, location)

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

------------------ Display and Insights ------------------

if st.session_state["job_data"] is not None: df = st.session_state["job_data"]

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

    st.markdown("## 🔮 Forecast (Next 7 Days)")
    prophet_df = trend_df.rename(columns={"Posted": "ds", "Job Count": "y"})
    model = Prophet()
    model.fit(prophet_df)
    future = model.make_future_dataframe(periods=7)
    forecast = model.predict(future)
    fig5 = model.plot(forecast)
    st.pyplot(fig5)
else:
    st.warning("No data available after filtering.")
            