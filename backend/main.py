from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

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

def generate_ideal_resume(resume_text: str, job_description_text: str):
    # Create a prompt to ask ChatGPT to generate an ideal resume with strictly structured output
    prompt = f"""
    I need help enhancing a resume to better match a job description.

    Here is the original resume:
    {resume_text}

    Here is the job description:
    {job_description_text}

    Please provide me with specific, actionable recommendations to improve this resume for this job.
    You MUST follow this EXACT structured format in your response:

    ## Skills Alignment
    • [Specific skill from job description 1]
    • [Specific skill from job description 2]
    • [Additional skills to highlight or add]

    ## Experience Reframing
    • [Suggested improvement for experience bullet point 1]
    • [Suggested improvement for experience bullet point 2]
    • [Ways to better quantify achievements]

    ## Content Organization
    • [Recommendation for section reorganization 1]
    • [Recommendation for section reorganization 2]
    • [Sections to emphasize or de-emphasize]

    ## Key Terminology
    • [Industry term 1 from job description to include]
    • [Industry term 2 from job description to include]
    • [Buzzwords that should be incorporated]

    ## Format and Presentation
    • [Suggestion for layout improvement 1]
    • [Suggestion for readability improvement 1]
    • [Visual enhancement recommendation]

    For each recommendation, provide specific, concrete examples and clear, actionable advice.
    Each bullet point should be a complete thought and recommendation.
    Always begin each section with the exact heading as shown above (e.g., "## Skills Alignment").
    """

    # Make the ChatGPT API call to generate the ideal resume
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional resume writer with expertise in optimizing resumes for specific job descriptions. You MUST format your response with the exact section headings specified and use bullet points for all recommendations."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500
    )

    # Parse the response from ChatGPT
    result = response.choices[0].message.content.strip()
    return result

def generate_skill_development_plan(resume_text: str, job_description_text: str):
    # Create a prompt to generate skill development suggestions with strictly structured output
    prompt = f"""
    Based on the following resume and job description, provide a detailed skill development plan to help the candidate become more competitive for this position.

    Resume:
    {resume_text}

    Job Description:
    {job_description_text}

    Please create a structured skill development plan using this EXACT format with the specified section headers:

    ## Skill Gaps Analysis
    • [Skill 1]: (High) - [Brief description of gap]
    • [Skill 2]: (Medium) - [Brief description of gap]
    • [Skill 3]: (Low) - [Brief description of gap]
    
    ## Learning Resources
    • For [Skill 1]: [Specific course/certification name] on [Platform] - [Brief description]
    • For [Skill 2]: [Book/resource title] - [Brief description]
    • For [Skill 3]: [Learning resource] - [Brief description]
    
    ## Practical Experience
    • Project 1: [Descriptive project name] - [Brief description and skills addressed]
    • Project 2: [Descriptive project name] - [Brief description and skills addressed]
    • Activity: [Specific activity] - [Brief description and skills addressed]
    
    ## Timeline
    • Short-term (1-3 months): [Skills to focus on first with specific actions]
    • Medium-term (3-6 months): [Skills to develop next with specific actions]
    • Long-term (6+ months): [Skills that require more time with specific actions]
    
    ## Demonstrating Progress
    • Resume Updates: [Specific suggestions for resume modifications]
    • Portfolio Additions: [Specific items to add to portfolio]
    • Interview Talking Points: [Key points to emphasize during interviews]

    Always use bullet points for each recommendation.
    Always begin each section with the exact heading format shown above (e.g., "## Skill Gaps Analysis").
    For skills in the Skill Gaps Analysis section, always include priority level as (High), (Medium), or (Low).
    """

    # Make the ChatGPT API call
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a career development coach specializing in skill gap analysis and professional development planning. You MUST format your response with the exact section headings specified and use bullet points for all recommendations."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500
    )

    # Parse the response from ChatGPT
    result = response.choices[0].message.content.strip()
    return result

def generate_comprehensive_analysis(resume_text: str, job_description_text: str):
    """
    Make a single API call to OpenAI to generate all analysis components at once:
    - Scores and feedback
    - Cover letter
    - Resume suggestions
    - Skill development plan
    
    This function uses a structured format to ensure consistent responses that are easy to parse.
    """
    # Create a comprehensive prompt that includes all our needs with strict formatting requirements
    prompt = f"""
    I need a comprehensive analysis of a resume against a job description. You MUST provide the following outputs in EXACTLY the structured format shown below.

    Resume:
    {resume_text}

    Job Description:
    {job_description_text}

    You MUST follow this EXACT format with NO deviations:

    [SECTION:SCORES]
    Skills: [Score 1-10]
    Skills_Feedback: [Detailed feedback about skills]

    Impact: [Score 1-10]
    Impact_Feedback: [Detailed feedback about impact]

    Brevity: [Score 1-10]
    Brevity_Feedback: [Detailed feedback about brevity]

    Style: [Score 1-10]
    Style_Feedback: [Detailed feedback about style]
    [/SECTION:SCORES]

    [SECTION:COVER_LETTER]
    [Generate a professional cover letter that is specifically tailored based on the resume and job description provided. The letter must address the hiring manager, reference specific experiences from the resume that match the job requirements, and express enthusiasm for the position. Format with greeting, introduction, body paragraphs, and conclusion.]
    [/SECTION:COVER_LETTER]

    [SECTION:RESUME_SUGGESTIONS]
    [SECTION:SKILLS_TO_HIGHLIGHT]
    • [Skill 1 from the resume that matches job description]
    • [Skill 2 from the resume that matches job description]
    • [Skill 3 from the resume that matches job description]
    [/SECTION:SKILLS_TO_HIGHLIGHT]

    [SECTION:SKILLS_TO_ADD]
    • [Missing skill 1 that should be added]
    • [Missing skill 2 that should be added]
    • [Missing skill 3 that should be added]
    [/SECTION:SKILLS_TO_ADD]

    [SECTION:EXPERIENCE_IMPROVEMENTS]
    • [Suggestion 1 for improving experience bullets]
    • [Suggestion 2 for improving experience bullets]
    • [Suggestion 3 for improving experience bullets]
    [/SECTION:EXPERIENCE_IMPROVEMENTS]

    [SECTION:FORMATTING_IMPROVEMENTS]
    • [Format suggestion 1]
    • [Format suggestion 2]
    • [Format suggestion 3]
    [/SECTION:FORMATTING_IMPROVEMENTS]
    [/SECTION:RESUME_SUGGESTIONS]

    [SECTION:SKILL_DEVELOPMENT]
    [SECTION:PRIORITY_SKILLS]
    • [High Priority Skill 1]: [Brief explanation why it's needed]
    • [High Priority Skill 2]: [Brief explanation why it's needed]
    • [Medium Priority Skill 3]: [Brief explanation why it's needed]
    [/SECTION:PRIORITY_SKILLS]
    
    [SECTION:LEARNING_RESOURCES]
    • [Resource 1]: [Description of specific course/certification/book]
    • [Resource 2]: [Description of specific course/certification/book]
    • [Resource 3]: [Description of specific course/certification/book]
    [/SECTION:LEARNING_RESOURCES]
    
    [SECTION:ACTION_PLAN]
    • [Short-term action 1]: [30-day goal]
    • [Medium-term action 2]: [90-day goal]
    • [Long-term action 3]: [6-month goal]
    [/SECTION:ACTION_PLAN]
    [/SECTION:SKILL_DEVELOPMENT]

    YOU MUST MAINTAIN EXACTLY THE SECTION TAGS AND STRUCTURE SHOWN ABOVE. This is critical as your response will be parsed programmatically.
    """

    # Make a single API call to OpenAI
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",  # Using the 16k model to handle the longer context
        messages=[
            {"role": "system", "content": "You are an expert career advisor. You MUST follow the EXACT formatting instructions specified in the prompt, including all section tags and structure. Do not deviate from the requested format as the response will be parsed programmatically."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=6000  # Increased token limit to accommodate all sections
    )

    # Get the full response
    result = response.choices[0].message.content.strip()
    
    # Parse the comprehensive response into the four sections using the new tag-based approach
    try:
        # Extract each high-level section
        scores_section = extract_section_by_tags(result, "[SECTION:SCORES]", "[/SECTION:SCORES]")
        cover_letter = extract_section_by_tags(result, "[SECTION:COVER_LETTER]", "[/SECTION:COVER_LETTER]")
        resume_suggestions_raw = extract_section_by_tags(result, "[SECTION:RESUME_SUGGESTIONS]", "[/SECTION:RESUME_SUGGESTIONS]")
        skill_development_raw = extract_section_by_tags(result, "[SECTION:SKILL_DEVELOPMENT]", "[/SECTION:SKILL_DEVELOPMENT]")
        
        # Parse scores and feedback from the tagged format
        scores_and_feedback = parse_scores_and_feedback_tagged(scores_section)
        
        # Extract sub-sections from resume suggestions
        resume_suggestions = {
            "skills_to_highlight": extract_section_by_tags(resume_suggestions_raw, "[SECTION:SKILLS_TO_HIGHLIGHT]", "[/SECTION:SKILLS_TO_HIGHLIGHT]"),
            "skills_to_add": extract_section_by_tags(resume_suggestions_raw, "[SECTION:SKILLS_TO_ADD]", "[/SECTION:SKILLS_TO_ADD]"),
            "experience_improvements": extract_section_by_tags(resume_suggestions_raw, "[SECTION:EXPERIENCE_IMPROVEMENTS]", "[/SECTION:EXPERIENCE_IMPROVEMENTS]"),
            "formatting_improvements": extract_section_by_tags(resume_suggestions_raw, "[SECTION:FORMATTING_IMPROVEMENTS]", "[/SECTION:FORMATTING_IMPROVEMENTS]")
        }
        
        # Extract sub-sections from skill development
        skill_development = {
            "priority_skills": extract_section_by_tags(skill_development_raw, "[SECTION:PRIORITY_SKILLS]", "[/SECTION:PRIORITY_SKILLS]"),
            "learning_resources": extract_section_by_tags(skill_development_raw, "[SECTION:LEARNING_RESOURCES]", "[/SECTION:LEARNING_RESOURCES]"),
            "action_plan": extract_section_by_tags(skill_development_raw, "[SECTION:ACTION_PLAN]", "[/SECTION:ACTION_PLAN]")
        }
        
        # Create a string representation of resume_suggestions for frontend compatibility
        resume_suggestions_str = "\n\n".join([
            f"## Skills to Highlight\n{resume_suggestions['skills_to_highlight']}",
            f"## Skills to Add\n{resume_suggestions['skills_to_add']}",
            f"## Experience Improvements\n{resume_suggestions['experience_improvements']}",
            f"## Formatting Improvements\n{resume_suggestions['formatting_improvements']}"
        ])
        
        # Create a string representation of skill_development for frontend compatibility
        skill_development_str = "\n\n".join([
            f"## Priority Skills\n{skill_development['priority_skills']}",
            f"## Learning Resources\n{skill_development['learning_resources']}",
            f"## Action Plan\n{skill_development['action_plan']}"
        ])
        
        return {
            "scores_and_feedback": scores_and_feedback,
            "cover_letter": cover_letter,
            "ideal_resume": resume_suggestions_str,  # String format for frontend compatibility
            "skill_development": skill_development_str,  # String format for frontend compatibility
            "ideal_resume_structured": resume_suggestions,  # Keep structured format for future use
            "skill_development_structured": skill_development  # Keep structured format for future use
        }
    except Exception as e:
        import traceback
        print(f"Error parsing comprehensive analysis: {str(e)}")
        print(traceback.format_exc())
        print(f"Raw response: {result}")  # Log the raw response for debugging
        
        # Attempt to return partial results if possible
        partial_results = {
            "error": f"Error parsing analysis: {str(e)}",
            "partial_response": True,
            "raw_response": result
        }
        
        # Try to extract what we can
        try:
            if scores_section:
                partial_results["scores_and_feedback"] = parse_scores_and_feedback_tagged(scores_section)
        except:
            pass
            
        try:
            if cover_letter:
                partial_results["cover_letter"] = cover_letter
        except:
            pass
        
        raise HTTPException(status_code=500, detail=f"Error parsing analysis: {str(e)}")

def extract_section_by_tags(text, start_tag, end_tag):
    """Extract content between tags, excluding the tags themselves"""
    start_index = text.find(start_tag)
    if start_index == -1:
        raise ValueError(f"Could not find section starting with '{start_tag}'")
    
    start_index += len(start_tag)
    end_index = text.find(end_tag, start_index)
    
    if end_index == -1:
        return text[start_index:].strip()
    
    return text[start_index:end_index].strip()

def parse_scores_and_feedback_tagged(scores_text):
    """Parse scores and feedback using the new tagged format with explicit labels"""
    scores_and_feedback = {}
    
    # Look for the four categories with explicit feedback labels
    categories = ["Skills", "Impact", "Brevity", "Style"]
    
    for category in categories:
        # Find the score
        score_pattern = f"{category}: (\\d+)"
        score_matches = re.search(score_pattern, scores_text)
        
        # Find the feedback with the labeled format
        feedback_pattern = f"{category}_Feedback: (.+?)(?=\\n\\w+:|$)"
        feedback_matches = re.search(feedback_pattern, scores_text, re.DOTALL)
        
        if score_matches and feedback_matches:
            try:
                score = float(score_matches.group(1))
                feedback = feedback_matches.group(1).strip()
                scores_and_feedback[category] = {"score": score, "feedback": feedback}
            except (ValueError, IndexError):
                continue
    
    # Ensure we found all four categories
    if len(scores_and_feedback) != 4:
        print(f"Warning: Found {len(scores_and_feedback)} score categories instead of 4")
        print(f"Score text: {scores_text}")
        # If we have at least one category, we'll continue rather than failing
        if len(scores_and_feedback) == 0:
            raise ValueError("Failed to parse any scores and feedback")
    
    return scores_and_feedback

@app.post("/analyze_resume/")
async def analyze_resume(resume_file: UploadFile = File(...), job_description_file: UploadFile = File(...)):
    try:
        if not resume_file or not job_description_file:
            raise HTTPException(status_code=400, detail="Both resume and job description must be uploaded.")

        print(f"Processing files: {resume_file.filename} and {job_description_file.filename}")
        
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

        # Generate all analysis components with a single API call
        analysis_results = generate_comprehensive_analysis(resume_text, job_description_text)
        
        return analysis_results
    except Exception as e:
        import traceback
        print(f"Error in analyze_resume: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/generate_cover_letter/")
async def generate_cover_letter(resume_file: UploadFile = File(...), job_description_file: UploadFile = File(...)):
    try:
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

        # Enhanced prompt for more tailored cover letter with strict formatting
        prompt = f"""
        Generate a highly personalized and tailored professional cover letter based on the following resume and job description.

        Resume:
        {resume_text}

        Job Description:
        {job_description_text}

        Your task is to:
        1. Create a cover letter that directly references specific experiences, skills, and achievements from the resume
        2. Align these elements with specific requirements and qualifications mentioned in the job description
        3. Address the letter to the hiring manager for the position
        4. Maintain a professional, concise, and enthusiastic tone throughout
        5. Format properly with a greeting, introduction, 2-3 body paragraphs, and conclusion
        
        The cover letter should:
        - Begin with a strong opening paragraph that mentions the specific position and expresses enthusiasm
        - Include at least 3 specific skills or experiences from the resume that directly match the job requirements
        - Quantify achievements where possible (using numbers from the resume if available)
        - Express genuine interest in the company and position (referencing company values or mission if apparent in the job description)
        - End with a professional closing paragraph requesting an interview
        - Be between 250-400 words in total
        
        Please create this cover letter now, with a focus on making it personalized and not generic.
        """

        # Make the API call specifically for cover letter
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer who specializes in creating highly tailored, personalized cover letters that specifically connect a candidate's actual experience to job requirements. You never use generic templates."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200
        )

        # Get the cover letter
        cover_letter = response.choices[0].message.content.strip()

        return {
            "cover_letter": cover_letter
        }
    except Exception as e:
        import traceback
        print(f"Error in generate_cover_letter: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/generate_skill_development_suggestions/")
async def generate_skill_development_suggestions(resume_file: UploadFile = File(...), job_description_file: UploadFile = File(...)):
    try:
        if not resume_file or not job_description_file:
            raise HTTPException(status_code=400, detail="Both resume and job description must be uploaded.")

        resume_extension = resume_file.filename.split(".")[-1].lower()
        job_description_extension = job_description_file.filename.split(".")[-1].lower()

        resume_bytes = await resume_file.read()
        job_description_bytes = await job_description_file.read()

        # Extract text from resume and job description files
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

        # Create a prompt with structured tag-based output format that matches the comprehensive analysis
        prompt = f"""
        [TASK]
        Please analyze the following resume and job description, and provide a structured skill development plan.

        Resume:
        {resume_text}

        Job Description:
        {job_description_text}
        [/TASK]

        You MUST respond using this EXACT structure:

        [SECTION:PRIORITY_SKILLS]
        • [High Priority Skill 1]: [Brief explanation why it's needed]
        • [High Priority Skill 2]: [Brief explanation why it's needed]
        • [Medium Priority Skill 3]: [Brief explanation why it's needed]
        [/SECTION:PRIORITY_SKILLS]
        
        [SECTION:LEARNING_RESOURCES]
        • [Resource 1]: [Description of specific course/certification/book]
        • [Resource 2]: [Description of specific course/certification/book]
        • [Resource 3]: [Description of specific course/certification/book]
        [/SECTION:LEARNING_RESOURCES]
        
        [SECTION:ACTION_PLAN]
        • [Short-term action 1]: [30-day goal]
        • [Medium-term action 2]: [90-day goal]
        • [Long-term action 3]: [6-month goal]
        [/SECTION:ACTION_PLAN]
        """

        # Make the API call for skill development suggestions
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a career development coach specializing in skill gap analysis and professional development planning. You MUST follow the exact format specified in the prompt."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )

        # Parse the response
        result = response.choices[0].message.content.strip()
        
        # Extract sections using tags
        try:
            priority_skills = extract_section_by_tags(result, "[SECTION:PRIORITY_SKILLS]", "[/SECTION:PRIORITY_SKILLS]")
            learning_resources = extract_section_by_tags(result, "[SECTION:LEARNING_RESOURCES]", "[/SECTION:LEARNING_RESOURCES]")
            action_plan = extract_section_by_tags(result, "[SECTION:ACTION_PLAN]", "[/SECTION:ACTION_PLAN]")
            
            # Create structured object
            structured_skill_development = {
                "priority_skills": priority_skills,
                "learning_resources": learning_resources,
                "action_plan": action_plan
            }
            
            # Create string representation for frontend compatibility
            skill_development_str = "\n\n".join([
                f"## Priority Skills\n{priority_skills}",
                f"## Learning Resources\n{learning_resources}",
                f"## Action Plan\n{action_plan}"
            ])
            
            return {
                "skill_development": skill_development_str,  # String format for frontend compatibility
                "structured_skill_development": structured_skill_development  # Keep structured format for future use
            }
        except Exception as e:
            import traceback
            print(f"Error parsing skill development suggestions: {str(e)}")
            print(traceback.format_exc())
            # Fallback to returning the raw response if parsing fails
            return {
                "error": "Failed to parse structured response",
                "raw_response": result
            }
    except Exception as e:
        import traceback
        print(f"Error in generate_skill_development_suggestions: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/generate_mock_interview_questions/")
async def generate_mock_interview_questions(resume_file: UploadFile = File(...), job_description_file: UploadFile = File(...)):
    try:
        if not resume_file or not job_description_file:
            raise HTTPException(status_code=400, detail="Both resume and job description must be uploaded.")

        resume_extension = resume_file.filename.split(".")[-1].lower()
        job_description_extension = job_description_file.filename.split(".")[-1].lower()

        resume_bytes = await resume_file.read()
        job_description_bytes = await job_description_file.read()

        # Extract text from resume and job description files
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

        # Create a prompt to generate mock interview questions with structured format
        prompt = f"""
        [TASK]
        Based on the following resume and job description, generate mock interview questions that the candidate might face during a job interview.

        Resume:
        {resume_text}

        Job Description:
        {job_description_text}
        [/TASK]

        Please respond using this EXACT structure:

        [SECTION:TECHNICAL_QUESTIONS]
        1. [Technical question 1]
        2. [Technical question 2]
        3. [Technical question 3]
        4. [Technical question 4]
        5. [Technical question 5]
        [/SECTION:TECHNICAL_QUESTIONS]

        [SECTION:BEHAVIORAL_QUESTIONS]
        1. [Behavioral question 1]
        2. [Behavioral question 2]
        3. [Behavioral question 3]
        4. [Behavioral question 4]
        5. [Behavioral question 5]
        [/SECTION:BEHAVIORAL_QUESTIONS]

        [SECTION:SITUATIONAL_QUESTIONS]
        1. [Situational question 1]
        2. [Situational question 2]
        3. [Situational question 3]
        [/SECTION:SITUATIONAL_QUESTIONS]

        [SECTION:SAMPLE_ANSWERS]
        Question: [One of the technical questions from above]
        Answer: [Sample strong answer that demonstrates relevant knowledge and experience]

        Question: [One of the behavioral questions from above]
        Answer: [Sample strong answer using the STAR method: Situation, Task, Action, Result]
        [/SECTION:SAMPLE_ANSWERS]
        """

        # Make the API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert career advisor specializing in interview preparation. You MUST follow the exact format specified in the prompt."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )

        # Parse the response
        result = response.choices[0].message.content.strip()
        
        # Extract sections using tags
        try:
            technical_questions = extract_section_by_tags(result, "[SECTION:TECHNICAL_QUESTIONS]", "[/SECTION:TECHNICAL_QUESTIONS]")
            behavioral_questions = extract_section_by_tags(result, "[SECTION:BEHAVIORAL_QUESTIONS]", "[/SECTION:BEHAVIORAL_QUESTIONS]")
            situational_questions = extract_section_by_tags(result, "[SECTION:SITUATIONAL_QUESTIONS]", "[/SECTION:SITUATIONAL_QUESTIONS]")
            sample_answers = extract_section_by_tags(result, "[SECTION:SAMPLE_ANSWERS]", "[/SECTION:SAMPLE_ANSWERS]")
            
            return {
                "technical_questions": technical_questions,
                "behavioral_questions": behavioral_questions,
                "situational_questions": situational_questions,
                "sample_answers": sample_answers
            }
        except Exception as e:
            import traceback
            print(f"Error parsing mock interview questions: {str(e)}")
            print(traceback.format_exc())
            # Fallback to returning the raw response if parsing fails
            return {
                "error": "Failed to parse structured response",
                "raw_response": result
            }
    except Exception as e:
        import traceback
        print(f"Error in generate_mock_interview_questions: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/generate_interview_feedback/")
async def generate_interview_feedback(answers: str):
    try:
        # Create a prompt for interview feedback with structured output
        prompt = f"""
        [TASK]
        Evaluate the following interview answers and provide feedback.

        Answers:
        {answers}
        [/TASK]

        Please respond using this EXACT structure:

        [SECTION:STRENGTHS]
        • [Strength 1]: [Brief explanation]
        • [Strength 2]: [Brief explanation]
        • [Strength 3]: [Brief explanation]
        [/SECTION:STRENGTHS]

        [SECTION:AREAS_FOR_IMPROVEMENT]
        • [Area 1]: [Specific suggestion for improvement]
        • [Area 2]: [Specific suggestion for improvement]
        • [Area 3]: [Specific suggestion for improvement]
        [/SECTION:AREAS_FOR_IMPROVEMENT]

        [SECTION:OVERALL_RATING]
        [Score out of 10]: [Brief justification]
        [/SECTION:OVERALL_RATING]
        """

        # Make the API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert interview coach. You MUST follow the exact format specified in the prompt."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )

        # Get the response
        result = response.choices[0].message.content.strip()

        # Extract sections using tags
        try:
            strengths = extract_section_by_tags(result, "[SECTION:STRENGTHS]", "[/SECTION:STRENGTHS]")
            areas_for_improvement = extract_section_by_tags(result, "[SECTION:AREAS_FOR_IMPROVEMENT]", "[/SECTION:AREAS_FOR_IMPROVEMENT]")
            overall_rating = extract_section_by_tags(result, "[SECTION:OVERALL_RATING]", "[/SECTION:OVERALL_RATING]")
            
            return {
                "strengths": strengths,
                "areas_for_improvement": areas_for_improvement,
                "overall_rating": overall_rating
            }
        except Exception as e:
            import traceback
            print(f"Error parsing interview feedback: {str(e)}")
            print(traceback.format_exc())
            # Fallback to returning the raw response if parsing fails
            return {
                "error": "Failed to parse structured response",
                "raw_response": result
            }
    except Exception as e:
        import traceback
        print(f"Error in generate_interview_feedback: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/generate_resume_suggestions/")
async def generate_resume_suggestions(resume_file: UploadFile = File(...), job_description_file: UploadFile = File(...)):
    try:
        if not resume_file or not job_description_file:
            raise HTTPException(status_code=400, detail="Both resume and job description must be uploaded.")

        resume_extension = resume_file.filename.split(".")[-1].lower()
        job_description_extension = job_description_file.filename.split(".")[-1].lower()

        resume_bytes = await resume_file.read()
        job_description_bytes = await job_description_file.read()

        # Extract text from resume and job description files
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

        # Create a prompt with structured tag-based output format that matches the comprehensive analysis
        prompt = f"""
        [TASK]
        Please analyze the following resume against this job description, and provide specific suggestions to improve the resume.

        Resume:
        {resume_text}

        Job Description:
        {job_description_text}
        [/TASK]

        You MUST respond using this EXACT structure:

        [SECTION:SKILLS_TO_HIGHLIGHT]
        • [Skill 1 from the resume that matches job description]
        • [Skill 2 from the resume that matches job description]
        • [Skill 3 from the resume that matches job description]
        [/SECTION:SKILLS_TO_HIGHLIGHT]

        [SECTION:SKILLS_TO_ADD]
        • [Missing skill 1 that should be added]
        • [Missing skill 2 that should be added]
        • [Missing skill 3 that should be added]
        [/SECTION:SKILLS_TO_ADD]

        [SECTION:EXPERIENCE_IMPROVEMENTS]
        • [Suggestion 1 for improving experience bullets]
        • [Suggestion 2 for improving experience bullets]
        • [Suggestion 3 for improving experience bullets]
        [/SECTION:EXPERIENCE_IMPROVEMENTS]

        [SECTION:FORMATTING_IMPROVEMENTS]
        • [Format suggestion 1]
        • [Format suggestion 2]
        • [Format suggestion 3]
        [/SECTION:FORMATTING_IMPROVEMENTS]
        """

        # Make the API call for resume suggestions
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional resume writer with expertise in optimizing resumes for specific job descriptions. You MUST follow the exact format specified in the prompt."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )

        # Parse the response
        result = response.choices[0].message.content.strip()
        
        # Extract sections using tags
        try:
            skills_to_highlight = extract_section_by_tags(result, "[SECTION:SKILLS_TO_HIGHLIGHT]", "[/SECTION:SKILLS_TO_HIGHLIGHT]")
            skills_to_add = extract_section_by_tags(result, "[SECTION:SKILLS_TO_ADD]", "[/SECTION:SKILLS_TO_ADD]")
            experience_improvements = extract_section_by_tags(result, "[SECTION:EXPERIENCE_IMPROVEMENTS]", "[/SECTION:EXPERIENCE_IMPROVEMENTS]")
            formatting_improvements = extract_section_by_tags(result, "[SECTION:FORMATTING_IMPROVEMENTS]", "[/SECTION:FORMATTING_IMPROVEMENTS]")
            
            # Create structured object
            structured_suggestions = {
                "skills_to_highlight": skills_to_highlight,
                "skills_to_add": skills_to_add,
                "experience_improvements": experience_improvements,
                "formatting_improvements": formatting_improvements
            }
            
            # Create string representation for frontend compatibility
            suggestions_str = "\n\n".join([
                f"## Skills to Highlight\n{skills_to_highlight}",
                f"## Skills to Add\n{skills_to_add}",
                f"## Experience Improvements\n{experience_improvements}",
                f"## Formatting Improvements\n{formatting_improvements}"
            ])
            
            return {
                "suggestions": suggestions_str,  # String format for frontend compatibility
                "structured_suggestions": structured_suggestions  # Keep structured format for future use
            }
        except Exception as e:
            import traceback
            print(f"Error parsing resume suggestions: {str(e)}")
            print(traceback.format_exc())
            # Fallback to returning the raw response if parsing fails
            return {
                "error": "Failed to parse structured response",
                "raw_response": result
            }
    except Exception as e:
        import traceback
        print(f"Error in generate_resume_suggestions: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
