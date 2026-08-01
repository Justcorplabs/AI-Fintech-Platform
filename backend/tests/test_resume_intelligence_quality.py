from app.services.recruitment.job_intelligence import (
    job_intelligence,
)
from app.services.recruitment.resume_reviewer import (
    resume_reviewer,
)
from app.services.recruitment.semantic_matcher import (
    semantic_matcher,
)


SAMPLE_JOB = """
## Sample Job Description: Junior Data Analyst

**Company:** JustCorp Technologies
Location: Harare, Zimbabwe
Employment Type: Full-time

Responsibilities
- Perform data analysis and forecasting.
- Prepare dashboards and reports.
- Work with technical teams.

Required Skills
- Communication
- Analytical ability
- Problem-solving
- Teamwork
"""


RESUME_EVIDENCE = """
Data Analyst Intern

Performed data cleaning and data validation
on programme records.

Prepared reports and presented findings to
technical teams.

Identified and corrected data inconsistencies
before monthly reporting.

Collaborated with technical teams during
field verification work.

Built a crop yield prediction model using
Python and historical agricultural data.
"""


def test_job_parser_removes_heading_and_field_labels():
    profile = job_intelligence.analyse(
        SAMPLE_JOB
    )

    assert (
        profile["job_title"]
        == "Junior Data Analyst"
    )

    assert (
        profile["organisation"]
        == "JustCorp Technologies"
    )


def test_semantic_matcher_recognises_truthful_evidence():
    requirements = [
        "data analysis",
        "communication",
        "analytical",
        "problem-solving",
        "team",
        "forecasting",
    ]

    result = semantic_matcher.match(
        resume_text=RESUME_EVIDENCE,
        requirements=requirements,
    )

    matched = set(
        result["matched"]
    )

    assert "data analysis" in matched
    assert "communication" in matched
    assert "analytical" in matched
    assert "problem solving" in matched
    assert "team" in matched
    assert "forecasting" in matched
    assert result["score"] >= 85


def test_resume_reviewer_uses_semantic_match_score():
    requirements = [
        "data analysis",
        "communication",
        "analytical",
        "team",
        "forecasting",
    ]

    review = resume_reviewer.review_resume(
        raw_text=RESUME_EVIDENCE,
        target_keywords=requirements,
    )

    found = set(
        review["found_keywords"]
    )

    missing = set(
        review["missing_keywords"]
    )

    assert set(requirements) <= found
    assert not (
        set(requirements)
        & missing
    )

    assert (
        review["skills_score"]
        >= 85
    )

    assert (
        review["job_match_score"]
        >= 85
    )
