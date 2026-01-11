import streamlit as st
import google.generativeai as genai
import os
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

def get_gemini_model():
    models = genai.list_models()
    text_models = [m.name for m in models if "gemini" in m.name.lower()]
    if not text_models:
        st.error("No Gemini text-generation models available for your API key.")
        st.stop()
    model_name = text_models[0]
    st.info(f"Using Gemini model: {model_name}")
    return genai.GenerativeModel(model_name)

model = get_gemini_model()

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
    sentences = text.split('. ')
    return ". ".join(sentences[:max_sentences])

def extract_keywords(text, max_keywords=8):
    import re
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
    return len(text.strip()) >= min_length

def generate_csv_quiz(prompt):
    """Generate quiz CSV directly using Gemini"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating questions: {str(e)}"

# -----------------------------
# STREAMLIT UI
# -----------------------------
def main():
    st.set_page_config(page_title="Fast AI Quiz Generator (Gemini)", layout="wide")
    st.title("⚡ Fast AI Quiz Generator (Gemini Version)")

    st.subheader("Upload your study material or paste text")
    uploaded_file = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])
    text_input = st.text_area("Or paste text here...", height=200)

    text_data = ""
    if uploaded_file:
        text_data = extract_text_from_file(uploaded_file)
    elif text_input.strip():
        text_data = text_input.strip()

    if not text_data:
        st.info("Paste some text or upload a PDF/TXT to generate summary and quiz.")
        return

    # Show summary
    st.subheader("Summary")
    summary = generate_summary(text_data)
    st.write(summary)

    # Quiz settings
    st.subheader("Quiz Settings")
    num_questions = st.slider("Questions per topic", 1, 15, 5)
    difficulty = st.selectbox("Difficulty level", ["easy", "medium", "hard"])

    if st.button("Generate Quiz ⚡"):
        st.subheader("Generated Quiz (CSV format)")

        if has_enough_context(text_data):
            st.info("📘 Context detected — generating questions from the document.")
            content_source = text_data
        else:
            st.warning("⚠ Not enough context — generating questions using keywords.")
            keywords = extract_keywords(text_data)
            st.success(f"Keywords found: {', '.join(keywords)}")
            content_source = ", ".join(keywords)

        # Gemini prompt for CSV output
        prompt = f"""
Generate {num_questions} multiple-choice questions in CSV format with columns:
question_num,question,option_a,option_b,option_c,option_d,correct_option

Use ONLY the following content for question generation:
{content_source}

Difficulty: {difficulty}

Requirements:
- 4 options per question (A, B, C, D)
- correct_option must be A, B, C, or D
- Provide exactly {num_questions} questions
- Output the CSV text exactly as it should appear in the file
"""
        with st.spinner("Generating CSV quiz..."):
            csv_quiz = generate_csv_quiz(prompt)

        # Show raw CSV
        st.text_area("CSV Output Preview", csv_quiz, height=300)

        # Download CSV file
        st.download_button(
            "Download Quiz CSV",
            data=csv_quiz,
            file_name="quiz.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
