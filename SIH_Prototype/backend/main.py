import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import io

# Import all our logic and constants from the logic.py file
from logic import (
    compute_ranking, 
    get_all_form_data, 
    PRESET_INTERNSHIPS,
    ALL_SKILLS_LIST
)

app = FastAPI(
    title="Smart Internship Matching Engine API",
    description="API backend for the matching engine."
)

# --- IMPORTANT: CORS Middleware ---
# This allows your frontend (running on a different domain/port)
# to make requests to this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],
)

# --- In-Memory "Database" ---
# Just like your Streamlit app, we'll store the loaded candidates in a global DataFrame.
# We initialize it with the same sample data.
sample_data = {
    'name': ['Priya Sharma', 'Rohan Verma (PWD)', 'Aisha Khan', 'Suresh Gupta (SC)'],
    'education': ['B.TECH CS', 'B.TECH IT', 'B.COM ACCOUNTS', '12TH PASS'],
    'skills': ['PYTHON;AIML;MS EXCEL', 'JAVA;WEB DEVELOPMENT;COMMUNICATION', 'TALLY;GST;MS EXCEL', 'DATA ENTRY;MS WORD'],
    'city': ['Mumbai', 'Pune', 'Mumbai', 'Delhi'],
    'state': ['Maharashtra', 'Maharashtra', 'Maharashtra', 'Delhi'],
    'interest': ['AI and Machine Learning', 'Full Stack Development', 'Accounting and Finance', 'Office Administration'],
    'gender': ['FEMALE', 'MALE', 'FEMALE', 'MALE'],
    'category': ['GENERAL', 'PWD', 'GENERAL', 'SC']
}
DF_CANDIDATES = pd.DataFrame(sample_data)

# --- Pydantic Models (Data Validation) ---
# This tells FastAPI what the JSON data for a custom internship should look like.
class InternshipRequest(BaseModel):
    post: str
    company: str
    offers: int
    city: str
    state: str
    degree: List[str]
    branch: List[str]
    skills: List[str]
    priority: List[str]

# --- API ENDPOINTS ---

@app.post("/api/upload-csv")
async def upload_candidate_csv(file: UploadFile = File(...)):
    """
    Endpoint to upload the candidates CSV file.
    It replaces the global DF_CANDIDATES DataFrame.
    """
    global DF_CANDIDATES
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")
    
    try:
        contents = await file.read()
        buffer = io.StringIO(contents.decode('utf-8'))
        df = pd.read_csv(buffer)
        
        # Normalize columns just like in the streamlit app
        df.columns = df.columns.str.lower().str.strip()
        
        # Check for required columns
        required_cols = {'name', 'education', 'skills', 'city', 'state'}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise HTTPException(status_code=400, detail=f"CSV is missing required columns: {missing}")
            
        DF_CANDIDATES = df
        return {"status": "success", "rows_loaded": len(df), "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/api/presets")
async def get_preset_internships():
    """
    Returns the list of hardcoded preset internships.
    """
    return PRESET_INTERNSHIPS

@app.get("/api/form-data")
async def get_form_constants():
    """
    Returns all the constants needed to populate the frontend dropdowns.
    """
    return get_all_form_data()

@app.post("/api/rank-custom")
async def rank_custom_internship(internship_data: InternshipRequest):
    """
    Receives a custom internship (as JSON) and ranks candidates from the
    globally stored DataFrame against it.
    """
    global DF_CANDIDATES
    if DF_CANDIDATES.empty:
        raise HTTPException(status_code=400, detail="No candidate data loaded. Please upload a CSV first.")
        
    # The internship_data is already a validated Pydantic model,
    # so we can convert it to a dict to pass to our logic function.
    job_dict = internship_data.model_dump()
    
    ranked_list = compute_ranking(DF_CANDIDATES, job_dict)
    
    return {"ranking": ranked_list, "internship_details": job_dict}


# --- To run this server ---
# Open your terminal in the 'backend' folder and run:
# uvicorn main:app --reload