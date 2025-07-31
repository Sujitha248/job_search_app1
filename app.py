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
st.title("\U0001F4BC Real-Time Job Explorer")

# ------------------ Session State Init ------------------
if "job_data" not in st.session_state:
    st.session_state["job_data"] = None

# ------------------ User Input Section ------------------
st.markdown("## \U0001F50D Enter Search Criteria")
job_title = st.text_input("Job Title:", "")
location = st.text_input("Location:", "India")

st.markdown("### \U0001F3AF Optional Filters")
skill = st.text_input("Required Skill (optional):", "")
experience = st.selectbox("Experience Level:", ["", "Entry level", "Mid-Senior level", "Manager", "Director"])
industry = st.text_input("Industry (optional):", "")

# ------------------ Scraping Function ------------------
def scrape_remoteok(query):
    jobs = []
    try:
        url = "https://remoteok.com/remote-dev+{}-jobs".format(query.replace(" ", "+"))
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        listings = soup.find_all("tr", class_="job")

        for job in listings:
            title = job.find("h2").text.strip() if job.find("h2") else "N/A"
            company = job.find("h3").text.strip() if job.find("h3") else "N/A"
            tags = ", ".join([tag.text for tag in job.find_all("span", class_="tag")])
            location = job.find("div", class_="location")
            location = location.text.strip() if location else "Remote"
            posted = datetime.today().strftime('%Y-%m-%d')
            link = "https://remoteok.com" + job.get("data-href") if job.get("data-href") else "N/A"

            jobs.append({
                "Job Title": title,
                "Company": company,
                "Location": location,
                "Posted": posted,
                "Skills": tags,
                "Apply Link": link
            })

    except Exception as e:
        st.error(f"Scraping failed: {e}")
    return jobs

# ------------------ Search Button ------------------
if st.button("\U0001F50D Search Jobs"):
    with st.spinner("Scraping jobs..."):
        query = f"{job_title} {location} {skill} {experience} {industry}"
        jobs = scrape_remoteok(query)

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
            st.warning("\U0001F615 No jobs found.")

# ------------------ Show Filters and Charts ------------------
if st.session_state["job_data"] is not None:
    df = st.session_state["job_data"]

    st.markdown("## \U0001F3A7 Filter Results")
    available_cities = df["Location"].dropna().unique().tolist()
    selected_city = st.selectbox("\U0001F4CD Filter by City:", ["All"] + sorted(available_cities))

    available_skills = sorted(set(
        skill.strip() for skills in df["Skills"] if skills != "N/A"
        for skill in skills.split(",")
    ))
    selected_skill = st.selectbox("\U0001F6E0 Filter by Skill:", ["All"] + available_skills)

    filtered_df = df.copy()
    if selected_city != "All":
        filtered_df = filtered_df[filtered_df["Location"] == selected_city]
    if selected_skill != "All":
        filtered_df = filtered_df[filtered_df["Skills"].str.contains(selected_skill)]

    st.success(f"Showing {len(filtered_df)} jobs after filtering.")
    st.markdown("### \U0001F4CB Filtered Job Listings")
    st.write(filtered_df.to_markdown(index=False), unsafe_allow_html=True)

    st.markdown("## \U0001F4CA Job Market Insights")
    if not filtered_df.empty:
        top_cities = filtered_df["Location"].value_counts().head(10)
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_cities.values, y=top_cities.index, ax=ax1, palette="coolwarm")
        ax1.set_title("Top Job Locations")
        st.pyplot(fig1)

        top_titles = filtered_df["Job Title"].value_counts().head(10)
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_titles.values, y=top_titles.index, ax=ax2, palette="viridis")
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

        st.markdown("## \U0001F52E Job Forecast (Next 7 Days)")
        prophet_df = trend_df.rename(columns={"Posted": "ds", "Job Count": "y"})
        model = Prophet()
        model.fit(prophet_df)
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)
        fig5 = model.plot(forecast)
        st.pyplot(fig5)
    else:
        st.warning("No data available after filtering.")