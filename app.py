import streamlit as st
import requests
import pdfplumber
import pandas as pd
import urllib.parse
import re

JOB_ROLES = [
    "Software Developer", "Data Scientist", "Data Analyst", "Product Manager", "Project Manager",
    "UI/UX Designer", "DevOps Engineer", "QA Engineer", "Business Analyst", "Machine Learning Engineer",
    "Full Stack Developer", "Backend Developer", "Frontend Developer"
]
LOCATIONS = [
    "Meerut", "Noida", "Gurugram", "Bengaluru", "Hyderabad", "Pune", "Mumbai",
    "Chennai", "Delhi", "Anywhere in India"
]
SKILLS_DB = [
    # Programming Languages
    'python', 'java', 'c#', 'c++', 'c', 'javascript', 'js', 'typescript', 'ts', 'php', 'ruby', 'go', 'golang', 'swift', 'kotlin', 'rust', 'scala',
    # Web Frameworks (Backend)
    'django', 'flask', 'spring', 'spring boot', 'nodejs', 'node.js', 'express', 'expressjs', 'ruby on rails',
    # Web Frameworks (Frontend)
    'react', 'reactjs', 'react.js', 'angular', 'angularjs', 'vue', 'vuejs', 'vue.js', 'svelte',
    # Databases & Caching
    'sql', 'mysql', 'postgresql', 'postgres', 'mssql', 'sqlite', 'mongodb', 'mongo', 'nosql', 'redis', 'elasticsearch', 'cassandra', 'graphql',
    # Cloud & DevOps
    'aws', 'amazon web services', 'azure', 'microsoft azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s', 'terraform', 'ansible',
    'jenkins', 'ci/cd', 'ci-cd', 'git', 'github', 'gitlab', 'devops',
    # Data Science & Machine Learning
    'machine learning', 'ml', 'deep learning', 'artificial intelligence', 'ai', 'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn',
    'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'data analysis', 'data analytics', 'natural language processing', 'nlp', 'computer vision',
    # Big Data
    'big data', 'hadoop', 'spark', 'apache spark', 'kafka', 'apache kafka', 'data engineering',
    # General Software Engineering & Methodologies
    'data structures', 'algorithms', 'api', 'rest', 'restful', 'microservices', 'agile', 'scrum', 'testing', 'qa', 'automation'
]


@st.cache_data
def get_jobs_from_api(query, location, internship_only, entry_level_only, page=1):
    url = "https://jsearch.p.rapidapi.com/search"
    api_key = st.secrets.get("JSEARCH_API_KEY")
    if not api_key:
        st.error("JSearch API key not found. Please add it to your .streamlit/secrets.toml file.")
        return []

    if entry_level_only:
        query = f"{query} entry level fresher"

    employment_types = []
    if internship_only:
        employment_types.append("INTERN")
    if entry_level_only and not internship_only:
        employment_types.append("FULLTIME")

    headers = {"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"}
    params = {"query": f"{query} in {location}", "page": str(page)}
    if employment_types:
        params["employment_types"] = ",".join(employment_types)

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        results = response.json().get("data", [])
        jobs = []
        for job in results:
            jobs.append({
                "title": job.get("job_title", "N/A"), "company": job.get("employer_name", "N/A"),
                "description": job.get("job_description", "No description provided."),
                "link": job.get("job_apply_link", "#")
            })
        return jobs
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching jobs from JSearch API: {e}")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return []

def extract_skills(text, skills_list):
    """Extracts skills with special, stricter rules for common false positives."""
    found_skills = set()
    for skill in skills_list:
        pattern = r'\b' + re.escape(skill) + r'\b'
        # General case-insensitive search
        if re.search(pattern, text, re.IGNORECASE):
            
            if skill.lower() in ['sql', 'api']:

                uppercase_pattern = r'\b' + skill.upper() + r'\b'
                if not re.search(uppercase_pattern, text):
                    continue # Skip this skill if it's not found in ALL CAPS
            
            # Normalize skill names before adding to the set
            if skill.lower() in ['js', 'javascript']:
                found_skills.add('Javascript')
            elif skill.lower() in ['aws', 'amazon web services']:
                found_skills.add('AWS')
            elif skill.lower() in ['gcp', 'google cloud']:
                found_skills.add('GCP')
            else:
                found_skills.add(skill.title())
    return found_skills

# UI
st.set_page_config(page_title="Resume-to-Job  System", layout="wide")
st.title("🔍 Resume to Job Matching  System")
st.markdown("Select a role and location, upload your resume, and click 'Find Jobs' to start.")

if 'page' not in st.session_state: st.session_state.page = 1
if 'jobs' not in st.session_state: st.session_state.jobs = []
if 'resume_text' not in st.session_state: st.session_state.resume_text = ""

col1, col2 = st.columns(2)
with col1:
    job_query = st.selectbox("Select your desired job role:", options=JOB_ROLES)
with col2:
    default_location_index = LOCATIONS.index("Meerut") if "Meerut" in LOCATIONS else 0
    job_location = st.selectbox("Select a location:", options=LOCATIONS, index=default_location_index)

st.markdown("#### Job Type Filters")
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    is_internship = st.checkbox("Show Internships only")
with filter_col2:
    is_entry_level = st.checkbox("Show Entry-Level / Fresher roles only")

uploaded_file = st.file_uploader("Upload your resume (PDF format only):", type=["pdf"])

if st.button("Find Matching Jobs"):
    if uploaded_file is None:
        st.error("Please upload your resume first!")
    else:
        with st.spinner("Analyzing your resume and fetching the first page of jobs..."):
            st.session_state.page = 1
            st.session_state.jobs = []
            
            try:
                resume_text = ""
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text: resume_text += text + "\n"
                st.session_state.resume_text = resume_text
            except Exception as e:
                st.error(f"Error parsing PDF: {e}")
                st.stop()
            
            initial_jobs = get_jobs_from_api(job_query, job_location, is_internship, is_entry_level, page=st.session_state.page)
            st.session_state.jobs.extend(initial_jobs)
            
            if not initial_jobs:
                st.warning("No relevant job listings found with the selected filters. Please try a different role or location.")

if st.session_state.resume_text:
    resume_skills = extract_skills(st.session_state.resume_text, SKILLS_DB)
    with st.expander("🔍 **Skills found in your resume**"):
        if resume_skills: st.write(", ".join(sorted(list(resume_skills))))
        else: st.write("No specific technical skills from our list were found.")

if st.session_state.jobs:
    enriched_jobs = []
    for job in st.session_state.jobs:
        job_skills = extract_skills(job['description'], SKILLS_DB)
        matching_skills = resume_skills.intersection(job_skills)
        job['matching_skills_count'] = len(matching_skills)
        job['missing_skills_count'] = len(job_skills - matching_skills)
        job['total_skills_in_job'] = len(job_skills)
        enriched_jobs.append(job)

    job_matches = pd.DataFrame(enriched_jobs).sort_values(
        by=["matching_skills_count", "missing_skills_count"],
        ascending=[False, True]
    ).reset_index(drop=True)

    st.subheader(f"✅ Displaying {len(job_matches)} Top Job Matches (Sorted by Skill Overlap)")
    st.dataframe(job_matches[[
        "title", "company", "matching_skills_count", "missing_skills_count", "total_skills_in_job"
    ]].rename(columns={
        "title": "Job Title", "company": "Company",
        "matching_skills_count": "✅ Matching Skills", "missing_skills_count": "💡 Missing Skills",
        "total_skills_in_job": "Total Skills in Job"
    }))

    st.subheader("📌 Detailed Job-by-Job Analysis")
    for index, row in job_matches.iterrows():
        title = f"**{row['title']}** at **{row['company']}**"
        skill_metric = f"({row['matching_skills_count']} / {row['total_skills_in_job']} Skills Match)"
        with st.expander(f"{title} - {skill_metric}"):
            st.markdown("---")
            st.markdown("##### Skill Analysis for this Role")
            job_skills = extract_skills(row['description'], SKILLS_DB)
            matching_skills = resume_skills.intersection(job_skills)
            missing_skills_for_job = job_skills - resume_skills
            colA, colB = st.columns(2)
            with colA:
                st.markdown("###### ✅ Skills You Have")
                if matching_skills:
                    for skill in sorted(list(matching_skills)): st.success(skill, icon="✔️")
                else: st.markdown("_No direct skill matches found._")
            with colB:
                st.markdown("###### 💡 Skills to Add")
                if missing_skills_for_job:
                    for skill in sorted(list(missing_skills_for_job)): st.warning(skill, icon="➕")
                else: st.markdown("_You have all required skills!_")
            st.markdown("---")
            st.markdown("##### Full Job Description")
            st.markdown(row['description'][:1500] + "...")
            st.link_button("View Full Job Listing", row['link'])

    st.markdown("---")
    if st.button("Show More..."):
        st.session_state.page += 1
        with st.spinner("Fetching more jobs..."):
            more_jobs = get_jobs_from_api(job_query, job_location, is_internship, is_entry_level, page=st.session_state.page)
            if more_jobs:
                st.session_state.jobs.extend(more_jobs)
                st.rerun()
            else:
                st.info("No more job listings found.")