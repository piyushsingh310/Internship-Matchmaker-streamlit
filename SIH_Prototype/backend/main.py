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
    ALL_SKILLS_LIST,
    generate_smart_allotment  # <-- IMPORT THE NEW ALLOTMENT FUNCTION
)

app = FastAPI(
    title="Smart Internship Matching Engine API",
    description="API backend for the matching engine."
)

# --- CORS Middleware (Unchanged) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],
)

# --- In-Memory "Database" (Unchanged) ---
# Added 'past_participation' to sample data
sample_data = {
    'name': ['Priya Sharma', 'Rohan Verma (PWD)', 'Aisha Khan', 'Suresh Gupta (SC)'],
    'education': ['B.TECH CS', 'B.TECH IT', 'B.COM ACCOUNTS', '12TH PASS'],
    'skills': ['PYTHON;AIML;MS EXCEL', 'JAVA;WEB DEVELOPMENT;COMMUNICATION', 'TALLY;GST;MS EXCEL', 'DATA ENTRY;MS WORD'],
    'city': ['Mumbai', 'Pune', 'Mumbai', 'Delhi'],
    'state': ['Maharashtra', 'Maharashtra', 'Maharashtra', 'Delhi'],
    'interest': ['AI and Machine Learning', 'Full Stack Development', 'Accounting and Finance', 'Office Administration'],
    'gender': ['FEMALE', 'MALE', 'FEMALE', 'MALE'],
    'category': ['GENERAL', 'PWD', 'GENERAL', 'SC'],
    'past_participation': ['NO', 'YES', 'NO', 'NO']
}
DF_CANDIDATES = pd.DataFrame(sample_data)

# --- Pydantic Models (Data Validation) ---
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

# --- NEW Pydantic Model for Allotment ---
class AllotmentRequest(BaseModel):
    job_keys: List[str]


# --- API ENDPOINTS ---
@app.post("/api/upload-csv")
async def upload_candidate_csv(file: UploadFile = File(...)):
    """
    Endpoint to upload the candidates CSV file. (Unchanged)
    """
    global DF_CANDIDATES
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")
    
    try:
        contents = await file.read()
        buffer = io.StringIO(contents.decode('utf-8'))
        df = pd.read_csv(buffer)
        
        df.columns = df.columns.str.lower().str.strip()
        
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
    """ Returns the list of hardcoded preset internships. (Unchanged) """
    return PRESET_INTERNSHIPS

@app.get("/api/form-data")
async def get_form_constants():
    """ Returns all constants needed to populate frontend dropdowns. (Unchanged) """
    return get_all_form_data()

@app.post("/api/rank-custom")
async def rank_custom_internship(internship_data: InternshipRequest):
    """ Receives a custom internship and ranks candidates against it. (Unchanged) """
    global DF_CANDIDATES
    if DF_CANDIDATES.empty:
        raise HTTPException(status_code=400, detail="No candidate data loaded. Please upload a CSV first.")
        
    job_dict = internship_data.model_dump()
    ranked_list = compute_ranking(DF_CANDIDATES, job_dict)
    
    return {"ranking": ranked_list, "internship_details": job_dict}


# --- *** ALLOTMENT API ENDPOINT *** ---

@app.post("/api/generate-allotment")
async def generate_master_allotment(request: AllotmentRequest):
    """
    Receives a list of selected preset job keys, runs the complex
    smart allotment engine, and returns a single master list of all
    candidates (either Allotted or Waitlisted).
    """
    global DF_CANDIDATES
    if DF_CANDIDATES.empty:
        raise HTTPException(status_code=400, detail="No candidate data loaded. Please upload a CSV first.")
    
    if not request.job_keys:
        raise HTTPException(status_code=400, detail="No internship roles were selected for allotment.")
    
    # Filter the master preset list to get the full job objects for the selected keys
    preset_lookup = {job['key']: job for job in PRESET_INTERNSHIPS}
    selected_jobs = [preset_lookup[key] for key in request.job_keys if key in preset_lookup]

    if not selected_jobs:
         raise HTTPException(status_code=404, detail="Selected job keys not found.")

    try:
        # Call the new logic function
        allotment_list = generate_smart_allotment(DF_CANDIDATES, selected_jobs)
        total_offers = sum(j['offers'] for j in selected_jobs)
        total_allotted = len([c for c in allotment_list if c['Status'] == 'Allotted'])
        
        return {
            "allotment_list": allotment_list,
            "summary": {
                "total_candidates": len(DF_CANDIDATES),
                "total_jobs_selected": len(selected_jobs),
                "total_offers_available": total_offers,
                "total_candidates_allotted": total_allotted
            }
        }
    except Exception as e:
        # Catch any unexpected errors during the complex allotment logic
        print(f"Allotment Error: {e}") # Log error to server console
        raise HTTPException(status_code=500, detail=f"An internal error occurred during allotment: {str(e)}")

