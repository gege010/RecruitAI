"""
Job family templates — predefined criteria configurations.
Based on categories present in the Kaggle resume dataset (hadikp/resume-data-pdf).
"""
from __future__ import annotations

JOB_TEMPLATES: dict[str, dict] = {
    "Data Science": {
        "job_family": "Data Science",
        "required_education_level": "S1",
        "required_education_field": "Computer Science, Statistics, Mathematics, Data Science",
        "required_experience_months": 12,
        "required_skills": [
            "Python", "Machine Learning", "SQL", "Statistics", "Data Visualization",
            "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "Deep Learning",
        ],
        "required_certifications": ["Google Data Analytics", "AWS Machine Learning", "Coursera ML"],
        "required_languages": ["English"],
    },
    "Software Engineer": {
        "job_family": "Software Engineer",
        "required_education_level": "S1",
        "required_education_field": "Computer Science, Software Engineering, Informatics",
        "required_experience_months": 6,
        "required_skills": [
            "Python", "Java", "C++", "Git", "OOP", "REST API",
            "System Design", "Unit Testing", "Agile", "Docker",
        ],
        "required_certifications": [],
        "required_languages": ["English"],
    },
    "Java Developer": {
        "job_family": "Java Developer",
        "required_education_level": "S1",
        "required_education_field": "Computer Science, Informatics",
        "required_experience_months": 12,
        "required_skills": [
            "Java", "Spring Boot", "Maven", "Microservices", "REST API",
            "JUnit", "SQL", "Git", "Docker", "Kafka",
        ],
        "required_certifications": ["Oracle Java Certified"],
        "required_languages": ["English"],
    },
    "Python Developer": {
        "job_family": "Python Developer",
        "required_education_level": "S1",
        "required_education_field": "Computer Science, Informatics",
        "required_experience_months": 6,
        "required_skills": [
            "Python", "FastAPI", "Django", "REST API", "OOP",
            "PostgreSQL", "Git", "Docker", "Testing", "Linux",
        ],
        "required_certifications": [],
        "required_languages": ["English"],
    },
    "React Developer": {
        "job_family": "React Developer",
        "required_education_level": "S1",
        "required_education_field": "Computer Science, Informatics",
        "required_experience_months": 6,
        "required_skills": [
            "React", "JavaScript", "TypeScript", "CSS", "HTML",
            "REST API", "Node.js", "Git", "Redux", "Testing",
        ],
        "required_certifications": [],
        "required_languages": ["English"],
    },
    "DevOps Engineer": {
        "job_family": "DevOps Engineer",
        "required_education_level": "S1",
        "required_education_field": "Computer Science, IT, Informatics",
        "required_experience_months": 18,
        "required_skills": [
            "Docker", "Kubernetes", "CI/CD", "Linux", "AWS",
            "Terraform", "Git", "Ansible", "Monitoring", "Shell Scripting",
        ],
        "required_certifications": ["AWS Solutions Architect", "CKA", "GCP"],
        "required_languages": ["English"],
    },
    "HR": {
        "job_family": "HR",
        "required_education_level": "S1",
        "required_education_field": "Psychology, Human Resource Management, Business Administration",
        "required_experience_months": 12,
        "required_skills": [
            "Recruitment", "Payroll", "Labor Law", "HRIS", "Performance Management",
            "Training & Development", "Employee Relations", "Onboarding", "Excel",
        ],
        "required_certifications": ["SHRM", "PHR"],
        "required_languages": ["English", "Indonesian"],
    },
    "Accountant": {
        "job_family": "Accountant",
        "required_education_level": "S1",
        "required_education_field": "Accounting, Finance",
        "required_experience_months": 12,
        "required_skills": [
            "Accounting", "Financial Reporting", "Taxation", "SAP",
            "Excel", "Auditing", "Budgeting", "GAAP", "Payroll",
        ],
        "required_certifications": ["CPA", "Brevet Pajak", "CA"],
        "required_languages": ["English", "Indonesian"],
    },
    "Banking": {
        "job_family": "Banking",
        "required_education_level": "S1",
        "required_education_field": "Finance, Economics, Accounting, Business",
        "required_experience_months": 12,
        "required_skills": [
            "Financial Analysis", "Risk Management", "Credit Analysis",
            "KYC", "AML", "Banking Products", "Customer Relationship", "Excel",
        ],
        "required_certifications": ["CFA", "WPPE", "Certified Banker"],
        "required_languages": ["English", "Indonesian"],
    },
    "Civil Engineer": {
        "job_family": "Civil Engineer",
        "required_education_level": "S1",
        "required_education_field": "Civil Engineering, Structural Engineering",
        "required_experience_months": 12,
        "required_skills": [
            "AutoCAD", "Structural Analysis", "Project Management",
            "SAP2000", "Revit", "Estimation", "Site Supervision", "MS Project",
        ],
        "required_certifications": ["SKA Teknik Sipil", "PMP"],
        "required_languages": ["English", "Indonesian"],
    },
    "Custom": {
        "job_family": "Custom",
        "required_education_level": "S1",
        "required_education_field": "",
        "required_experience_months": 0,
        "required_skills": [],
        "required_certifications": [],
        "required_languages": [],
    },
}


def get_template(job_family: str) -> dict:
    """Return a copy of the job template for the given family."""
    return dict(JOB_TEMPLATES.get(job_family, JOB_TEMPLATES["Custom"]))


def list_job_families() -> list[str]:
    """Return sorted list of available job families."""
    return sorted(JOB_TEMPLATES.keys())
