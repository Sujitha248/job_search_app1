import streamlit as st
import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ------------------- App Config -------------------
st.set_page_config(page_title="Resume Analyzer & Job Role Recommender", layout="wide")
st.title("📄 Resume Analyzer + 🔍 Job Role Recommender")

# ------------------- Load ESCO Dataset -------------------
@st.cache_data
def load_occupations(path):
    try:
        df = pd.read_csv(path)
        df = df[['preferredLabel', 'description']]
        df = df.dropna()
        df = df.drop_duplicates()
        df.rename(columns={'preferredLabel': 'Job Title', 'description': 'Description'}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Failed to load ESCO data: {e}")
        return pd.DataFrame()

esco_path = os.path.join("ESCO_dataset","occupation_en.csv")
occupations_df = load_occupations(esco_path)

# ------------------- Resume Input -------------------
st.markdown("### ✨ Paste Your Resume or Skills Below")
resume_text = st.text_area("Paste your resume content here:", height=250)

# ------------------- Role Matching Function -------------------
def recommend_roles(resume_text, job_df, top_n=5):
    if resume_text.strip() == "":
        return pd.DataFrame()

    docs = job_df['Description'].tolist()
    docs.insert(0, resume_text)  # First item is resume

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(docs)
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])

    job_df['Similarity Score'] = cosine_sim[0]
    recommended = job_df.sort_values(by='Similarity Score', ascending=False).head(top_n)
    return recommended

# ------------------- Show Recommendations -------------------
if st.button("🔍 Analyze & Recommend Roles"):
    with st.spinner("Analyzing your resume..."):
        results = recommend_roles(resume_text, occupations_df, top_n=10)
        if not results.empty:
            st.success("✅ Recommended Roles Based on Your Resume")
            st.dataframe(results[['Job Title', 'Description', 'Similarity Score']])
        else:
            st.warning("😕 No results found. Please paste valid resume content.")

# ------------------- Footer -------------------
st.markdown("---")
st.caption("Built using ESCO job classification dataset | Developed in Streamlit 🔥")