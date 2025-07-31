import streamlit as st
import pandas as pd
import os
import difflib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ------------------ Setup ------------------
st.set_page_config(page_title="Resume Analyzer & Role Recommender", layout="wide")
st.title("📄 Resume Analyzer & Job Role Recommender")

# ------------------ Load ESCO Dataset ------------------
@st.cache_data
def load_esco_data():
    try:
        dataset_path = os.path.join(os.getcwd(), "ESCO_dataset","occupations_en.csv")
        df = pd.read_csv(dataset_path)
        df = df[['preferredLabel', 'description', 'code']]
        df.dropna(subset=["preferredLabel", "description"], inplace=True)
        return df
    except Exception as e:
        st.error(f"Error loading ESCO dataset: {e}")
        return pd.DataFrame()

esco_df = load_esco_data()

# ------------------ Input Resume ------------------
st.markdown("## 📝 Upload or Paste Your Resume")

upload_option = st.radio("Choose input method:", ("Upload .txt file", "Paste text manually"))

resume_text = ""
if upload_option == "Upload .txt file":
    uploaded_file = st.file_uploader("Upload your resume (.txt only):", type=["txt"])
    if uploaded_file:
        resume_text = uploaded_file.read().decode("utf-8")
else:
    resume_text = st.text_area("Paste your resume here:")

# ------------------ Matching & Recommendation ------------------
def recommend_roles(resume, esco_df, top_n=5):
    tfidf = TfidfVectorizer(stop_words="english")
    esco_texts = esco_df["preferredLabel"] + " " + esco_df["description"]
    tfidf_matrix = tfidf.fit_transform(esco_texts)
    resume_vec = tfidf.transform([resume])

    similarity = cosine_similarity(resume_vec, tfidf_matrix).flatten()
    top_indices = similarity.argsort()[-top_n:][::-1]

    results = []
    for idx in top_indices:
        role = esco_df.iloc[idx]
        overlap = set(resume.lower().split()) & set(role["description"].lower().split())
        results.append({
            "Job Title": role["preferredLabel"],
            "ESCO Code": role["code"],
            "Similarity Score (%)": round(similarity[idx] * 100, 2),
            "Matching Keywords": ", ".join(list(overlap)[:10]),
            "Description": role["description"]
        })
    return results

# ------------------ Display Recommendations ------------------
if resume_text and not esco_df.empty:
    with st.spinner("Analyzing your resume..."):
        recommendations = recommend_roles(resume_text, esco_df)

    st.success("✅ Here are the top job roles for your resume:")
    for rec in recommendations:
        st.markdown(f"### 🔹 {rec['Job Title']} (ESCO Code: {rec['ESCO Code']})")
        st.markdown(f"*Similarity Score*: {rec['Similarity Score (%)']}%")
        st.markdown(f"*Matching Keywords*: {rec['Matching Keywords'] or 'N/A'}")
        st.markdown(f"*Description*: {rec['Description']}")
        st.markdown("---")
elif resume_text:
    st.warning("ESCO dataset not loaded correctly.")