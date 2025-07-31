import streamlit as st
import pandas as pd
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
import PyPDF2
from io import StringIO
from wordcloud import WordCloud

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
st.markdown("### 📤 Upload Your Resume")
uploaded_file = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])

resume_text = ""

if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            resume_text += page.extract_text()
    elif uploaded_file.type == "text/plain":
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        resume_text = stringio.read()

# Optional manual text input
st.markdown("### ✏ Or Paste Your Resume Text")
resume_input = st.text_area("Paste Resume Text:", height=250)
if resume_input:
    resume_text = resume_input

if resume_text:
    # ----------------- Preprocess -----------------
    def preprocess(text):
        text = re.sub(r"[^a-zA-Z0-9 ]", "", text)
        return text.lower()

    clean_resume = preprocess(resume_text)

    # ----------------- Role Recommendation -----------------
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

    # ----------------- Skill Matching -----------------
    matched_skills = set()
    resume_words = set(clean_resume.split())

    for skill in skills_df['preferredLabel'].dropna().unique():
        skill_words = set(skill.lower().split())
        if resume_words & skill_words:
            matched_skills.add(skill)

    st.markdown("### ✅ Skills Found in Resume")
    if matched_skills:
        st.success(", ".join(sorted(matched_skills)))
    else:
        st.warning("No matching skills found.")

    # ----------------- Skill Gap Analysis -----------------
    st.markdown("### ❌ Missing Recommended Skills")
    recommended_skills = set()
    for occ in top_matches['conceptUri']:
        skill_links = relations_df[relations_df['occupationUri'] == occ]
        skill_uris = skill_links['skillUri'].unique()
        skills_for_occ = skills_df[skills_df['conceptUri'].isin(skill_uris)]
        recommended_skills.update(skills_for_occ['preferredLabel'].dropna().tolist())

    missing_skills = recommended_skills - matched_skills
    if missing_skills:
        st.error(", ".join(sorted(missing_skills)))
    else:
        st.success("Great! You seem to have the recommended skills.")

    # ----------------- Course Suggestions -----------------
    st.markdown("### 📚 Suggested Courses for Missing Skills")
    for skill in list(missing_skills)[:5]:
        st.markdown(f"- [Learn {skill} on Coursera](https://www.coursera.org/search?query={skill})")

    # ----------------- Skill Frequency Chart -----------------
    st.markdown("### 📊 Skill Frequency Chart")
    resume_skill_counts = {s: resume_text.lower().count(s.lower()) for s in matched_skills}
    skill_df = pd.DataFrame(list(resume_skill_counts.items()), columns=['Skill', 'Frequency']).sort_values(by='Frequency', ascending=False)

    if not skill_df.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(data=skill_df, x='Frequency', y='Skill', ax=ax, palette='magma')
        ax.set_title("Skill Mentions in Resume")
        st.pyplot(fig)

    # ----------------- Word Cloud -----------------
    st.markdown("### ☁ Resume Word Cloud")
    wordcloud = WordCloud(width=800, height=300, background_color="white").generate(clean_resume)
    fig_wc, ax_wc = plt.subplots(figsize=(10, 4))
    ax_wc.imshow(wordcloud, interpolation="bilinear")
    ax_wc.axis("off")
    st.pyplot(fig_wc)

    # ----------------- Resume Tips -----------------
    st.markdown("### 🤖 Resume Writing Tips")
    st.info("✅ Use strong action verbs like 'Designed', 'Implemented', 'Optimized'.")
    st.info("✅ Highlight quantifiable achievements: 'Improved performance by 25%'.")
    st.info("✅ Customize your resume to match the job you're applying for.")

    # ----------------- Industry Tags -----------------
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
        st.info("Add more domain-specific terms to get industry suggestions.")
else:
    st.info("Please upload or paste your resume to get started.")