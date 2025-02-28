from fastapi import FastAPI, UploadFile, File, HTTPException
import os
import re
from openai import OpenAI
import spacy
from docx import Document
import pdfplumber
from io import BytesIO
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import cosine
from collections import Counter
import re
import textstat  # For readability metrics

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Initialize OpenAI client with the API key
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Initialize SpaCy model
nlp = spacy.load("en_core_web_sm")

app = FastAPI()

def extract_text_from_pdf(pdf_bytes):
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        if not text:
            raise HTTPException(status_code=400, detail="No text found in PDF.")
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

import re
from fastapi import HTTPException

# Function to generate scores and feedback using ChatGPT
def generate_scores_and_feedback(resume_text: str, job_description_text: str):
    # Create a prompt to ask ChatGPT to evaluate the resume and job description with a fixed format
    prompt = f"""
    Please evaluate the following resume against this job description and provide scores and feedback for the following categories:
    1. Skills: Based on how well the resume matches the skills required by the job description.
    2. Impact: Based on the quantifiable achievements and contributions in the resume.
    3. Brevity: Based on how concise and relevant the resume is to the job description.
    4. Style: Based on the readability, clarity, and tone of the resume.

    Here is the resume:
    {resume_text}

    Here is the job description:
    {job_description_text}

    Please follow this format exactly for your response:
    ---
    Skills: [score out of 10]
    Feedback: [detailed feedback about skills]

    Impact: [score out of 10]
    Feedback: [detailed feedback about impact]

    Brevity: [score out of 10]
    Feedback: [detailed feedback about brevity]

    Style: [score out of 10]
    Feedback: [detailed feedback about style]
    ---
    Provide only the scores and feedback in the format above, no additional text.
    """

    # Make the ChatGPT API call to generate the scores and feedback
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional resume reviewer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000  # Increased token limit to get detailed feedback
    )

    # Parse the response from ChatGPT
    result = response.choices[0].message.content.strip()

    # Log the response for debugging purposes
    print("ChatGPT Response:", result)

    # Use regex to find all instances of scores and feedback for each category
    categories = ["Skills", "Impact", "Brevity", "Style"]
    pattern = r"(\w+): (\d+)\s*Feedback: (.+?)(?=\n\w+:|\Z)"

    try:
        # Find all matches for categories, scores, and feedback
        matches = re.findall(pattern, result, re.DOTALL)

        if len(matches) != 4:
            raise HTTPException(status_code=500, detail="ChatGPT response format is incorrect. Expected 4 categories with score and feedback.")

        scores_and_feedback = {}

        # Process the matches
        for match in matches:
            category, score_str, feedback = match
            if category not in categories:
                continue  # Skip if category is not recognized

            # Convert the score to a float
            try:
                score = float(score_str)
            except ValueError:
                continue  # Skip if score cannot be converted to float

            # Store the score and feedback in the dictionary
            scores_and_feedback[category] = {"score": score, "feedback": feedback.strip()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing ChatGPT response: {str(e)}")

    return scores_and_feedback





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

    # Get ChatGPT-generated scores and feedback
    scores_and_feedback = generate_scores_and_feedback(resume_text, job_description_text)

    return {
        "scores_and_feedback": scores_and_feedback
    }

@app.post("/generate_cover_letter/")
async def generate_cover_letter(resume_file: UploadFile = File(...), job_description_file: UploadFile = File(...)):
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

    # Create a prompt to generate the cover letter using ChatGPT
    prompt = f"""
    Based on the following resume and job description, generate a professional cover letter addressed to the hiring manager for the position. 

    Resume:
    {resume_text}

    Job Description:
    {job_description_text}

    The cover letter should:
    - Be professional, concise, and respectful.
    - Mention key qualifications from the resume that align with the job requirements.
    - Express enthusiasm for the position and the company.
    - Be addressed to the hiring manager.

    Please format the cover letter appropriately with a greeting, introduction, body, and conclusion.
    """

    # Make the ChatGPT API call to generate the cover letter
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional cover letter generator."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000  # Increased token limit to get detailed cover letter
    )

    # Parse the response from ChatGPT
    result = response.choices[0].message.content.strip()

    return {
        "cover_letter": result
    }