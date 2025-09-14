# api.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import re
import requests  # <-- Make sure to import requests
import pandas as pd # <-- Make sure to import pandas

# --- CONFIGURATION (Copied from your app) ---
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

app = Flask(__name__)
# This allows your React app (on a different port) to call this API
CORS(app)

# --- SECURITY WARNING ---
# Hardcoding API keys is not secure for production.
# It is better to load them from environment variables.
# For example: import os; JSEARCH_API_KEY = os.environ.get("JSEARCH_API_KEY")
JSEARCH_API_KEY = "332fdfcc6dmsh5996abe50ef6b4fp1ee338jsn056cd92de316"


# --- HELPER FUNCTIONS (Copied and adapted from your app) ---

def get_jobs_from_api(query, location, internship_only, entry_level_only, page=1):
    url = "https://jsearch.p.rapidapi.com/search"
    
    if not JSEARCH_API_KEY:
        print("ERROR: JSearch API key not found.")
        return []

    if entry_level_only:
        query = f"{query} entry level fresher"

    employment_types = []
    if internship_only:
        employment_types.append("INTERN")
    if entry_level_only and not internship_only:
        employment_types.append("FULLTIME")

    headers = {"X-RapidAPI-Key": JSEARCH_API_KEY, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"}
    params = {"query": f"{query} in {location}", "page": str(page)}
    if employment_types:
        params["employment_types"] = ",".join(employment_types)

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status() # Raises an exception for bad status codes (4xx or 5xx)
        results = response.json().get("data", [])
        jobs = []
        if not results: return [] # Return empty if no data
        for job in results:
            jobs.append({
                "title": job.get("job_title", "N/A"),
                "company": job.get("employer_name", "N/A"),
                "description": job.get("job_description", "No description provided."),
                "link": job.get("job_apply_link", "#")
            })
        return jobs
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching jobs from JSearch API: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

def extract_skills(text, skills_list):
    found_skills = set()
    for skill in skills_list:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            if skill.lower() in ['sql', 'api']:
                uppercase_pattern = r'\b' + skill.upper() + r'\b'
                if not re.search(uppercase_pattern, text):
                    continue
            
            # Normalize skill names
            if skill.lower() in ['js', 'javascript']: found_skills.add('Javascript')
            elif skill.lower() in ['aws', 'amazon web services']: found_skills.add('AWS')
            elif skill.lower() in ['gcp', 'google cloud']: found_skills.add('GCP')
            else: found_skills.add(skill.title())
    return found_skills

# --- API ENDPOINTS ---

@app.route('/api/job-roles', methods=['GET'])
def get_job_roles():
    """Provides the list of job roles for frontend dropdowns."""
    return jsonify(JOB_ROLES)

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Provides the list of locations for frontend dropdowns."""
    return jsonify(LOCATIONS)

@app.route('/api/match-jobs', methods=['POST'])
def match_jobs():
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file provided"}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    job_query = request.form.get('job_query', 'Software Developer')
    job_location = request.form.get('job_location', 'Anywhere in India')
    is_internship = request.form.get('is_internship', 'false').lower() == 'true'
    is_entry_level = request.form.get('is_entry_level', 'false').lower() == 'true'
    page = request.form.get('page', 1, type=int)

    try:
        resume_text = ""
        with pdfplumber.open(file) as pdf:
            for page_content in pdf.pages:
                text = page_content.extract_text()
                if text: resume_text += text + "\n"

        resume_skills = extract_skills(resume_text, SKILLS_DB)
        jobs = get_jobs_from_api(job_query, job_location, is_internship, is_entry_level, page)
        
        if not jobs:
             return jsonify({ "resume_skills": sorted(list(resume_skills)), "job_matches": [] })

        # --- Job Enrichment and Sorting Logic (Copied from your app) ---
        enriched_jobs = []
        for job in jobs:
            job_skills = extract_skills(job['description'], SKILLS_DB)
            matching_skills = resume_skills.intersection(job_skills)
            job['matching_skills_count'] = len(matching_skills)
            job['missing_skills_count'] = len(job_skills - matching_skills)
            job['total_skills_in_job'] = len(job_skills)
            # Add the skill lists themselves for detailed view in frontend
            job['matching_skills'] = sorted(list(matching_skills))
            job['missing_skills'] = sorted(list(job_skills - resume_skills))
            enriched_jobs.append(job)

        job_matches_df = pd.DataFrame(enriched_jobs).sort_values(
            by=["matching_skills_count", "missing_skills_count"],
            ascending=[False, True]
        ).reset_index(drop=True)
        
        # Convert DataFrame back to list of dictionaries for JSON response
        sorted_jobs = job_matches_df.to_dict('records')

        return jsonify({
            "resume_skills": sorted(list(resume_skills)),
            "job_matches": sorted_jobs
        })

    except Exception as e:
        print(f"Error processing match-jobs request: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)