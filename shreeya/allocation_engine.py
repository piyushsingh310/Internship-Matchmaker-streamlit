import pandas as pd
import random

# Load data
students = pd.read_csv("students.csv")
orgs = pd.read_csv("organizations.csv")

# Configurable weights (GPA removed from scoring)
WEIGHTS = {
    "degree": 2,
    "skill": 3,
    "location": 2
}

allocations = []

def calculate_score(student, org):
    score = 0
    reasons = []
    max_score = 0

    # Degree match
    max_score += WEIGHTS["degree"]
    if student["degree"] == org["degree"]:
        score += WEIGHTS["degree"]
        reasons.append("Degree matched")
    else:
        reasons.append("Degree not matched")

    # Skill match
    student_skills = set(student["skills"].split(";"))
    org_skills = set(org["required_skills"].split(";"))
    skill_overlap = student_skills.intersection(org_skills)
    score += len(skill_overlap) * WEIGHTS["skill"]
    max_score += len(org_skills) * WEIGHTS["skill"]
    if skill_overlap:
        reasons.append(f"Skills matched: {', '.join(sorted(skill_overlap))}")
    else:
        reasons.append("No skill overlap")

    # Location preference
    max_score += WEIGHTS["location"]
    if student["location_pref"] == org["location"]:
        score += WEIGHTS["location"]
        reasons.append("Location matched")
    else:
        reasons.append("Location not matched")

    # Past participation penalty
    if student["past_participation"] == "Yes":
        score *= 0.9
        reasons.append("Past participation penalized")

    # Normalize score
    normalized = score / max_score if max_score > 0 else 0

    return normalized, "; ".join(reasons)


# Allocation logic
for _, org in orgs.iterrows():
    candidates = []

    # Evaluate all students
    for _, student in students.iterrows():
        score, reasons = calculate_score(student, org)
        candidates.append({
            "student_id": student["student_id"],
            "student_name": student["name"],
            "org_id": org["org_id"],
            "org_name": org["org_name"],
            "score": score,
            "gpa": student.get("gpa", 0),  # kept only for tie-break
            "reason": reasons,
            "gender": student["gender"]
        })

    # Sort: score → GPA (only as tie-breaker) → random
    candidates = sorted(
        candidates,
        key=lambda x: (
            -x["score"],
            -x["gpa"],  # only applies if scores are equal
            random.random()
        )
    )

    # Female quota allocation
    female_quota = int(org.get("female_openings", 0))
    female_allocated = [c for c in candidates if c["gender"] == "F"][:female_quota]

    # Remove allocated females from pool
    remaining_candidates = [c for c in candidates if c not in female_allocated]

    # Fill remaining seats
    other_allocated = remaining_candidates[: org["no_of_openings"] - len(female_allocated)]

    allocated = female_allocated + other_allocated
    not_allocated = [c for c in candidates if c not in allocated]

    # Mark statuses
    for c in allocated:
        c["status"] = "Allocated"
        allocations.append(c)
    for c in not_allocated:
        c["status"] = "Not Allocated"
        allocations.append(c)


# Save results
df_allocations = pd.DataFrame(allocations)
df_allocations["score"] = df_allocations["score"].round(4)  # round only in output
df_allocations.to_csv("allocations.csv", index=False)

print("✅ Allocation completed (GPA only used for tie-breaks)!")