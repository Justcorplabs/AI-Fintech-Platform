from app.services.recruitment.candidate_intelligence import (
    candidate_intelligence,
)
from app.services.recruitment.job_intelligence import (
    job_intelligence,
)
from app.services.recruitment.professional_polisher import (
    professional_polisher,
)
from app.services.recruitment.resume_intelligence import (
    resume_intelligence,
)
from app.services.recruitment.resume_reviewer import (
    resume_reviewer,
)


RAW_RESUME = """
PROFESSIONAL EXPERIENCE

Monitoring and Evaluation Intern
Environmental Management Agency
2024 - 2025

- Cleaned and validated programme records.

EDUCATION AND TRAINING

University of Zimbabwe
Honours Degree in Data Science and Systems,
2022 to 2026 | Degree Class: Upper Second Class (2.1)

Zimbabwe Institute of Public Administration and Management
Certificate in Monitoring and Evaluation, 2024

Mabvuku High School
Advanced Level, 2021

LANGUAGES AND REFERENCES

Languages: Shona: Native; English: Fluent
Monitoring and Evaluation Technician, Environmental Management

Mr Nota
Monitoring and Evaluation Technician
Environmental Management Agency
Phone: +263 786 328 560
Email: nota@example.com

Ruvimbo Parirenyatwa
Environmental Quality Inspector
Environmental Management Agency
Phone: +263 771 225 800
"""


JOB_DESCRIPTION = """
## Sample Job Description: Junior Data Analyst

Company: JustCorp Technologies
Experience Level: Entry Level

Required Qualifications

Bachelor's degree or final-year study in Data Science,
Artificial Intelligence, Machine Learning, Statistics,
Computer Science, Information Systems, Mathematics,
or a related field.

Required Skills

Python, SQL, Excel, Microsoft Excel, Power BI,
dashboards, dashboard, databases and database.
"""


def test_education_supports_institution_first_layout():
    profile = resume_intelligence.analyse(
        RAW_RESUME
    )

    education = profile["education"]

    assert education[0]["institution"] == (
        "University of Zimbabwe"
    )

    assert "Honours Degree" in (
        education[0]["qualification"]
    )

    assert education[1]["institution"] == (
        "Zimbabwe Institute of Public "
        "Administration and Management"
    )

    assert "Certificate" in (
        education[1]["qualification"]
    )

    assert education[2]["institution"] == (
        "Mabvuku High School"
    )

    assert "Advanced Level" in (
        education[2]["qualification"]
    )


def test_reference_parser_removes_language_contamination():
    profile = resume_intelligence.analyse(
        RAW_RESUME
    )

    references = profile["references"]

    combined = " ".join(
        references
    ).lower()

    assert references[0] == "Mr Nota"
    assert "languages:" not in combined
    assert "shona: native" not in combined

    assert not combined.startswith(
        "monitoring and evaluation technician"
    )


def test_skill_polisher_canonicalises_fragments():
    skills = professional_polisher.polish_skills(
        [
            "Programming And Data Python",
            "Data",
            "Transformation",
            "Machine Learning Logistic Regression",
            "Decision Tree",
            "Random Forest",
            "Model Evaluation Precision",
            "Recall",
            "F1-Score",
            "Roc-Auc",
            "Pr",
            "Auc",
            "Explainable Artificial Intelligence Shap",
            "Lime",
        ]
    )

    assert "Python" in skills
    assert "Data Transformation" in skills
    assert "Machine Learning" in skills
    assert "Logistic Regression" in skills
    assert "Decision Trees" in skills
    assert "Random Forest" in skills

    assert (
        "Precision, Recall & F1-Score"
        in skills
    )

    assert "ROC-AUC & PR-AUC" in skills
    assert "Explainable AI" in skills
    assert "SHAP" in skills
    assert "LIME" in skills

    assert "Data" not in skills
    assert "Pr" not in skills
    assert "Auc" not in skills


def test_job_profile_canonicalises_requirements():
    profile = job_intelligence.analyse(
        JOB_DESCRIPTION
    )

    assert (
        profile["experience_requirement"]
        == "Entry Level"
    )

    assert (
        profile["degree_requirement_group"]["mode"]
        == "any"
    )

    tools = profile["software_tools"]

    assert tools.count(
        "microsoft excel"
    ) == 1

    assert tools.count(
        "dashboards"
    ) == 1

    assert tools.count(
        "databases"
    ) == 1

    assert (
        "computer science"
        not in profile["keywords"]
    )


def test_degree_alternatives_are_evaluated_as_or_group():
    review = resume_reviewer.review_resume(
        raw_text=RAW_RESUME,
        job_description=JOB_DESCRIPTION,
    )

    assert (
        review["degree_requirement_satisfied"]
        is True
    )

    assert "data science" in (
        review["degree_requirement_evidence"]
    )

    assert (
        "computer science"
        not in review["missing_keywords"]
    )


def test_candidate_risks_do_not_require_every_degree_option():
    review = resume_reviewer.review_resume(
        raw_text=RAW_RESUME,
        job_description=JOB_DESCRIPTION,
    )

    intelligence = candidate_intelligence.generate(
        review=review,
        built_resume={
            "education": [
                "Honours Degree in Data Science "
                "and Systems"
            ],
        },
    )

    risks = " ".join(
        item["risk"]
        for item in intelligence[
            "hiring_risks"
        ]
    ).lower()

    assert (
        "computer science"
        not in risks
    )

    salary = intelligence[
        "salary_intelligence"
    ]

    assert (
        salary["confidence"]
        == "Heuristic only; "
        "not market-verified"
    )

    assert (
        "not based on live market data"
        in salary[
            "recommended_positioning"
        ].lower()
    )
