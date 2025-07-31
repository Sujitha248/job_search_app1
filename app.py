import streamlit as st
import pandas as pd
import os
import re
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from wordcloud import WordCloud
import PyPDF2
import nltk
nltk.download('punkt')

# ----------------- App Config -----------------
st.set_page_config(page_title="Resume Analyzer + Role Recommender", layout="wide")
st.title("📄 Resume Analyzer & Role Recommender")

# ----------------- Load ESCO Dataset -----------------
@st.cache_data
def load_data():
    occ_df = pd.read_csv("ESCO_dataset/occupations_en.csv")
    sk_df = pd.read_csv("ESCO_dataset/skills_en.csv")
    rel_df = pd.read_csv("ESCO_dataset/occupationSkillRelations.csv")
    return occ_df, sk_df, rel_df

occupations_df, skills_df, relations_df = load_data()

# ----------------- Upload Resume -----------------
st.markdown("### 📤 Upload Your Resume (.txt or .pdf)")
uploaded_file = st.file_uploader("Upload File", type=["txt", "pdf"])

resume_text = ""
if uploaded_file:
    if uploaded_file.type == "application/pdf":
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            resume_text += page.extract_text()
    else:
        resume_text = uploaded_file.read().decode("utf-8")

if resume_text:
    # ----------------- Preprocess Resume -----------------
    def preprocess(text):
        text = re.sub(r"[^a-zA-Z0-9 ]", " ", text)
        return text.lower()

    clean_resume = preprocess(resume_text)

    # ----------------- Role Recommendation -----------------
    tfidf = TfidfVectorizer(stop_words='english')
    occ_vectors = tfidf.fit_transform(occupations_df['preferredLabel'].astype(str))
    resume_vec = tfidf.transform([clean_resume])
    similarity = cosine_similarity(resume_vec, occ_vectors).flatten()
    occupations_df['Similarity'] = similarity
    top_roles = occupations_df.sort_values(by='Similarity', ascending=False).head(5)

    st.markdown("### 🎯 Top Recommended Job Roles")
    st.table(top_roles[['preferredLabel', 'description']].rename(columns={
        'preferredLabel': 'Job Title',
        'description': 'Job Description'
    }))

    # ----------------- Skills in Resume -----------------
    resume_tokens = set(clean_resume.split())
    matched_skills = {
        skill for skill in skills_df['preferredLabel'].dropna().unique()
        if any(word in skill.lower() for word in resume_tokens)
    }

    st.markdown("### ✅ Skills Found in Resume")
    if matched_skills:
        st.success(", ".join(sorted(matched_skills)))
    else:
        st.warning("No matching skills found.")

    # ----------------- Skill Gap Analysis -----------------
    recommended_skills = set()
    for uri in top_roles['conceptUri']:
        related_skills = relations_df[relations_df['occupationUri'] == uri]['skillUri']
        skill_names = skills_df[skills_df['conceptUri'].isin(related_skills)]['preferredLabel'].tolist()
        recommended_skills.update(skill_names)

    missing_skills = recommended_skills - matched_skills
    st.markdown("### ❌ Missing Recommended Skills")
    if missing_skills:
        st.error(", ".join(sorted(missing_skills)))
    else:
        st.success("You have all the recommended skills!")

    # ----------------- Course Suggestions -----------------
    st.markdown("### 📚 Course Suggestions for Missing Skills")
    for skill in list(missing_skills)[:5]:
        st.markdown(f"- [Learn {skill} on Coursera](https://www.coursera.org/search?query={skill})")

    # ----------------- Skill Frequency Chart -----------------
    st.markdown("### 📊 Skill Frequency in Resume")
    skill_counts = {s: resume_text.lower().count(s.lower()) for s in matched_skills}
    if skill_counts:
        df_freq = pd.DataFrame(list(skill_counts.items()), columns=["Skill", "Frequency"]).sort_values(by="Frequency", ascending=False)
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(data=df_freq, x="Frequency", y="Skill", palette="viridis", ax=ax)
        ax.set_title("Skill Frequency")
        st.pyplot(fig)

    # ----------------- Resume Word Cloud -----------------
    st.markdown("### ☁ Resume Word Cloud")
    wordcloud = WordCloud(width=800, height=300, background_color='white').generate(clean_resume)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)

    # ----------------- Suggested Industry -----------------
    st.markdown("### 🏢 Suggested Industry Tags")
    tags = []
    if 'python' in clean_resume: tags.append("Software / IT")
    if 'machine learning' in clean_resume or 'data' in clean_resume: tags.append("Data Science / AI")
    if 'marketing' in clean_resume: tags.append("Marketing / Digital")
    if tags:
        st.success("Industry Tags: " + ", ".join(tags))
    else:
        st.info("Try including domain-specific keywords for better industry suggestion.")