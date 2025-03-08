# ResuMate

ResuMate is an application that helps users improve their resumes by matching them against job descriptions.

## Deployment on Render

This repository is configured for deployment on Render using the `render.yaml` Blueprint.

### Setup Steps:

1. Fork or clone this repository
2. Connect your GitHub account to Render
3. Create a new Blueprint on Render and select this repository
4. Add the required environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
5. Deploy the Blueprint

Render will automatically deploy both the frontend and backend services.

### Manual Service Configuration

Alternatively, you can manually set up services on Render:

#### Backend API (FastAPI)
- **Build Command**: `pip install -r backend/requirements.txt && python -m spacy download en_core_web_sm`
- **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**: 
  - `OPENAI_API_KEY`: Your OpenAI API key

#### Frontend (React)
- **Build Command**: `npm install && npm run build`
- **Start Command**: `npx serve -s build -l $PORT`
- **Environment Variables**:
  - `REACT_APP_API_URL`: URL of your deployed backend API
