

# Resume to Job Matching System
Tired of sifting through countless job postings? This tool streamlines your job search by intelligently matching your resume to the most relevant job opportunities in India.

This application analyzes the content of your uploaded resume and compares it against real-time job listings to provide a ranked list of jobs with a calculated match score.

# How it Works
The process is simple:

1. 🎯 Enter Your Job Query Specify the job title or role you're looking for (e.g., "Data Analyst", "React Developer").

2. 📄 Upload Your Resume Provide your resume in PDF format. The system will parse the text to understand your skills and experience.

3. ✨ View Your Matches The application fetches relevant job listings and displays them with a percentage score, indicating how closely each job description matches your resume.

# Key Features
* Real-time Job Listings: Fetches current job openings from across India using the powerful JSearch API.

* PDF Resume Parsing: Automatically extracts text and relevant keywords from your uploaded PDF resume.

* Smart Matching Algorithm: Utilizes TF-IDF Vectorization and Cosine Similarity to accurately calculate the match score between your resume and each job description.

* Interactive Dashboard: A clean and user-friendly interface built with Streamlit to display job details, including title, company, location, and your match percentage.

# Tech Stack & Installation
This project is built with Python and requires the following libraries:

* Python 3.7+

* Streamlit

* Requests

* PyPDF2

* Pandas

* scikit-learn