import pytest

from app.services.recruitment.ats_scorer import (
    ATSScorer,
)
from app.services.recruitment.candidate_intelligence import (
    CandidateIntelligence,
)
from app.services.recruitment.resume_builder import (
    ResumeBuilder,
)
from app.services.recruitment.resume_reviewer import (
    ResumeReviewer,
)


@pytest.fixture
def scorer():
    return ATSScorer()


@pytest.fixture
def intelligence():
    return CandidateIntelligence()


@pytest.fixture
def builder():
    return ResumeBuilder()


def test_skill_aliases_are_deduplicated(
    scorer,
):
    score = scorer.skills_score(
        found=[
            "Power BI",
            "SQL",
        ],
        target=[
            "powerbi",
            "Power BI",
            "sql",
        ],
    )

    assert score == 100.0


def test_empty_resume_has_no_artificial_score_floor(
    scorer,
):
    scores = {
        "contact_score": (
            scorer.contact_score("")
        ),
        "skills_score": 0,
        "education_score": (
            scorer.education_score("")
        ),
        "experience_score": (
            scorer.experience_score("")
        ),
        "formatting_score": (
            scorer.formatting_score("")
        ),
        "achievement_score": (
            scorer.achievement_score("")
        ),
        "job_match_score": 0,
    }

    assert (
        scorer.final_score(
            scores,
            job_context_available=False,
        )
        == 0.0
    )


def test_strong_resume_scores_above_weak_resume(
    scorer,
):
    strong_text = """
    Jane Candidate
    jane@example.com
    +263 77 123 4567
    linkedin.com/in/jane

    Professional Summary
    Data analyst with 3 years of experience.

    Skills
    Python, SQL, Power BI

    Work Experience
    Data Analyst
    Improved monthly reporting time by 35%.
    Automated 12 recurring reports.

    Education
    BSc Honours in Data Science

    Projects
    Sales dashboard project
    """

    weak_text = (
        "Jane Candidate\n"
        "Hardworking person looking for work."
    )

    strong_components = {
        "contact_score": (
            scorer.contact_score(
                strong_text
            )
        ),
        "skills_score": (
            scorer.skills_score(
                [
                    "python",
                    "sql",
                    "power bi",
                ],
                [
                    "python",
                    "sql",
                    "power bi",
                ],
            )
        ),
        "education_score": (
            scorer.education_score(
                strong_text,
                "Bachelors",
            )
        ),
        "experience_score": (
            scorer.experience_score(
                strong_text,
                3.0,
            )
        ),
        "formatting_score": (
            scorer.formatting_score(
                strong_text
            )
        ),
        "achievement_score": (
            scorer.achievement_score(
                strong_text
            )
        ),
        "job_match_score": 100,
    }

    weak_components = {
        "contact_score": (
            scorer.contact_score(
                weak_text
            )
        ),
        "skills_score": 0,
        "education_score": (
            scorer.education_score(
                weak_text
            )
        ),
        "experience_score": (
            scorer.experience_score(
                weak_text
            )
        ),
        "formatting_score": (
            scorer.formatting_score(
                weak_text
            )
        ),
        "achievement_score": (
            scorer.achievement_score(
                weak_text
            )
        ),
        "job_match_score": 0,
    }

    strong_score = (
        scorer.final_score(
            strong_components,
            job_context_available=True,
        )
    )

    weak_score = (
        scorer.final_score(
            weak_components,
            job_context_available=True,
        )
    )

    assert strong_score > weak_score
    assert strong_score >= 75
    assert weak_score < 30


def test_all_component_scores_are_bounded(
    scorer,
):
    long_text = (
        "email@example.com "
        "+263771234567 "
        "https://linkedin.com/test "
        "Education Skills Experience Projects "
        "Certifications Summary "
        "Improved performance by 100% "
        * 100
    )

    values = [
        scorer.contact_score(
            long_text
        ),
        scorer.education_score(
            long_text,
            "PhD",
        ),
        scorer.experience_score(
            long_text,
            50,
        ),
        scorer.formatting_score(
            long_text
        ),
        scorer.achievement_score(
            long_text
        ),
        scorer.skills_score(
            ["python"],
            ["python"],
        ),
    ]

    assert all(
        0 <= value <= 100
        for value in values
    )


def test_recruiter_score_does_not_double_count_ats(
    intelligence,
):
    common = {
        "job_match": 80,
        "education": 80,
        "experience": 70,
        "achievements": 60,
        "built_resume": {},
        "skills": 75,
        "formatting": 80,
        "contact": 100,
        "job_context_available": True,
    }

    low_ats = (
        intelligence._recruiter_score(
            ats_score=20,
            **common,
        )
    )

    high_ats = (
        intelligence._recruiter_score(
            ats_score=95,
            **common,
        )
    )

    assert low_ats == high_ats


def test_no_job_context_avoids_interview_claim(
    intelligence,
):
    recommendation = (
        intelligence._recommendation(
            82,
            job_context_available=False,
        )
    )

    assert "Job Description" in recommendation
    assert "Recommended for Interview" not in recommendation


def test_builder_does_not_add_missing_job_skills(
    builder,
):
    profile = {
        "skills": [],
    }

    review = {
        "found_keywords": [],
        "technical_skills_required": [
            "Python",
        ],
        "software_tools_required": [
            "Power BI",
        ],
        "soft_skills_required": [
            "Leadership",
        ],
    }

    assert (
        builder._core_skills(
            profile,
            review,
        )
        == []
    )

    assert (
        builder._technical_skills(
            profile,
            review,
        )
        == []
    )


def test_builder_does_not_fabricate_experience(
    builder,
):
    result = builder._experience(
        {
            "experience": [],
        },
        {
            "cv_coach": {
                "experience_rewrite": [
                    "Managed reports.",
                ],
            }
        },
    )

    assert result == []


def test_builder_does_not_fabricate_education(
    builder,
):
    result = builder._education(
        {
            "education": [],
        },
        {
            "degree_requirements": [
                "Bachelor's degree",
            ],
        },
    )

    assert result == []


def test_builder_does_not_assume_languages(
    builder,
):
    assert (
        builder._languages(
            {
                "languages": [],
            }
        )
        == []
    )


def test_interview_probability_can_be_zero():
    reviewer = ResumeReviewer()

    probability = (
        reviewer._interview_probability(
            0,
            {
                "job_match_score": 0,
                "experience_score": 0,
                "education_score": 0,
            },
            job_context_available=True,
        )
    )

    assert probability == 0.0


def test_cv_coach_gain_is_capped():
    reviewer = ResumeReviewer()

    review = {
        "ats_score": 20,
        "contact_score": 0,
        "formatting_score": 0,
        "achievement_score": 0,
        "missing_keywords": [
            f"skill-{index}"
            for index in range(50)
        ],
        "professional_summary": "",
        "scoring_context": {
            "job_context_available": True,
        },
    }

    coach = reviewer._cv_coach(
        review
    )

    assert (
        coach["estimated_gain"]
        <= 12
    )