import streamlit as st
import pandas as pd
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns

# ----------------- App Config -----------------
st.set_page_config(page_title="Resume Analyzer + Role Recommender", layout="wide")
st.title("📄 Resume Analyzer & Role Recommender")

# ----------------- Load ESCO Dataset -----------------
@st.cache_data
def load_data():
    occ_df = pd.read_csv("ESCO_dataset/occupations_en.csv")
    sk_df = pd.read_csv("ESCO_dataset/skills_en.csv")
    rel_df = pd.read_csv("ESCO_dataset/occupationSkillRelations_en.csv")
    return occ_df, sk_df, rel_df

occupations_df, skills_df, relations_df = load_data()

# ----------------- Resume Upload -----------------
st.markdown("### 📤 Upload your Resume (Text Format)")
resume_text = st.text_area("Paste Resume Text Here:", height=250)

if resume_text:
    # Preprocess resume
    def preprocess(text):
        text = re.sub(r"[^a-zA-Z0-9 ]", "", text)
        return text.lower()

    clean_resume = preprocess(resume_text)

    # Match with occupations
    tfidf = TfidfVectorizer(stop_words='english')
    occ_vectors = tfidf.fit_transform(occupations_df['preferredLabel'].astype(str))
    resume_vec = tfidf.transform([clean_resume])
    similarity = cosine_similarity(resume_vec, occ_vectors).flatten()
    occupations_df['Similarity'] = similarity
    top_matches = occupations_df.sort_values(by='Similarity', ascending=False).head(10)

    st.markdown("### 🎯 Top Recommended Job Roles")
    st.dataframe(top_matches[['preferredLabel', 'description', 'Similarity']].rename(columns={
        'preferredLabel': 'Job Title',
        'description': 'Job Description'
    }))

    # ----------------- Skill Highlight -----------------
    matched_skills = set()
    resume_words = clean_resume.split()
    for skill in skills_df['preferredLabel'].dropna().unique():
        if any(word in skill.lower() for word in resume_words):
            matched_skills.add(skill)

    st.markdown("### ✅ Skills Found in Resume")
    if matched_skills:
        st.write(", ".join(matched_skills))
    else:
        st.warning("No matching skills found.")

    # ----------------- Skill Gap Analysis -----------------
    st.markdown("### ❌ Missing Recommended Skills")
    recommended_skills = set()
    for occ in top_matches['conceptUri']:
        skills_for_occ = relations_df[relations_df['originUri'] == occ]
        skill_names = skills_df[skills_df['conceptUri'].isin(skills_for_occ['targetUri'])]['preferredLabel'].tolist()
        recommended_skills.update(skill_names)

    missing_skills = recommended_skills - matched_skills
    if missing_skills:
        st.error(", ".join(missing_skills))

    # ----------------- Course Suggestions -----------------
    st.markdown("### 📚 Suggested Courses for Missing Skills")
    for skill in list(missing_skills)[:5]:
        st.markdown(f"- [Learn {skill} on Coursera](https://www.coursera.org/search?query={skill})")

    # ----------------- Skill Frequency Chart -----------------
    st.markdown("### 📊 Skill Frequency Chart in Resume")
    resume_skill_counts = {s: resume_text.lower().count(s.lower()) for s in matched_skills}
    skill_df = pd.DataFrame(list(resume_skill_counts.items()), columns=['Skill', 'Frequency']).sort_values(by='Frequency', ascending=False)
    if not skill_df.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(data=skill_df, x='Frequency', y='Skill', ax=ax, palette='viridis')
        ax.set_title("Skill Mentions in Resume")
        st.pyplot(fig)

    # ----------------- ChatGPT Resume Tips -----------------
    st.markdown("### 🤖 AI Resume Tips")
    st.info("✅ Tip: Use action verbs like 'Developed', 'Implemented', 'Led', etc.")
    st.info("✅ Tip: Quantify your achievements (e.g., 'Increased sales by 20%').")
    st.info("✅ Tip: Tailor your resume for each job role.")

    # ----------------- Project Suggestions -----------------
    st.markdown("### 💡 Suggested Projects to Add")
    if 'data' in clean_resume:
        st.write("- Build a real-time dashboard using Streamlit")
        st.write("- Predict stock prices using ML")
    if 'web' in clean_resume:
        st.write("- Create a portfolio website using HTML/CSS/JS")
        st.write("- Develop a RESTful API using Flask")

    # ----------------- Industry Tagging -----------------
    st.markdown("### 🏢 Suggested Industries")
    industry_tags = []
    if 'python' in clean_resume:
        industry_tags.append('Software / IT')
    if 'data' in clean_resume:
        industry_tags.append('Analytics / Research')
    if 'marketing' in clean_resume:
        industry_tags.append('Marketing / Digital')
    if industry_tags:
        st.success(", ".join(set(industry_tags)))
    else:
        st.info("Couldn't detect specific industry. Try adding more domain-specific keywords.")