import streamlit as st
import pandas as pd
import json

students_df = pd.read_csv("students.csv")
orgs_df = pd.read_csv("organizations.csv")

# Load rules JSON
with open("rules.json", "r") as f:
    rules = json.load(f)

def extract_features(student, org_rules):
    student_skills = set(str(student['skills']).split(';'))
    features = {
        "degree_match": int(
            student['degree'].strip().lower() == org_rules.get("degree_required", "").lower()
        ),
        "compulsory_skills_met": int(
            set(org_rules.get("compulsory_skills", [])) <= student_skills
        ),
        "optional_skills_count": len(
            set(org_rules.get("optional_skills", [])) & student_skills
        ),
        "gpa": float(student['gpa']),
        "location_match": int(
            org_rules.get("location") is not None
            and str(student['location_pref']).strip().lower() == str(org_rules.get("location", "")).lower()
        ),
        "past_participation": int(str(student['past_participation']).lower() == "yes"),
        "age": int(student['age']),
        "category": str(student['category']).upper()
    }
    return features

def score_candidate(student, org_rules, method="rules", model=None):
    features = extract_features(student, org_rules)

    if method == "rules":
        weights = org_rules.get("weights", {})
        score_val = 0
        score_val += features["degree_match"] * weights.get("degree", 0)
        score_val += features["optional_skills_count"] * weights.get("skills", 0)
        score_val += features["location_match"] * weights.get("location", 0)
        score_val += features["gpa"] * weights.get("gpa", 0)
        score_val += features["past_participation"] * weights.get("past_participation", 0)
        return score_val

    elif method == "ml" and model is not None:
        X = pd.DataFrame([features])
        return model.predict_proba(X)[0][1]

    else:
        raise ValueError("Invalid scoring method")


def rank_candidates(org, students, method="rules", model=None):
    org_name = org['org_name']
    if org_name not in rules:
        st.warning(f"No rules defined for {org_name} in rules.json")
        return pd.DataFrame()

    r = rules[org_name]

    students = students.copy()
    students['score'] = students.apply(
        lambda row: score_candidate(row, r, method=method, model=model), axis=1
    )

    def hard_filter(student):
        if r.get("degree_required") and student['degree'].strip().lower() != r["degree_required"].lower():
            return False
        if r.get("age_range") and not (r["age_range"][0] <= int(student['age']) <= r["age_range"][1]):
            return False
        if r.get("location") and str(student['location_pref']).strip().lower() != r["location"].lower():
            return False
        if r.get("compulsory_skills"):
            student_skills = set(str(student['skills']).split(';'))
            if not set(r["compulsory_skills"]).issubset(student_skills):
                return False
        if r.get("min_gpa") and float(student['gpa']) < r["min_gpa"]:
            return False
        return True

    students = students[students.apply(hard_filter, axis=1)]
    ranked = students.sort_values(by=['score', 'gpa'], ascending=[False, False])
    return ranked


st.title("Internship Allocation System (ML-Ready)")

for _, org in orgs_df.iterrows():
    with st.container():
        st.subheader(org['org_name'])
        st.write(f"**Sector:** {org['sector']}")
        st.write(f"**Location:** {org['location']}")
        st.write(f"**Degree Required:** {org['degree']}")
        st.write(f"**Required Skills:** {org['required_skills']}")
        st.write(f"**Total Openings:** {org['no_of_openings']}")
        st.write(f"**Female Reserved:** {org['female_openings']}")
        st.write(f"**Category Preference:** {org['category_pref']}")

        if st.button(f"Rank Candidates for {org['org_name']}", key=org['org_id']):
            candidates = rank_candidates(org, students_df, method="rules")

            if candidates.empty:
                st.error(f"No eligible candidates for {org['org_name']}")
                continue

            openings = int(org['no_of_openings'])
            female_openings = int(org['female_openings'])
            allocated = pd.DataFrame()

            org_rules = rules[org['org_name']]
            special_lists = org_rules.get("special_lists", {})

            # GREENFUTURE ALLOCATION 
            if "category_openings" in special_lists:
                category_openings = special_lists.get("category_openings", {})
                # 1️⃣ Allocate by categories first
                for cat, num in category_openings.items():
                    cat_candidates = candidates[
                        (candidates['category'].str.upper() == cat.upper()) & 
                        (~candidates.index.isin(allocated.index))
                    ]
                    cat_alloc = cat_candidates.head(num*3).copy()
                    cat_alloc['status'] = f"Allocated - {cat.upper()}"
                    allocated = pd.concat([allocated, cat_alloc])
                    st.write(f"### {cat.upper()} Merit List")
                    st.dataframe(cat_alloc[['student_id', 'name', 'gender', 'age', 'degree',
                                            'skills', 'score', 'gpa', 'category','past_participation','status']])
                    cat_alloc.to_csv(f"{org['org_id']}_{cat.upper()}_allocations.csv", index=False)

                remaining_candidates = candidates[~candidates.index.isin(allocated.index)]
                female_candidates = remaining_candidates[remaining_candidates['gender'] == 'F']
                female_alloc = female_candidates.head(female_openings*3).copy()
                female_alloc['status'] = "Allocated - Female"
                allocated = pd.concat([allocated, female_alloc])

                remaining_candidates = candidates[~candidates.index.isin(allocated.index)]
                general_alloc = remaining_candidates.head((openings - len(allocated))*3).copy()
                general_alloc['status'] = "Allocated - General"
                allocated = pd.concat([allocated, general_alloc])

                st.write("### Female Merit List")
                st.dataframe(female_alloc[['student_id', 'name', 'gender', 'age', 'degree',
                                           'skills', 'score', 'gpa', 'category','past_participation', 'status']])

                st.write("### General Merit List")
                st.dataframe(general_alloc[['student_id', 'name', 'gender', 'age', 'degree',
                                            'skills', 'score', 'gpa','category','past_participation','status']])
                
                st.success(f"Saved allocations for {org['org_name']} as CSVs!")

            else:
                female_candidates = candidates[candidates['gender'] == 'F']
                female_alloc = female_candidates.head(female_openings * 3).copy()
                female_alloc['status'] = "Allocated - Female"
                allocated = pd.concat([allocated, female_alloc])

                remaining_candidates = candidates.drop(allocated.index)
                general_alloc = remaining_candidates.head(openings * 3).copy()
                general_alloc['status'] = "Allocated - General"
                allocated = pd.concat([allocated, general_alloc])

                if "general_sc" in special_lists:
                    sc_candidates = candidates[candidates['category'].str.upper() == 'SC']
                    sc_alloc = sc_candidates.head(openings * 3).copy()
                    sc_alloc['status'] = "Allocated - General SC"
                    allocated = pd.concat([allocated, sc_alloc])
                    st.write("### General SC Merit List")
                    st.dataframe(sc_alloc[['student_id', 'name', 'gender', 'age', 'degree',
                                           'skills', 'score', 'gpa', 'category','past_participation','status']])
                    sc_alloc.to_csv(f"{org['org_id']}_general_sc_allocations.csv", index=False)


                # Display
                st.write("### Female Merit List")
                st.dataframe(female_alloc[['student_id', 'name', 'gender', 'age', 'degree',
                                           'skills', 'score', 'gpa','category','past_participation','status']])

                st.write("### General Merit List")
                st.dataframe(general_alloc[['student_id', 'name', 'gender', 'age', 'degree',
                                            'skills', 'score', 'gpa','category','past_participation', 'status']])

                female_alloc.to_csv(f"{org['org_id']}_female_allocations.csv", index=False)
                general_alloc.to_csv(f"{org['org_id']}_general_allocations.csv", index=False)

                allocated_ids = set(allocated.index)
                
                all_candidates = candidates.copy()
                all_candidates['status'] = all_candidates.index.map(
                    lambda idx: allocated.loc[idx, 'status'] if idx in allocated_ids else "Not Selected"
                )

                all_candidates.to_csv(
                    f"{org['org_id']}_all_candidates.csv", index=False
                )

                st.success(f"Saved full candidate list (including not selected) for {org['org_name']}")

