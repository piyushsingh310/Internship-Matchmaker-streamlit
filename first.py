import pandas as pd
import streamlit as st
import numpy as np

# --- 1. Data Models ---
# A simple way to represent a Candidate and an Internship offer
# In a real-world scenario, you might use classes or a database.

# Sample data structure for a candidate
# The actual data will be loaded from the CSV.
candidate_template = {
    'name': '',
    'education': '', # e.g., 'B.Tech in CS', 'B.Tech in IT', 'BCA', 'Diploma'
    'skills': [], # e.g., ['AIML', 'WEBDEV', 'Communication Skills']
    'location': '', # e.g., 'Mumbai', 'Pune', 'Delhi'
    'state': '', # e.g., 'Maharashtra', 'Delhi'
}

# Sample data structure for an internship
# We'll create a list of these for the app.
internship_template = {
    'post': '',
    'company': '',
    'offers': 0,
    'education_req': '',
    'skills_req': [],
    'location_req': '',
    'criteria_priority': {} # e.g., {'skills': 0.4, 'education': 0.3, 'location': 0.2}
}

# Skill tree structure for the skills matching logic
SKILL_TREE = {
    'core': {
        'engineering': {
            'comp_engineering': ['AIML', 'WEBDEV', 'APPDEV', 'CYBER SECURITY'],
            'mechanical_engineering': ['CAD', 'Robotics'],
            # ... add other engineering fields
        },
        'medical': ['Biotechnology', 'Pharmacology'],
        'law': ['Corporate Law', 'Criminal Law'],
        # ... add other core fields
    },
    'non_core': ['Communication Skills', 'Typing Skills', 'Maths Skills', 'Word Excel Skills']
}

# --- 2. Matching Engine Functions ---

def calculate_location_match(candidate_loc, internship_loc):
    """
    Calculates the location match percentage based on the user's criteria.
    """
    candidate_state = candidate_loc.get('state', '').lower()
    internship_state = internship_loc.get('state', '').lower()
    candidate_city = candidate_loc.get('city', '').lower()
    internship_city = internship_loc.get('city', '').lower()
    
    if candidate_city == internship_city:
        return 100
    elif candidate_state == internship_state:
        return 66
    else:
        return 33

def calculate_education_match(candidate_edu, internship_edu_req):
    """
    Calculates the education match percentage based on the user's criteria.
    """
    candidate_edu_lower = candidate_edu.lower()
    internship_edu_req_lower = internship_edu_req.lower()

    if candidate_edu_lower == internship_edu_req_lower:
        return 100
    elif 'btech' in candidate_edu_lower and 'btech' in internship_edu_req_lower:
        # B.Tech in IT vs B.Tech in CS
        return 80
    elif ('bca' in candidate_edu_lower or 'bsc' in candidate_edu_lower) and ('science' in internship_edu_req_lower or 'btech' in internship_edu_req_lower):
        # Science stream match
        return 60
    elif 'diploma' in candidate_edu_lower:
        return 40
    elif '12th pass' in candidate_edu_lower:
        return 20
    else:
        return 0

def calculate_skills_match(candidate_skills, internship_skills_req):
    """
    Calculates the skills match percentage based on the tree structure and rules.
    This will require careful implementation of the skill tree logic.
    """
    core_skill_match_scores = []
    non_core_skill_match_scores = []

    # Map skills to their tiers (row 1, 2, 3)
    skill_tiers = {}
    for r1, val1 in SKILL_TREE['core'].items():
        if isinstance(val1, list):
            for skill in val1:
                skill_tiers[skill] = {'row': 1, 'path': [r1]}
        else:
            for r2, val2 in val1.items():
                if isinstance(val2, list):
                    for skill in val2:
                        skill_tiers[skill] = {'row': 2, 'path': [r1, r2]}
                else:
                    for r3, val3 in val2.items():
                         for skill in val3:
                            skill_tiers[skill] = {'row': 3, 'path': [r1, r2, r3]}

    # Iterate through each required skill and find a match
    for req_skill in internship_skills_req:
        req_skill_lower = req_skill.lower()
        is_core_skill = req_skill in SKILL_TREE['core'].values()

        match_found = False
        if is_core_skill:
            for cand_skill in candidate_skills:
                cand_skill_lower = cand_skill.lower()
                
                if req_skill_lower == cand_skill_lower:
                    core_skill_match_scores.append(100)
                    match_found = True
                    break
                
                # Fuzzy matching can be used here for partial matches, e.g., using a library like TheFuzz.
                # For this rule-based system, let's use the row-based logic
                if cand_skill in skill_tiers and req_skill in skill_tiers:
                    cand_path = skill_tiers[cand_skill]['path']
                    req_path = skill_tiers[req_skill]['path']
                    
                    if len(cand_path) >= 3 and cand_path[2] == req_path[2]:
                        core_skill_match_scores.append(50)
                        match_found = True
                        break
                    elif len(cand_path) >= 2 and cand_path[1] == req_path[1]:
                        core_skill_match_scores.append(10)
                        match_found = True
                        break

            if not match_found:
                core_skill_match_scores.append(0)
        
        else: # Non-core skills
            if req_skill_lower in [s.lower() for s in candidate_skills]:
                non_core_skill_match_scores.append(100)
            else:
                non_core_skill_match_scores.append(0)

    # Calculate final skills percentage
    total_skills_score = 0
    # You mentioned core skills get "way more priority". Let's assign a 0.8 weight to core and 0.2 to non-core for their sum.
    if core_skill_match_scores:
        total_skills_score += np.mean(core_skill_match_scores) * 0.8
    if non_core_skill_match_scores:
        total_skills_score += np.mean(non_core_skill_match_scores) * 0.2
    
    return total_skills_score

def calculate_final_match(location_match, education_match, skills_match, priority_weights):
    """
    Calculates the final weighted score for a candidate.
    """
    final_score = (
        (location_match * priority_weights.get('location', 0)) +
        (education_match * priority_weights.get('education', 0)) +
        (skills_match * priority_weights.get('skills', 0))
    )
    return final_score

# --- 3. Streamlit App ---

st.title("Al-Based Smart Allocation Engine for PM Internship Scheme")
st.markdown("---")

st.header("Upload Candidate Data")
uploaded_file = st.file_uploader("Upload a CSV file with candidate data", type=["csv"])

candidates_df = None
if uploaded_file is not None:
    try:
        candidates_df = pd.read_csv(uploaded_file)
        st.success("Candidate data uploaded successfully!")
        st.dataframe(candidates_df)
    except Exception as e:
        st.error(f"Error loading file: {e}")

if candidates_df is not None:
    st.markdown("---")
    st.header("Pre-set Internship Offers")

    # Define some dummy internship offers
    dummy_internships = [
        {
            'post': 'AI/ML Intern',
            'company': 'Tech Solutions Inc.',
            'offers': 3,
            'education_req': 'B.Tech in CS',
            'skills_req': ['AIML', 'Python', 'Communication Skills'],
            'location_req': 'Mumbai',
            'criteria_priority': {'skills': 0.4, 'education': 0.3, 'location': 0.2}
        },
        {
            'post': 'Web Development Intern',
            'company': 'Digital Growth Ltd.',
            'offers': 2,
            'education_req': 'B.Tech in IT',
            'skills_req': ['WEBDEV', 'Word Excel Skills'],
            'location_req': 'Bangalore',
            'criteria_priority': {'skills': 0.4, 'education': 0.3, 'location': 0.2}
        }
        # You can add more dummy internships here
    ]

    for internship in dummy_internships:
        with st.expander(f"**{internship['post']}** at **{internship['company']}**"):
            st.write(f"**Number of offers:** {internship['offers']}")
            st.write(f"**Required Education:** {internship['education_req']}")
            st.write(f"**Required Skills:** {', '.join(internship['skills_req'])}")
            st.write(f"**Location:** {internship['location_req']}")
            
            # --- Perform the matching and ranking ---
            ranked_candidates = []
            for _, candidate in candidates_df.iterrows():
                location_match = calculate_location_match(
                    {'city': candidate['location'], 'state': candidate['state']}, 
                    {'city': internship['location_req'], 'state': 'Maharashtra' if internship['location_req'] == 'Mumbai' else 'Karnataka' } # This part needs refinement for general locations
                )
                education_match = calculate_education_match(candidate['education'], internship['education_req'])
                
                # Assuming 'skills' is a comma-separated string in the CSV
                candidate_skills_list = [s.strip() for s in candidate['skills'].split(',')]
                skills_match = calculate_skills_match(candidate_skills_list, internship['skills_req'])
                
                final_score = calculate_final_match(location_match, education_match, skills_match, internship['criteria_priority'])
                
                ranked_candidates.append({
                    'name': candidate['name'],
                    'final_score': final_score,
                    'location_match': location_match,
                    'education_match': education_match,
                    'skills_match': skills_match
                })

            # Sort and display the ranking
            ranked_candidates_df = pd.DataFrame(ranked_candidates).sort_values(by='final_score', ascending=False).reset_index(drop=True)
            ranked_candidates_df.index += 1
            
            st.subheader("Candidate Rankings")
            st.dataframe(ranked_candidates_df)

            # Highlight the top 'n' candidates
            top_n = internship['offers']
            st.markdown(f"**Top {top_n} candidates (highlighted in green):**")
            
            # This is a bit complex to do directly in a Streamlit table. A workaround is to display a separate table.
            top_candidates_df = ranked_candidates_df.head(top_n).style.apply(lambda x: ['background-color: #d4edda'] * len(x))
            st.dataframe(top_candidates_df)

            st.markdown("---")
            st.subheader("Filter Rankings")
            filter_option = st.selectbox("View rankings by:", ["Final Score", "Skills %", "Education %", "Location %"], key=f"filter_{internship['post']}")
            
            if filter_option == "Skills %":
                st.dataframe(ranked_candidates_df.sort_values(by='skills_match', ascending=False).reset_index(drop=True))
            elif filter_option == "Education %":
                st.dataframe(ranked_candidates_df.sort_values(by='education_match', ascending=False).reset_index(drop=True))
            elif filter_option == "Location %":
                st.dataframe(ranked_candidates_df.sort_values(by='location_match', ascending=False).reset_index(drop=True))
            else:
                st.dataframe(ranked_candidates_df)

    st.markdown("---")
    st.header("Add Custom Internship Post")
    
    with st.form("custom_internship_form"):
        post_name = st.text_input("Internship Post Name")
        company_name = st.text_input("Company Name")
        num_offers = st.number_input("Number of offers", min_value=1, step=1)
        education_req = st.text_input("Required Degree (e.g., B.Tech in CS)")
        skills_req = st.multiselect("Required Skills", list(SKILL_TREE['core']['engineering']['comp_engineering']) + SKILL_TREE['non_core'])
        location_req = st.text_input("Location of posting (City)")
        
        st.subheader("Set Criteria Priorities")
        
        # This part requires some careful UI design for the weights
        st.info("Assign weights that sum up to 1 (e.g., 0.4, 0.3, 0.2)")
        skills_weight = st.slider("Skills Weight", 0.0, 1.0, 0.4, 0.1)
        education_weight = st.slider("Education Weight", 0.0, 1.0, 0.3, 0.1)
        location_weight = st.slider("Location Weight", 0.0, 1.0, 0.2, 0.1)
        
        submitted = st.form_submit_button("Generate Rankings")

        if submitted:
            # Check if weights sum to 1 (or close to it due to floating point precision)
            if abs(skills_weight + education_weight + location_weight - 1.0) > 0.01:
                st.error("The sum of weights must be close to 1.")
            else:
                custom_internship = {
                    'post': post_name,
                    'company': company_name,
                    'offers': num_offers,
                    'education_req': education_req,
                    'skills_req': skills_req,
                    'location_req': location_req,
                    'criteria_priority': {
                        'skills': skills_weight,
                        'education': education_weight,
                        'location': location_weight
                    }
                }
                
                # --- Perform the matching and ranking for custom post ---
                ranked_candidates = []
                for _, candidate in candidates_df.iterrows():
                    location_match = calculate_location_match(
                        {'city': candidate['location'], 'state': candidate['state']}, 
                        {'city': custom_internship['location_req'], 'state': 'Unknown'} # This needs a proper way to get the state from the city
                    )
                    education_match = calculate_education_match(candidate['education'], custom_internship['education_req'])
                    candidate_skills_list = [s.strip() for s in candidate['skills'].split(',')]
                    skills_match = calculate_skills_match(candidate_skills_list, custom_internship['skills_req'])
                    final_score = calculate_final_match(location_match, education_match, skills_match, custom_internship['criteria_priority'])
                    
                    ranked_candidates.append({
                        'name': candidate['name'],
                        'final_score': final_score,
                        'location_match': location_match,
                        'education_match': education_match,
                        'skills_match': skills_match
                    })
                
                ranked_candidates_df = pd.DataFrame(ranked_candidates).sort_values(by='final_score', ascending=False).reset_index(drop=True)
                ranked_candidates_df.index += 1
                
                st.subheader(f"Rankings for '{post_name}'")
                st.dataframe(ranked_candidates_df)
                
                top_n = custom_internship['offers']
                st.markdown(f"**Top {top_n} candidates (highlighted in green):**")
                
                top_candidates_df = ranked_candidates_df.head(top_n).style.apply(lambda x: ['background-color: #d4edda'] * len(x))
                st.dataframe(top_candidates_df)   