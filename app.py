import streamlit as st
import google.generativeai as genai
import os
import re
import io
from dotenv import load_dotenv

# PDF handling
import pdfplumber
import PyPDF2

load_dotenv()

# -----------------------------
# CONFIG
# -----------------------------
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ GEMINI_API_KEY not found in .env file")
    st.stop()

genai.configure(api_key=API_KEY)

# Auto-select a Gemini text model
models = genai.list_models()
text_models = [m.name for m in models if "gemini" in m.name.lower()]

if not text_models:
    st.error("No Gemini text-generation models available for your API key.")
    st.stop()

model_name = text_models[0]  # pick the first available
st.info(f"Using Gemini model: {model_name}")
model = genai.GenerativeModel(model_name)

# -----------------------------
# STREAMLIT PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Fast AI Quiz Generator (Gemini)", layout="wide")
st.title("⚡ Fast AI Quiz Generator (Gemini Version)")

# -----------------------------
# UTILS
# -----------------------------
def extract_text_from_file(uploaded_file):
    """Extract text from PDF or TXT"""
    try:
        if uploaded_file.name.lower().endswith(".pdf"):
            try:
                with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
                    pages = [p.extract_text() or "" for p in pdf.pages]
                    return "\n".join(pages)
            except:
                reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                pages = [p.extract_text() or "" for p in reader.pages]
                return "\n".join(pages)
        else:
            raw = uploaded_file.getvalue()
            if isinstance(raw, bytes):
                return raw.decode("utf-8", errors="ignore")
            return str(raw)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return ""

def generate_summary(text, max_sentences=5):
    """Simple extractive summary"""
    sentences = re.split(r'(?<=[.!?]) +', text)
    return " ".join(sentences[:max_sentences])

def extract_keywords(text, max_keywords=8):
    text = re.sub(r"[^a-zA-Z0-9 ]", " ", text.lower())
    words = text.split()

    stopwords = {
        "the","is","and","in","of","to","a","on","for","as","by","with","an",
        "it","this","that","are","be","or","from","at","was","were","you","your"
    }

    freq = {}
    for w in words:
        if w not in stopwords and len(w) > 3:
            freq[w] = freq.get(w, 0) + 1

    keywords = sorted(freq, key=freq.get, reverse=True)
    return keywords[:max_keywords]

def has_enough_context(text, min_length=300):
    """Check if text contains enough content for direct question generation."""
    return len(text.strip()) >= min_length

# -----------------------------
# QUESTION GENERATION USING GEMINI
# -----------------------------
def generate_questions(prompt, n=5, difficulty="easy"):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating questions: {str(e)}"

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.subheader("Upload your study material or paste text")
uploaded_file = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])
text_input = st.text_area("Or paste text here...", height=200)

text_data = ""
if uploaded_file:
    text_data = extract_text_from_file(uploaded_file)
elif text_input.strip():
    text_data = text_input.strip()

if text_data:
    st.subheader("Summary")
    summary = generate_summary(text_data)
    st.write(summary)

    st.subheader("Quiz Settings")
    num_questions = st.slider("Questions per topic", 1, 15, 5)
    difficulty = st.selectbox("Difficulty level", ["easy", "medium", "hard"])

    if st.button("Generate Quiz ⚡"):

        st.subheader("Generated Quiz")

        # --------------------------
        # DECISION: Enough context?
        # --------------------------
        if has_enough_context(text_data):
            st.info("📘 Context detected — generating questions directly from the document.")

            prompt = f"""
Use ONLY the content below to generate {num_questions} MCQs:

{text_data}

Difficulty: {difficulty}

Requirements:
- Each question must be based ONLY on the provided text
- Use 4 options (A-D)
- Provide the correct answer at the end
"""
            with st.spinner("Generating MCQs from the document context..."):
                quiz = generate_questions(prompt, num_questions, difficulty)

            st.markdown(quiz)
            full_quiz_text = quiz

        else:
            st.warning("⚠ Not enough context found — generating questions using extracted keywords.")

            with st.spinner("Extracting keywords..."):
                keywords = extract_keywords(text_data)
            st.success(f"Keywords found: {', '.join(keywords)}")

            combined_topic = ", ".join(keywords)

            prompt = f"""
Generate {num_questions} multiple-choice questions on:
{combined_topic}

Difficulty: {difficulty}

Requirements:
- 4 options per question (A–D)
- Mention correct answer at the end
"""
            with st.spinner("Generating questions using keywords..."):
                quiz = generate_questions(prompt, num_questions, difficulty)

            st.markdown(f"### Topics: {combined_topic}")
            st.markdown(quiz)
            full_quiz_text = quiz

        # Download file
        st.download_button(
            "Download Quiz File",
            data=full_quiz_text,
            file_name="quiz.txt",
            mime="text/plain"
        )

else:
    st.info("Paste some text or upload a PDF/TXT to generate summary and quiz.")
