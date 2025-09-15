import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Set

# --- 1. EXPANDED TAXONOMY & MASTER DATA (Unchanged) ---

CORE_TREE: Dict[str, Dict[str, List[str]]] = {
    "engineering": {
        "computer_eng": ["PYTHON", "JAVA", "C++", "C#", "JAVASCRIPT", "SQL", "GOLANG", "RUST", "AIML", "WEB DEVELOPMENT", "APP DEVELOPMENT", "CYBERSECURITY", "DATA ENGINEERING", "DEVOPS", "CLOUD COMPUTING", "BLOCKCHAIN", "COMPUTER VISION", "NLP"],
        "electrical_eng": ["POWER SYSTEMS", "EMBEDDED SYSTEMS", "IOT", "VLSI", "PCB DESIGN", "CONTROL SYSTEMS", "MATLAB", "SIMULINK"],
        "mechanical_eng": ["AUTOCAD", "SOLIDWORKS", "CATIA", "ANSYS", "THERMAL ENGINEERING", "AUTOMOTIVE DESIGN", "ROBOTICS", "3D PRINTING"],
        "civil_eng": ["STRUCTURAL ANALYSIS", "STAAD PRO", "ETABS", "SURVEYING", "GEOTECHNICAL ENGINEERING"],
    },
    "finance": {
        "accounting": ["TALLY", "GST", "INCOME TAX", "FINANCIAL ANALYSIS", "AUDITING", "QUICKBOOKS"],
        "investment_banking": ["FINANCIAL MODELING", "VALUATION", "MERGERS & ACQUISITIONS", "EQUITY RESEARCH"],
        "fintech": ["PAYMENT GATEWAYS", "ALGORITHMIC TRADING", "REGTECH"],
    },
    "law": {
        "corporate_law": ["CONTRACT DRAFTING", "LEGAL RESEARCH", "COMPLIANCE", "DUE DILIGENCE"],
        "litigation": ["CASE PREPARATION", "LEGAL BRIEFING", "MOOT COURT"],
        "ipr": ["PATENT LAW", "TRADEMARK LAW", "COPYRIGHT LAW"],
    },
    "medical_pharma": {
        "pharma": ["QUALITY ASSURANCE (QA)", "QUALITY CONTROL (QC)", "REGULATORY AFFAIRS", "PHARMACOVIGILANCE"],
        "clinical": ["CLINICAL RESEARCH", "PATIENT COUNSELING", "MEDICAL WRITING"],
    },
    "design_creative": {
        "ui_ux": ["FIGMA", "ADOBE XD", "SKETCH", "USER RESEARCH", "WIREFRAMING"],
        "graphic_design": ["ADOBE PHOTOSHOP", "ADOBE ILLUSTRATOR", "CANVA", "VIDEO EDITING"],
    },
    "business_management": {
        "marketing": ["SEO", "SEM", "SOCIAL MEDIA MARKETING", "CONTENT WRITING", "EMAIL MARKETING"],
        "sales": ["LEAD GENERATION", "CRM SOFTWARE", "NEGOTIAITON"], # Typo fix from NEGOTIATION
        "operations": ["SUPPLY CHAIN", "LOGISTICS", "PROJECT MANAGEMENT"],
    }
}
NON_CORE = ["COMMUNICATION", "ENGLISH PROFICIENCY", "MS WORD", "MS EXCEL", "MS POWERPOINT", "DATA ENTRY", "BASIC MATHS", "TEAMWORK", "PROBLEM SOLVING"]

# --- Master lists (Unchanged) ---
BACHELORS_DEGREES = ["B.TECH", "B.E.", "B.COM", "B.A.", "BBA", "BCA", "B.SC", "LLB", "B.PHARM", "DIPLOMA", "12TH PASS"]
ENGINEERING_BRANCHES = ["CS", "IT", "ECE", "EEE", "MECHANICAL", "CIVIL", "CHEMICAL", "BIOTECHNOLOGY"]
FINANCE_BRANCHES = ["ACCOUNTS", "FINANCE", "BANKING", "ECONOMICS"]
LAW_BRANCHES = ["CORPORATE", "CRIMINAL", "IPR", "CONSTITUTIONAL"]
ALL_BRANCHES = sorted(list(set(ENGINEERING_BRANCHES + FINANCE_BRANCHES + LAW_BRANCHES)))
INDIAN_STATES = ["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi"]


# --- PRESET INTERNSHIP LIST (Unchanged) ---
PRESET_INTERNSHIPS = [
    {"key": "job1", "post": "AI/ML Intern", "company": "IntelliTech", "offers": 3, "degree": ["B.TECH"], "branch": ["CS", "IT"], "skills": ["AIML", "PYTHON", "DATA ENGINEERING", "MS EXCEL"], "city": "Bengaluru", "state": "Karnataka", "priority": ["skills", "education", "interest", "location"]},
    {"key": "job2", "post": "Web Development Intern", "company": "WebWeavers", "offers": 5, "degree": ["B.TECH", "BCA", "B.SC"], "branch": ["CS", "IT"], "skills": ["JAVASCRIPT", "WEB DEVELOPMENT", "DEVOPS", "COMMUNICATION"], "city": "Pune", "state": "Maharashtra", "priority": ["skills", "education", "location", "interest"]},
    {"key": "job3", "post": "Financial Analyst Intern", "company": "Capital Gains Inc.", "offers": 4, "degree": ["B.COM", "BBA"], "branch": ["ACCOUNTS", "FINANCE"], "skills": ["FINANCIAL ANALYSIS", "FINANCIAL MODELING", "MS EXCEL"], "city": "Mumbai", "state": "Maharashtra", "priority": ["skills", "education", "interest", "location"]},
    {"key": "job4", "post": "Data Science Intern", "company": "DataCorp Analytics", "offers": 3, "degree": ["B.TECH", "B.SC"], "branch": ["CS", "IT"], "skills": ["PYTHON", "SQL", "AIML", "DATA ENGINEERING"], "city": "Chennai", "state": "Tamil Nadu", "priority": ["skills", "education", "interest", "location"]},
    {"key": "job5", "post": "Cybersecurity Intern", "company": "SecureNet Solutions", "offers": 2, "degree": ["B.TECH"], "branch": ["CS", "IT", "ECE"], "skills": ["CYBERSECURITY", "PYTHON", "COMMUNICATION"], "city": "Hyderabad", "state": "Telangana", "priority": ["skills", "education", "location", "interest"]},
    {"key": "job6", "post": "Digital Marketing Intern", "company": "Brand Builders", "offers": 6, "degree": ["B.COM", "BBA", "B.A."], "branch": ["MARKETING", "FINANCE"], "skills": ["SEO", "SOCIAL MEDIA MARKETING", "CONTENT WRITING", "MS EXCEL"], "city": "Delhi", "state": "Delhi", "priority": ["skills", "interest", "education", "location"]},
]

# --- 2. UTILITY FUNCTIONS (Unchanged) ---

def normalize_skill(s: str) -> str:
    return str(s).strip().upper() if pd.notna(s) and str(s).strip() != "" else ""

def get_skill_maps() -> Tuple[Dict[str, Tuple[str, str]], Set[str], List[str]]:
    core_lookup = {}
    for row1, row2map in CORE_TREE.items():
        for row2, row3list in row2map.items():
            for skill in row3list:
                norm_skill = normalize_skill(skill)
                core_lookup[norm_skill] = (f"{row1}/{row2}", row2)

    non_core_set = {normalize_skill(s) for s in NON_CORE}
    all_skills_list = sorted(list(core_lookup.keys()) + list(non_core_set))
    return core_lookup, non_core_set, all_skills_list

CORE_LOOKUP, NON_CORE_SET, ALL_SKILLS_LIST = get_skill_maps()

# Normalize preset internship skills
for j in PRESET_INTERNSHIPS:
    j['skills'] = [normalize_skill(s) for s in j.get('skills', [])]
    j['degree'] = [normalize_skill(d) for d in j.get('degree', [])]
    j['branch'] = [normalize_skill(b) for b in j.get('branch', [])]


def skill_is_core(skill: str) -> bool:
    return normalize_skill(skill) in CORE_LOOKUP

def parse_skills(s: str) -> List[str]:
    if pd.isna(s):
        return []
    if isinstance(s, (list, tuple, set)):
        return [normalize_skill(x) for x in s if normalize_skill(x)]
    return [normalize_skill(p) for p in str(s).replace(";", ",").split(",") if p.strip()]

# --- 3. SCORING ALGORITHMS (Unchanged) ---

def education_score(candidate_edu: str, required_degrees: List[str], required_branches: List[str]) -> float:
    c_edu = normalize_skill(candidate_edu)
    if not c_edu or not required_degrees:
        return 0.0
    req_deg = [normalize_skill(d) for d in required_degrees]
    req_branch = [normalize_skill(b) for b in required_branches]
    if any(d in c_edu for d in req_deg) and (not req_branch or any(b in c_edu for b in req_branch)):
        return 100.0
    if any(d in c_edu for d in req_deg):
        return 80.0
    if "B.TECH" in req_deg and ("BCA" in c_edu or "B.SC" in c_edu) and ("CS" in c_edu or "IT" in c_edu):
        return 60.0
    if "DIPLOMA" in c_edu and any(b in c_edu for b in ENGINEERING_BRANCHES):
        return 40.0
    if "12TH" in c_edu or "XII" in c_edu:
        return 20.0
    return 0.0

def location_score(c_city: str, c_state: str, i_city: str, i_state: str) -> float:
    if c_city and i_city and normalize_skill(c_city) == normalize_skill(i_city):
        return 100.0
    if c_state and i_state and normalize_skill(c_state) == normalize_skill(i_state):
        return 66.0
    return 33.0

def best_match_for_required_skill(required_skill: str, candidate_skills: List[str]) -> Tuple[float, str]:
    req = normalize_skill(required_skill)
    if req in NON_CORE_SET:
        return (100.0, req) if req in candidate_skills else (0.0, "")
    if req in CORE_LOOKUP:
        req_row2, req_row3_bucket = CORE_LOOKUP[req]
        best_score = 0.0
        best_match_skill = ""
        for cs in candidate_skills:
            if cs == req:
                return 100.0, cs
            if req in cs or cs in req:
                if best_score < 80.0:
                    best_score = 80.0
                    best_match_skill = cs
            if cs in CORE_LOOKUP:
                cs_row2, cs_row3_bucket = CORE_LOOKUP[cs]
                if cs_row3_bucket == req_row3_bucket:
                    if best_score < 50.0:
                        best_score = 50.0
                        best_match_skill = cs
                elif cs_row2 == req_row2:
                    if best_score < 10.0:
                        best_score = 10.0
                        best_match_skill = cs
        return best_score, best_match_skill
    return 0.0, ""

def compute_skills_percent(required_skills: List[str], candidate_skills: List[str], core_weight: float = 0.8) -> float:
    if not required_skills:
        return 100.0
    req_norm = [normalize_skill(s) for s in required_skills]
    cand_norm = [normalize_skill(s) for s in candidate_skills]
    core_req = [s for s in req_norm if skill_is_core(s)]
    non_core_req = [s for s in req_norm if not skill_is_core(s)]
    core_scores = [best_match_for_required_skill(rs, cand_norm)[0] for rs in core_req]
    non_core_scores = [best_match_for_required_skill(rs, cand_norm)[0] for rs in non_core_req]
    avg_core = np.mean(core_scores) if core_scores else 100.0
    avg_non_core = np.mean(non_core_scores) if non_core_scores else 100.0
    if not core_req:
        return avg_non_core
    if not non_core_req:
        return avg_core
    return core_weight * avg_core + (1 - core_weight) * avg_non_core

def interest_score(candidate_interest: str, internship_post: str) -> float:
    c_int = normalize_skill(candidate_interest)
    i_post = normalize_skill(internship_post)
    if not c_int or not i_post:
        return 0.0
    if i_post in c_int:
        return 100.0
    c_tokens = set(c_int.replace("-", " ").split())
    i_tokens = set(i_post.replace("-", " ").split())
    if c_tokens & i_tokens:
        return 50.0
    return 25.0

def overall_score(scores: Dict[str, float], priority_order: List[str]) -> float:
    weights = {1: 0.4, 2: 0.3, 3: 0.2, 4: 0.1}
    final_score = 0.0
    for i, criteria in enumerate(priority_order, 1):
        final_score += scores.get(criteria, 0.0) * weights[i]
    return final_score

# --- 4. CORE APPLICATION LOGIC (Ranking function is unchanged) ---

def get_diversity_marker(row: pd.Series) -> str:
    gender = str(row.get("gender", "")).upper()
    category = str(row.get("category", "")).upper()
    markers = []
    if "FEMALE" in gender:
        markers.append("♀️")
    if "PWD" in category:
        markers.append("♿")
    if "SC" in category:
        markers.append("🔵")
    if "ST" in category:
        markers.append("🔴")
    return " ".join(markers)

def compute_ranking(df_candidates: pd.DataFrame, internship: dict) -> pd.DataFrame:
    """The main function to process the candidate list and rank them for an internship."""
    if df_candidates.empty:
        return pd.DataFrame()

    rows = []
    for _, row in df_candidates.iterrows():
        c_skills = parse_skills(row.get("skills", ""))
        
        scores = {
            "skills": compute_skills_percent(internship["skills"], c_skills),
            "education": education_score(str(row.get("education", "")), internship["degree"], internship["branch"]),
            "location": location_score(str(row.get("city", "")), str(row.get("state", "")), internship["city"], internship["state"]),
            "interest": interest_score(str(row.get("interest", "")), internship["post"]) 
        }

        total = overall_score(scores, internship["priority"]) if internship.get("priority") else np.mean(list(scores.values()))

        past_participation = str(row.get("past_participation", "")).strip().upper()
        if past_participation == "YES":
            total *= 0.80  

        rows.append({
            "Select": False,
            "Name": row.get("name", ""),
            "Diversity": get_diversity_marker(row),
            "Past Participant": "Yes" if past_participation == "YES" else "No",
            "Overall Match %": round(total, 2),
            "Skills %": round(scores["skills"], 2),
            "Education %": round(scores["education"], 2),
            "Location %": round(scores["location"], 2),
            "Interest %": round(scores["interest"], 2),
            "Candidate Skills": ", ".join(c_skills),
            "Education": row.get("education", ""),
            "Gender": str(row.get("gender", "")).upper(),
            "Category": str(row.get("category", "")).upper()
        })

    df_ranked = pd.DataFrame(rows).sort_values(by="Overall Match %", ascending=False).reset_index(drop=True)
    df_ranked.index += 1
    
    df_ranked.insert(1, "Rank", df_ranked.index)

    return df_ranked.to_dict('records')

# --- DATA FOR FRONTEND DROPDOWNS (Unchanged) ---

def get_all_form_data():
    """Helper function to send all constants to the frontend in one go."""
    return {
        "bachelors_degrees": BACHELORS_DEGREES,
        "all_branches": ALL_BRANCHES,
        "all_skills_list": ALL_SKILLS_LIST,
        "indian_states": INDIAN_STATES
    }

# --- 5. *** NEW SMART ALLOTMENT LOGIC *** ---

def is_diversity_candidate(row: pd.Series) -> bool:
    """Helper to check if a candidate meets SC, ST, or PWD criteria."""
    category = str(row.get("category", "")).upper()
    return any(c in category for c in ["SC", "ST", "PWD"])

def calculate_all_scores_for_job(candidate_row: pd.Series, internship: Dict) -> Dict:
    """Helper function to calculate all scores for a single cand-job pair."""
    c_skills = parse_skills(candidate_row.get("skills", ""))
    scores = {
        "skills": round(compute_skills_percent(internship["skills"], c_skills), 2),
        "education": round(education_score(str(candidate_row.get("education", "")), internship["degree"], internship["branch"]), 2),
        "location": round(location_score(str(candidate_row.get("city", "")), str(candidate_row.get("state", "")), internship["city"], internship["state"]), 2),
        "interest": round(interest_score(str(candidate_row.get("interest", "")), internship["post"]), 2) 
    }
    total = round(overall_score(scores, internship["priority"]), 2)
    
    past_participation = str(candidate_row.get("past_participation", "")).strip().upper()
    if past_participation == "YES":
        total = round(total * 0.80, 2)
    
    scores["total"] = total
    return scores

def generate_smart_allotment(df_candidates: pd.DataFrame, selected_jobs: List[Dict]) -> List[Dict]:
    """
    Main Smart Allotment Engine.
    This runs a two-pass algorithm:
    1. Pass 1: Fills diversity & female quotas for each job using the best *available* candidate.
    2. Pass 2: Fills all remaining slots using a global "best score" greedy algorithm.
    3. Pass 3: Formats the final list of ALL candidates (Allotted or Waitlisted).
    """
    
    # --- Step 1: Create the Master Score Matrix ---
    # Calculate score for EVERY candidate against EVERY selected job.
    all_scores_matrix = []
    for _, row in df_candidates.iterrows():
        for job in selected_jobs:
            all_scores_dict = calculate_all_scores_for_job(row, job)
            all_scores_matrix.append({
                "candidate_name": row["name"],
                "row_data": row.to_dict(),
                "job_key": job['key'],
                "post": job['post'],
                "total_score": all_scores_dict['total'],
                "all_scores": all_scores_dict,
                "is_female": "FEMALE" in str(row.get("gender", "")).upper(),
                "is_diversity": is_diversity_candidate(row)
            })

    # --- Step 2: Create sorted "Pools" for each job ---
    allotment_pools = {}
    for job in selected_jobs:
        job_key = job['key']
        # Get all matches for this job and sort them by score (best first)
        pool = sorted(
            [m for m in all_scores_matrix if m['job_key'] == job_key],
            key=lambda x: x['total_score'],
            reverse=True
        )
        allotment_pools[job_key] = pool

    # --- Step 3: Allocation Pass 1 (Enforce Diversity Quotas) ---
    final_allotment_map = {job['key']: [] for job in selected_jobs} # Holds the final lists
    allocated_candidates_set = set() # Tracks who has been given any job

    for job in selected_jobs:
        job_key = job['key']
        pool = allotment_pools[job_key] # This job's ranked candidate list
        offers = job['offers']

        if offers == 0:
            continue

        # 1. Find best AVAILABLE female
        best_female = next(
            (c for c in pool if c['is_female'] and c['candidate_name'] not in allocated_candidates_set), 
            None
        )
        if best_female:
            final_allotment_map[job_key].append(best_female)
            allocated_candidates_set.add(best_female['candidate_name'])
        
        # 2. Find best AVAILABLE diversity candidate (who isn't the female we just added)
        best_diversity = next(
            (c for c in pool if c['is_diversity'] and c['candidate_name'] not in allocated_candidates_set),
            None
        )
        if best_diversity:
            final_allotment_map[job_key].append(best_diversity)
            allocated_candidates_set.add(best_diversity['candidate_name'])

    # --- Step 4: Allocation Pass 2 (Fill remaining slots with best available) ---
    
    # Create a global pool of all remaining matches for unallocated candidates
    remaining_matches_pool = sorted(
        [m for m in all_scores_matrix if m['candidate_name'] not in allocated_candidates_set],
        key=lambda x: x['total_score'], # Sort by highest score, regardless of job
        reverse=True
    )

    # Get offer limits
    job_offer_limits = {j['key']: j['offers'] for j in selected_jobs}

    # Iterate the global pool and give everyone their best available slot
    for match in remaining_matches_pool:
        c_name = match['candidate_name']
        job_key = match['job_key']

        # If this candidate is STILL not allocated AND the job they match with has space
        if (c_name not in allocated_candidates_set and 
            len(final_allotment_map[job_key]) < job_offer_limits[job_key]):
            
            # Allocate them
            final_allotment_map[job_key].append(match)
            allocated_candidates_set.add(c_name)

    # --- Step 5: Format Final Output List (All Candidates) ---
    final_results_list = []
    
    # Create a simple lookup map of who got what
    candidate_allotment_lookup = {}
    for job_key, allotted_candidates in final_allotment_map.items():
        for candidate_match in allotted_candidates:
            candidate_allotment_lookup[candidate_match['candidate_name']] = candidate_match

    # Build the final list, showing "Allotted" or "Waitlisted" for everyone
    for _, row in df_candidates.iterrows():
        name = row['name']
        if name in candidate_allotment_lookup:
            # This candidate was allotted a job
            match_data = candidate_allotment_lookup[name]
            final_results_list.append({
                "Name": name,
                "Diversity": get_diversity_marker(row),
                "Status": "Allotted",
                "Allotted Job": match_data['post'],
                "Match %": match_data['total_score'],
                "Skills %": match_data['all_scores']['skills'],
                "Education %": match_data['all_scores']['education'],
                "Location %": match_data['all_scores']['location'],
                "Interest %": match_data['all_scores']['interest'],
                "Gender": str(row.get("gender", "")).upper(),
                "Category": str(row.get("category", "")).upper(),
            })
        else:
            # This candidate is on the waitlist
            final_results_list.append({
                "Name": name,
                "Diversity": get_diversity_marker(row),
                "Status": "Waitlisted",
                "Allotted Job": "N/A",
                "Match %": 0.0,
                "Skills %": 0.0,
                "Education %": 0.0,
                "Location %": 0.0,
                "Interest %": 0.0,
                "Gender": str(row.get("gender", "")).upper(),
                "Category": str(row.get("category", "")).upper(),
            })

    # Sort the final list to show Allotted candidates first, then by score
    final_results_list.sort(key=lambda x: (x['Status'] != 'Allotted', -x['Match %']))
    
    return final_results_list