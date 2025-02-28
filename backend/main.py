from fastapi import FastAPI, UploadFile, File, HTTPException
import os
from openai import OpenAI
import spacy
from docx import Document
import pdfplumber
from io import BytesIO
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import cosine
from collections import Counter

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Initialize OpenAI client with the API key
client = OpenAI(
    api_key=os.environ.get('OPENAI_API_KEY'),  # Uses the environment variable for the API key
)

# Initialize SpaCy model
nlp = spacy.load("en_core_web_sm")

app = FastAPI()

def extract_text_from_pdf(pdf_bytes):
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        if not text:
            raise HTTPException(status_code=400, detail="No text found in PDF. Ensure it's not an image-based PDF.")
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

def extract_text_from_word(word_bytes):
    try:
        doc = Document(BytesIO(word_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
        if not text:
            raise HTTPException(status_code=400, detail="No text found in Word file.")
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing Word file: {str(e)}")

# Preprocess text: Tokenization, lemmatization, and stopword removal
def preprocess_text(text: str):
    doc = nlp(text)
    processed_text = " ".join([token.lemma_ for token in doc if not token.is_stop and not token.is_punct])
    return processed_text

# Compute similarity based on cosine distance
def compute_similarity(text1: str, text2: str):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])

    # Convert the sparse matrix to a dense format, then flatten it to 1D
    vector1 = tfidf_matrix[0].toarray().flatten()
    vector2 = tfidf_matrix[1].toarray().flatten()

    # Now compute cosine similarity
    cosine_sim = 1 - cosine(vector1, vector2)  # 1 - cosine distance gives cosine similarity
    return cosine_sim


# Calculate individual scores based on different criteria
def calculate_scores(resume_text: str, job_description_text: str):
    # Preprocess the resume and job description
    resume_processed = preprocess_text(resume_text)
    job_description_processed = preprocess_text(job_description_text)

    # Calculate similarity for skills (keyword matching, TF-IDF, or embeddings)
    skills_score = compute_similarity(resume_processed, job_description_processed) * 10  # Scale to 0-10

    # Impact score based on quantifiable achievements (e.g., numbers, percentages)
    impact_score = 0
    for word in resume_processed.split():
        if word.isdigit():  # Looking for numbers (e.g., "20%", "500 projects")
            impact_score += 1  # Simple rule: increment score for each number found
    impact_score = min(impact_score, 10)  # Cap the score at 10

    # Brevity score based on word count (smaller resume length can be more concise)
    brevity_score = 10 - len(resume_processed.split()) // 50  # Simple rule: fewer words, higher brevity score

    # Style score (using tone and readability check - basic example based on stopwords count)
    style_score = 10 - len([word for word in resume_processed.split() if word in nlp.Defaults.stop_words]) // 10

    # Average score
    average_score = (impact_score + brevity_score + style_score + skills_score) / 4
    return {
        "impact": impact_score,
        "brevity": brevity_score,
        "style": style_score,
        "skills": skills_score,
        "average": average_score
    }

# Generate feedback with specific suggestions for improvement
def generate_feedback(resume_text: str, job_description_text: str):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional resume reviewer."},
            {"role": "user", "content": f"Review this resume against the job description and provide suggestions for improvement. Resume: {resume_text} Job Description: {job_description_text}"}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

@app.post("/analyze_resume/")
async def analyze_resume(resume_file: UploadFile = File(...), job_description_file: UploadFile = File(...)):
    if not resume_file or not job_description_file:
        raise HTTPException(status_code=400, detail="Both resume and job description must be uploaded.")

    resume_extension = resume_file.filename.split(".")[-1].lower()
    job_description_extension = job_description_file.filename.split(".")[-1].lower()

    resume_bytes = await resume_file.read()
    job_description_bytes = await job_description_file.read()

    if resume_extension == "pdf":
        resume_text = extract_text_from_pdf(resume_bytes)
    elif resume_extension == "docx":
        resume_text = extract_text_from_word(resume_bytes)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type for resume. Only PDF and Word (.docx) are allowed.")

    if job_description_extension == "pdf":
        job_description_text = extract_text_from_pdf(job_description_bytes)
    elif job_description_extension == "docx":
        job_description_text = extract_text_from_word(job_description_bytes)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type for job description. Only PDF and Word (.docx) are allowed.")

    # Calculate individual scores and average score based on resume and job description
    scores = calculate_scores(resume_text, job_description_text)

    # Generate AI feedback for the resume
    feedback = generate_feedback(resume_text, job_description_text)

    return {
        "scores": scores,
        "feedback": feedback
    }

