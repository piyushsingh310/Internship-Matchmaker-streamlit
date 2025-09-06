import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Set

st.set_page_config(page_title="Smart Internship Matching Engine", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------------
# --- 1. EXPANDED TAXONOMY & MASTER DATA ---
# ---------------------------------------------------------------------

# Greatly expanded skill tree for richer matching
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
        "sales": ["LEAD GENERATION", "CRM SOFTWARE", "NEGOTIATION"],
        "operations": ["SUPPLY CHAIN", "LOGISTICS", "PROJECT MANAGEMENT"],
    }
}

NON_CORE = ["COMMUNICATION", "ENGLISH PROFICIENCY", "MS WORD", "MS EXCEL", "MS POWERPOINT", "DATA ENTRY", "BASIC MATHS", "TEAMWORK", "PROBLEM SOLVING"]

# --- Master lists for UI selectors ---
BACHELORS_DEGREES = ["B.TECH", "B.E.", "B.COM", "B.A.", "BBA", "BCA", "B.SC", "LLB", "B.PHARM", "DIPLOMA", "12TH PASS"]
ENGINEERING_BRANCHES = ["CS", "IT", "ECE", "EEE", "MECHANICAL", "CIVIL", "CHEMICAL", "BIOTECHNOLOGY"]
FINANCE_BRANCHES = ["ACCOUNTS", "FINANCE", "BANKING", "ECONOMICS"]
LAW_BRANCHES = ["CORPORATE", "CRIMINAL", "IPR", "CONSTITUTIONAL"]
# Combine all branches for a general list
ALL_BRANCHES = sorted(list(set(ENGINEERING_BRANCHES + FINANCE_BRANCHES + LAW_BRANCHES)))

INDIAN_STATES = ["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi"]


# ---------------------------------------------------------------------
# --- 2. UTILITY FUNCTIONS ---
# ---------------------------------------------------------------------

def normalize_skill(s: str) -> str:
    """Cleans and uppercases a skill string."""
    return str(s).strip().upper() if pd.notna(s) and str(s).strip() != "" else ""

@st.cache_data
def get_skill_maps() -> Tuple[Dict[str, Tuple[str, str]], Set[str], List[str]]:
    """Flattens the core skill tree and prepares lookup sets. Cached for performance."""
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


def skill_is_core(skill: str) -> bool:
    return normalize_skill(skill) in CORE_LOOKUP


def parse_skills(s: str) -> List[str]:
    """Parses a comma or semicolon-separated string of skills and normalizes them."""
    if pd.isna(s):
        return []
    # Accept lists too (if the CSV had list-like column), otherwise treat as string
    if isinstance(s, (list, tuple, set)):
        return [normalize_skill(x) for x in s if normalize_skill(x)]
    return [normalize_skill(p) for p in str(s).replace(";", ",").split(",") if p.strip()]

# ---------------------------------------------------------------------
# --- 3. SCORING ALGORITHMS ---
# ---------------------------------------------------------------------

def education_score(candidate_edu: str, required_degrees: List[str], required_branches: List[str]) -> float:
    """Calculates education match score based on a hierarchy of rules."""
    c_edu = normalize_skill(candidate_edu)
    if not c_edu or not required_degrees:
        return 0.0

    req_deg = [normalize_skill(d) for d in required_degrees]
    req_branch = [normalize_skill(b) for b in required_branches]

    # Rule 1: 100% for exact degree + branch match
    if any(d in c_edu for d in req_deg) and (not req_branch or any(b in c_edu for b in req_branch)):
        return 100.0

    # Rule 2: 80% for same degree level, different branch
    if any(d in c_edu for d in req_deg):
        return 80.0

    # Rule 3: 60% for similar stream (e.g., BCA/BSc for B.Tech CS)
    if "B.TECH" in req_deg and ("BCA" in c_edu or "B.SC" in c_edu) and ("CS" in c_edu or "IT" in c_edu):
        return 60.0

    # Rule 4: 40% for Diploma in a relevant field
    if "DIPLOMA" in c_edu and any(b in c_edu for b in ENGINEERING_BRANCHES):
        return 40.0

    # Rule 5: 20% for 12th pass
    if "12TH" in c_edu or "XII" in c_edu:
        return 20.0

    return 0.0


def location_score(c_city: str, c_state: str, i_city: str, i_state: str) -> float:
    """Calculates location match score."""
    if c_city and i_city and normalize_skill(c_city) == normalize_skill(i_city):
        return 100.0
    if c_state and i_state and normalize_skill(c_state) == normalize_skill(i_state):
        return 66.0
    return 33.0  # Base score for being in the same country


def best_match_for_required_skill(required_skill: str, candidate_skills: List[str]) -> Tuple[float, str]:
    """Finds the best score for a single required skill from a candidate's skill list."""
    req = normalize_skill(required_skill)

    # Non-core skills require an exact match
    if req in NON_CORE_SET:
        return (100.0, req) if req in candidate_skills else (0.0, "")

    # Core skill matching logic
    if req in CORE_LOOKUP:
        req_row2, req_row3_bucket = CORE_LOOKUP[req]
        best_score = 0.0
        best_match_skill = ""

        for cs in candidate_skills:
            if cs == req:
                return 100.0, cs  # 100% for exact match
            if req in cs or cs in req:  # 80% for substring match (e.g., PYTHON vs PYTHON3)
                if best_score < 80.0:
                    best_score = 80.0
                    best_match_skill = cs

            if cs in CORE_LOOKUP:
                cs_row2, cs_row3_bucket = CORE_LOOKUP[cs]
                if cs_row3_bucket == req_row3_bucket:  # 50% for same skill group
                    if best_score < 50.0:
                        best_score = 50.0
                        best_match_skill = cs
                elif cs_row2 == req_row2:  # 10% for same broader category
                    if best_score < 10.0:
                        best_score = 10.0
                        best_match_skill = cs
        return best_score, best_match_skill

    return 0.0, ""


def compute_skills_percent(required_skills: List[str], candidate_skills: List[str], core_weight: float = 0.8) -> float:
    """Aggregates scores for all required skills, weighting core skills higher."""
    if not required_skills:
        return 100.0  # If no skills are required, it's a perfect match

    # normalize required skills and candidate skills
    req_norm = [normalize_skill(s) for s in required_skills]
    cand_norm = [normalize_skill(s) for s in candidate_skills]

    core_req = [s for s in req_norm if skill_is_core(s)]
    non_core_req = [s for s in req_norm if not skill_is_core(s)]

    core_scores = [best_match_for_required_skill(rs, cand_norm)[0] for rs in core_req]
    non_core_scores = [best_match_for_required_skill(rs, cand_norm)[0] for rs in non_core_req]

    avg_core = np.mean(core_scores) if core_scores else 100.0
    avg_non_core = np.mean(non_core_scores) if non_core_scores else 100.0

    # If only one type of skill is required, it gets 100% of the weight
    if not core_req:
        return avg_non_core
    if not non_core_req:
        return avg_core

    return core_weight * avg_core + (1 - core_weight) * avg_non_core


def interest_score(candidate_interest: str, internship_post: str) -> float:
    """Scores candidate's interest against the internship post title."""
    c_int = normalize_skill(candidate_interest)
    i_post = normalize_skill(internship_post)
    if not c_int or not i_post:
        return 0.0
    if i_post in c_int:
        return 100.0  # Exact phrase match

    c_tokens = set(c_int.replace("-", " ").split())
    i_tokens = set(i_post.replace("-", " ").split())
    if c_tokens & i_tokens:
        return 50.0  # Token overlap

    return 25.0  # Fallback for having any interest listed


def overall_score(scores: Dict[str, float], priority_order: List[str]) -> float:
    """Calculates the final weighted score based on priorities."""
    weights = {1: 0.4, 2: 0.3, 3: 0.2, 4: 0.1}
    final_score = 0.0
    for i, criteria in enumerate(priority_order, 1):
        final_score += scores.get(criteria, 0.0) * weights[i]
    return final_score

# ---------------------------------------------------------------------
# --- 4. CORE APPLICATION LOGIC & UI HELPERS ---
# ---------------------------------------------------------------------

def get_diversity_marker(row: pd.Series) -> str:
    """Returns an emoji marker for diversity categories."""
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
        # be defensive: accept list-like or string skills
        c_skills = parse_skills(row.get("skills", ""))

        scores = {
            "skills": compute_skills_percent(internship["skills"], c_skills),
            "education": education_score(str(row.get("education", "")), internship["degree"], internship["branch"]),
            "location": location_score(str(row.get("city", "")), str(row.get("state", "")), internship["city"], internship["state"]),
            "interest": interest_score(str(row.get("interest", "")), internship["post"]) 
        }

        total = overall_score(scores, internship["priority"]) if internship.get("priority") else np.mean(list(scores.values()))

        rows.append({
            "Select": False,
            "Name": row.get("name", ""),
            "Diversity": get_diversity_marker(row),
            "Overall Match %": round(total, 2),
            "Skills %": round(scores["skills"], 2),
            "Education %": round(scores["education"], 2),
            "Location %": round(scores["location"], 2),
            "Interest %": round(scores["interest"], 2),
            "Candidate Skills": ", ".join(c_skills),
            "Education": row.get("education", ""),
        })

    df_ranked = pd.DataFrame(rows).sort_values(by="Overall Match %", ascending=False).reset_index(drop=True)
    df_ranked.index += 1
    df_ranked.insert(1, "Rank", df_ranked.index)

    return df_ranked


def style_top_n(df: pd.DataFrame, n: int):
    """Applies green background styling to the top N rows of a DataFrame."""
    def highlight_top(row: pd.Series):
        try:
            is_top = int(row["Rank"]) <= int(n)
        except Exception:
            is_top = False
        return ["background-color: #e6ffe6" if is_top else "" for _ in row.index]

    return df.style.apply(highlight_top, axis=1).format({
        'Overall Match %': '{:.2f}%',
        'Skills %': '{:.2f}%',
        'Education %': '{:.2f}%',
        'Location %': '{:.2f}%',
        'Interest %': '{:.2f}%',
    })


def internship_card(col, job, key):
    """A helper to display a clickable internship card."""
    with col:
        st.markdown(
            f"""
            <div style="border:1px solid #e0e0e0; border-radius:10px; padding:20px; margin-bottom:10px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); min-height:180px;">
                <h3 style="margin-top:0; margin-bottom:8px;">{job['post']}</h3>
                <p style="color:#666; margin-bottom:12px;"><b>{job['company']}</b> • {job['city']}, {job['state']}</p>
                <p style="font-size:14px; margin-bottom:8px;">
                    <b>Offers:</b> {job['offers']} | <b>Degree:</b> {', '.join(job['degree'])}<br>
                    <b>Branch:</b> {', '.join(job['branch']) if job['branch'] else 'Any'}<br>
                    <b>Skills:</b> {', '.join(job['skills'][:3])}...
                </p>
            </div>
            """, unsafe_allow_html=True
        )
        # Note: use_container_width is not available on all Streamlit versions for st.button - removed for compatibility
        if st.button("Rank Candidates", key=key):
            st.session_state.selected_job_key = key


# ---------------------------------------------------------------------
# --- 5. STREAMLIT UI LAYOUT ---
# ---------------------------------------------------------------------

# --- Sidebar for File Upload ---
with st.sidebar:
    st.title("Configuration")
    st.header("1. Upload Candidates CSV")
    st.caption("Must include: `name`, `education`, `skills`, `city`, `state`. Optional: `interest`, `gender`, `category` (for diversity filters).")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file:
        df_candidates = pd.read_csv(uploaded_file)
        # normalize column names to lowercase so the rest of the code works predictably
        df_candidates.columns = df_candidates.columns.str.lower().str.strip()
        st.success(f"Loaded {len(df_candidates)} candidates!")
    else:
        st.info("Using sample data. Please upload a CSV to analyze your candidates.")
        # Create a sample dataframe if none is uploaded
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
        df_candidates = pd.DataFrame(sample_data)

# --- Main Page ---
st.title("🎓 AI-Powered Internship Matching Engine")
st.markdown("---")

# --- Preset Internship Data (normalize skills for internal matching) ---
PRESET_INTERNSHIPS = [
    {"key": "job1", "post": "AI/ML Intern", "company": "IntelliTech", "offers": 3, "degree": ["B.TECH"], "branch": ["CS", "IT"], "skills": ["AIML", "PYTHON", "DATA ENGINEERING", "MS EXCEL"], "city": "Bengaluru", "state": "Karnataka", "priority": ["skills", "education", "interest", "location"]},
    {"key": "job2", "post": "Web Development Intern", "company": "WebWeavers", "offers": 5, "degree": ["B.TECH", "BCA", "B.SC"], "branch": ["CS", "IT"], "skills": ["JAVASCRIPT", "WEB DEVELOPMENT", "DEVOPS", "COMMUNICATION"], "city": "Pune", "state": "Maharashtra", "priority": ["skills", "education", "location", "interest"]},
    {"key": "job3", "post": "Financial Analyst Intern", "company": "Capital Gains Inc.", "offers": 4, "degree": ["B.COM", "BBA"], "branch": ["ACCOUNTS", "FINANCE"], "skills": ["FINANCIAL ANALYSIS", "FINANCIAL MODELING", "MS EXCEL"], "city": "Mumbai", "state": "Maharashtra", "priority": ["skills", "education", "interest", "location"]},
    {"key": "job4", "post": "Data Science Intern", "company": "DataCorp Analytics", "offers": 3, "degree": ["B.TECH", "B.SC"], "branch": ["CS", "IT"], "skills": ["PYTHON", "SQL", "AIML", "DATA ENGINEERING"], "city": "Chennai", "state": "Tamil Nadu", "priority": ["skills", "education", "interest", "location"]},
    {"key": "job5", "post": "Cybersecurity Intern", "company": "SecureNet Solutions", "offers": 2, "degree": ["B.TECH"], "branch": ["CS", "IT", "ECE"], "skills": ["CYBERSECURITY", "PYTHON", "COMMUNICATION"], "city": "Hyderabad", "state": "Telangana", "priority": ["skills", "education", "location", "interest"]},
    {"key": "job6", "post": "Digital Marketing Intern", "company": "Brand Builders", "offers": 6, "degree": ["B.COM", "BBA", "B.A."], "branch": ["MARKETING", "FINANCE"], "skills": ["SEO", "SOCIAL MEDIA MARKETING", "CONTENT WRITING", "MS EXCEL"], "city": "Delhi", "state": "Delhi", "priority": ["skills", "interest", "education", "location"]},
]

# Normalize preset skills to ensure comparisons are consistent
for j in PRESET_INTERNSHIPS:
    j['skills'] = [normalize_skill(s) for s in j.get('skills', [])]
    j['degree'] = [normalize_skill(d) for d in j.get('degree', [])]
    j['branch'] = [normalize_skill(b) for b in j.get('branch', [])]

# --- App Tabs ---
tab1, tab2 = st.tabs(["**Preset Internships**", "**Create Custom Internship**"])

with tab1:
    st.header("Select a Preset Internship to See Rankings")
    
    # Display cards in rows of 3
    for i in range(0, len(PRESET_INTERNSHIPS), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(PRESET_INTERNSHIPS):
                job = PRESET_INTERNSHIPS[i + j]
                internship_card(cols[j], job, key=job['key'])

    if 'selected_job_key' in st.session_state and st.session_state.selected_job_key:
        job = next((j for j in PRESET_INTERNSHIPS if j['key'] == st.session_state.selected_job_key), None)
        if job:
            st.markdown("---")
            st.subheader(f"Ranking for: {job['post']} at {job['company']}")

            # --- Filtering and Display Logic ---
            df_ranked = compute_ranking(df_candidates, job)

            # Diversity Filters
            st.markdown("**Diversity & Inclusion Filters:**")
            filter_cols = st.columns(3)
            categories = df_candidates['category'].dropna().unique().tolist() if 'category' in df_candidates.columns else []
            genders = df_candidates['gender'].dropna().unique().tolist() if 'gender' in df_candidates.columns else []

            selected_cat = filter_cols[0].multiselect("Filter by Category", options=['SC', 'ST', 'PWD', 'GENERAL'], help="Select one or more categories to filter the list.")
            selected_gen = filter_cols[1].multiselect("Filter by Gender", options=genders, help="Filter by gender.")
            sort_by = filter_cols[2].selectbox("Sort by", options=["Overall Match %", "Skills %", "Education %", "Location %", "Interest %"])

            # Apply filters correctly by matching candidate names
            df_filtered = df_ranked.copy()
            if selected_cat and 'category' in df_candidates.columns:
                allowed_names = df_candidates[df_candidates['category'].isin(selected_cat)]['name'].tolist()
                df_filtered = df_filtered[df_filtered['Name'].isin(allowed_names)]
            if selected_gen and 'gender' in df_candidates.columns:
                allowed_names = df_candidates[df_candidates['gender'].isin(selected_gen)]['name'].tolist()
                df_filtered = df_filtered[df_filtered['Name'].isin(allowed_names)]

            df_filtered = df_filtered.sort_values(by=sort_by, ascending=False).reset_index(drop=True)
            df_filtered["Rank"] = df_filtered.index + 1

            # Display editable dataframe with checkboxes
            edited_df = st.data_editor(
                style_top_n(df_filtered, job['offers']).data,
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select candidates for this internship",
                        default=False,
                    )
                },
                disabled=["Name", "Diversity", "Overall Match %", "Skills %", "Education %", "Location %", "Interest %", "Candidate Skills", "Education", "Rank"],
                hide_index=True,
                use_container_width=True,
                height=600
            )

            # Count selected candidates and provide feedback
            selected_candidates = edited_df[edited_df['Select'] == True]
            num_selected = len(selected_candidates)
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Selected Candidates", f"{num_selected}/{job['offers']}")
            with col2:
                if num_selected > job['offers']:
                    st.error(f"⚠️ Too many selected! Limit: {job['offers']}")
                elif num_selected == 0:
                    st.info("ℹ️ No candidates selected yet")
                else:
                    st.success(f"✅ {num_selected} candidates selected")

            # Submit button
            if st.button("Submit Selections", key=f"submit_{job['key']}"):
                if num_selected > job['offers']:
                    st.error(f"Error: You can only select up to {job['offers']} candidates.")
                elif num_selected == 0:
                    st.warning("Please select at least one candidate.")
                else:
                    st.success("Selections Submitted!")
                    st.balloons()
                    st.write(f"**Selected Candidates for {job['post']}:**")
                    for _, candidate in selected_candidates.iterrows():
                        st.write(f"- {candidate['Name']} (Match: {candidate['Overall Match %']}%)")


with tab2:
    st.header("Define a Custom Internship Role")
    with st.form("custom_internship_form"):
        col1, col2 = st.columns(2)
        with col1:
            post = st.text_input("Internship Post Title", "Data Science Intern")
            company = st.text_input("Company Name", "Future Corp")
            offers = st.number_input("Number of Offers (N)", min_value=1, value=5)
            city = st.text_input("City", "Hyderabad")
            state = st.selectbox("State", options=INDIAN_STATES, index=INDIAN_STATES.index("Telangana"))

        with col2:
            degree = st.multiselect("Required Degree(s)", options=BACHELORS_DEGREES, default=["B.TECH"])
            branch = st.multiselect("Required Branch(es)", options=ALL_BRANCHES, default=["CS", "IT"])
            skills = st.multiselect("Required Skills", options=ALL_SKILLS_LIST, default=["PYTHON", "AIML", "SQL", "COMMUNICATION"])

        st.markdown("**Set Matching Priorities**")
        p_cols = st.columns(4)
        options = ["skills", "education", "location", "interest"]
        p1 = p_cols[0].selectbox("Priority 1 (Weight: 0.4)", options, index=0)
        p2 = p_cols[1].selectbox("Priority 2 (Weight: 0.3)", [o for o in options if o != p1], index=0)
        p3 = p_cols[2].selectbox("Priority 3 (Weight: 0.2)", [o for o in options if o not in [p1, p2]], index=0)
        p4 = p_cols[3].selectbox("Priority 4 (Weight: 0.1)", [o for o in options if o not in [p1, p2, p3]], index=0)

        submitted = st.form_submit_button("Compute Custom Ranking", use_container_width=True)

    if submitted:
        custom_job = {
            "post": post,
            "company": company,
            "offers": offers,
            "degree": [normalize_skill(d) for d in degree],
            "branch": [normalize_skill(b) for b in branch],
            "skills": [normalize_skill(s) for s in skills],
            "city": city,
            "state": state,
            "priority": [p1, p2, p3, p4]
        }
        st.markdown("---")
        st.subheader(f"Custom Ranking for: {custom_job['post']} at {custom_job['company']}")

        # Re-use the same filtering and display logic
        df_ranked = compute_ranking(df_candidates, custom_job)

        st.markdown("**Diversity & Inclusion Filters:**")
        filter_cols = st.columns(3)
        categories = df_candidates['category'].dropna().unique().tolist() if 'category' in df_candidates.columns else []
        genders = df_candidates['gender'].dropna().unique().tolist() if 'gender' in df_candidates.columns else []

        selected_cat_custom = filter_cols[0].multiselect("Filter by Category", options=['SC', 'ST', 'PWD', 'GENERAL'], key="custom_cat")
        selected_gen_custom = filter_cols[1].multiselect("Filter by Gender", options=genders, key="custom_gen")
        sort_by_custom = filter_cols[2].selectbox("Sort by", options=["Overall Match %", "Skills %", "Education %", "Location %", "Interest %"], key="custom_sort")

        df_filtered_custom = df_ranked.copy()
        if selected_cat_custom and 'category' in df_candidates.columns:
            allowed_names = df_candidates[df_candidates['category'].isin(selected_cat_custom)]['name'].tolist()
            df_filtered_custom = df_filtered_custom[df_filtered_custom['Name'].isin(allowed_names)]
        if selected_gen_custom and 'gender' in df_candidates.columns:
            allowed_names = df_candidates[df_candidates['gender'].isin(selected_gen_custom)]['name'].tolist()
            df_filtered_custom = df_filtered_custom[df_filtered_custom['Name'].isin(allowed_names)]

        df_filtered_custom = df_filtered_custom.sort_values(by=sort_by_custom, ascending=False).reset_index(drop=True)
        df_filtered_custom["Rank"] = df_filtered_custom.index + 1

        # Display editable dataframe with checkboxes
        edited_df_custom = st.data_editor(
            style_top_n(df_filtered_custom, custom_job['offers']).data,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select candidates for this internship",
                    default=False,
                )
            },
            disabled=["Name", "Diversity", "Overall Match %", "Skills %", "Education %", "Location %", "Interest %", "Candidate Skills", "Education", "Rank"],
            hide_index=True,
            use_container_width=True,
            height=600,
            key="custom_data_editor"
        )

        # Count selected candidates and provide feedback
        selected_candidates_custom = edited_df_custom[edited_df_custom['Select'] == True]
        num_selected_custom = len(selected_candidates_custom)
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Selected Candidates", f"{num_selected_custom}/{custom_job['offers']}")
        with col2:
            if num_selected_custom > custom_job['offers']:
                st.error(f"⚠️ Too many selected! Limit: {custom_job['offers']}")
            elif num_selected_custom == 0:
                st.info("ℹ️ No candidates selected yet")
            else:
                st.success(f"✅ {num_selected_custom} candidates selected")

        # Submit button
        if st.button("Submit Selections", key="submit_custom"):
            if num_selected_custom > custom_job['offers']:
                st.error(f"Error: You can only select up to {custom_job['offers']} candidates.")
            elif num_selected_custom == 0:
                st.warning("Please select at least one candidate.")
            else:
                st.success("Selections Submitted!")
                st.balloons()
                st.write(f"**Selected Candidates for {custom_job['post']}:**")
                for _, candidate in selected_candidates_custom.iterrows():
                    st.write(f"- {candidate['Name']} (Match: {candidate['Overall Match %']}%)")


# --- Footer ---
with st.expander("ℹ️ How Scoring Works"):
    st.markdown("""
    - **Overall Score**: A weighted sum based on the four criteria. Default weights are **P1 (0.4), P2 (0.3), P3 (0.2), P4 (0.1)**.
    - **Skills (80% weight in skill score)**: 
        - `100%`: Exact skill match.
        - `80%`: Substring match (e.g., 'PYTHON' vs 'PYTHON3').
        - `50%`: Same skill group (e.g., AIML vs WEB DEVELOPMENT under Computer Engineering).
        - `10%`: Same broad category (e.g., a Computer Engineering skill vs an Electrical Engineering skill).
    - **Non-Core Skills (20% weight in skill score)**: `100%` for an exact match, `0%` otherwise.
    - **Education**: Scored hierarchically from `100%` (exact degree+branch) down to `20%` (12th pass).
    - **Location**: `100%` for city match, `66%` for state match, `33%` for same country.
    - **Interest**: `100%` if the internship title is in the candidate's interest field, `50%` for keyword overlap.
    - **Diversity Markers**: `♀️` (Female), `♿` (PWD), `🔵` (SC), `🔴` (ST).
    """)