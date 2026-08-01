from app.services.recruitment.achievement_extractor import (
    achievement_extractor,
)
from app.services.recruitment.recruiter_rewriter import (
    recruiter_rewriter,
)
from app.services.recruitment.resume_intelligence import (
    resume_intelligence,
)


RAW_RESUME = """
PROFESSIONAL EXPERIENCE

Monitoring and Evaluation Intern
Environmental Management Agency
2024 - 2025

- Cleaned and validated programme records.
- Prepared monthly reporting inputs.
- Participated in field verification activities.

EDUCATION AND TRAINING

BSc Honours Degree in Data Science and Systems
University of Zimbabwe
2022 - 2026

Certificate in Monitoring and Evaluation
Zimbabwe Institute of Public Administration and Management
2024

SELECTED STRENGTHS FOR ARTIFICIAL INTELLIGENCE ENGINEERING

- Strong attention to data quality and documentation.
- Ability to learn new technical frameworks.

LANGUAGES AND REFERENCES

English: Fluent
Shona: Native

Mr Nota
Monitoring and Evaluation Technician
Environmental Management Agency
nota@example.com
+263 700 000 000
"""


def test_combined_headings_preserve_section_boundaries():
    profile = resume_intelligence.analyse(
        RAW_RESUME
    )

    experience = profile["experience"]

    assert len(experience) == 1

    combined_bullets = " ".join(
        bullet
        for item in experience
        for bullet in item.get(
            "bullets",
            [],
        )
    ).lower()

    assert "cleaned and validated" in combined_bullets
    assert "monthly reporting" in combined_bullets
    assert "field verification" in combined_bullets

    assert "honours degree" not in combined_bullets
    assert "certificate in monitoring" not in combined_bullets
    assert "strong attention" not in combined_bullets
    assert "english" not in combined_bullets
    assert "mr nota" not in combined_bullets


def test_education_is_not_classified_as_experience():
    profile = resume_intelligence.analyse(
        RAW_RESUME
    )

    education_text = " ".join(
        str(item)
        for item in profile["education"]
    ).lower()

    assert "honours degree" in education_text
    assert "certificate in monitoring" in education_text


def test_languages_and_references_are_recovered():
    profile = resume_intelligence.analyse(
        RAW_RESUME
    )

    languages = {
        language.lower()
        for language in profile["languages"]
    }

    reference_text = " ".join(
        profile["references"]
    ).lower()

    assert "english" in languages
    assert "shona" in languages
    assert "mr nota" in reference_text
    assert "environmental management agency" in reference_text


def test_rewriter_does_not_invent_supported_prefix():
    rewritten = recruiter_rewriter.rewrite_bullet(
        "Data cleaning and validation",
        {
            "industry": "Technology / IT",
            "job_title": "Junior Data Analyst",
            "responsibilities": [],
        },
    )

    assert rewritten.startswith(
        "Performed data cleaning"
    )

    assert not rewritten.startswith(
        "Supported "
    )


def test_achievement_preserves_candidate_evidence():
    rewritten = (
        achievement_extractor
        ._rewrite_achievement(
            "Data cleaning and validation",
            "data",
        )
    )

    assert rewritten.startswith(
        "Performed data cleaning"
    )

    assert (
        "Applied data analysis and "
        "reporting techniques"
        not in rewritten
    )


def test_summary_uses_only_supplied_evidence_skills():
    summary = recruiter_rewriter.human_summary(
        resume_summary="",
        review={
            "job_title": "Junior Data Analyst",
            "industry": "Technology / IT",
            "found_keywords": [
                "python",
                "sql",
            ],
        },
        skills=[
            "Python",
            "SQL",
        ],
    )

    lower = summary.lower()

    assert "python" in lower
    assert "sql" in lower
    assert "problem-solving" not in lower
    assert "forecasting" not in lower
