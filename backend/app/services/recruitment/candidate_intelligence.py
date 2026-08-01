from typing import Any, Dict, List

from app.services.recruitment.explainability_engine import (
    explainability_engine,
)


class CandidateIntelligence:
    def generate(
        self,
        review: dict[str, Any],
        built_resume: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        built_resume = (
            built_resume or {}
        )

        scoring_context = (
            review.get(
                "scoring_context",
                {},
            )
            or {}
        )

        job_context_available = bool(
            scoring_context.get(
                "job_context_available",
                True,
            )
        )

        ats_score = self._clamp(
            review.get(
                "ats_score",
                0,
            )
        )

        job_match = self._clamp(
            review.get(
                "job_match_score",
                0,
            )
        )

        skills = self._clamp(
            review.get(
                "skills_score",
                0,
            )
        )

        education = self._clamp(
            review.get(
                "education_score",
                0,
            )
        )

        experience = self._clamp(
            review.get(
                "experience_score",
                0,
            )
        )

        achievements = self._clamp(
            review.get(
                "achievement_score",
                0,
            )
        )

        formatting = self._clamp(
            review.get(
                "formatting_score",
                0,
            )
        )

        contact = self._clamp(
            review.get(
                "contact_score",
                0,
            )
        )

        recruiter_score = (
            self._recruiter_score(
                ats_score=ats_score,
                job_match=job_match,
                education=education,
                experience=experience,
                achievements=achievements,
                built_resume=built_resume,
                skills=skills,
                formatting=formatting,
                contact=contact,
                job_context_available=(
                    job_context_available
                ),
            )
        )

        score_components = (
            self._score_components(
                job_match=job_match,
                skills=skills,
                education=education,
                experience=experience,
                achievements=achievements,
                formatting=formatting,
                contact=contact,
                job_context_available=(
                    job_context_available
                ),
            )
        )

        explainability = (
            explainability_engine.generate(
                review=review,
                candidate_intelligence={
                    "recruiter_score": (
                        recruiter_score
                    ),
                    "score_components": (
                        score_components
                    ),
                },
            )
        )

        return {
            "overall_rating": (
                self._letter_grade(
                    recruiter_score
                )
            ),
            "recruiter_score": round(
                recruiter_score,
                2,
            ),
            "hiring_recommendation": (
                self._recommendation(
                    recruiter_score,
                    job_context_available=(
                        job_context_available
                    ),
                )
            ),
            "confidence": (
                self._confidence(
                    review,
                    built_resume,
                    job_context_available=(
                        job_context_available
                    ),
                )
            ),
            "candidate_strengths": (
                self._strengths(
                    review,
                    built_resume,
                )
            ),
            "hiring_risks": (
                self._risks(
                    review
                )
            ),
            "interview_readiness": (
                self._interview_readiness(
                    review,
                    recruiter_score,
                    job_context_available=(
                        job_context_available
                    ),
                )
            ),
            "learning_roadmap": (
                self._learning_roadmap(
                    review
                )
            ),
            "salary_intelligence": (
                self._salary_intelligence(
                    review,
                    recruiter_score,
                )
            ),
            "recruiter_summary": (
                self._summary(
                    review,
                    recruiter_score,
                    job_context_available=(
                        job_context_available
                    ),
                )
            ),
            "score_components": (
                score_components
            ),
            "scoring_context": {
                "job_context_available": (
                    job_context_available
                ),
                "aggregate_ats_used_as_score_input": (
                    False
                ),
            },
            "explainability": explainability,
        }

    def _clamp(
        self,
        value: Any,
    ) -> float:
        try:
            numeric = float(
                value or 0
            )

        except (
            TypeError,
            ValueError,
        ):
            numeric = 0.0

        return min(
            100.0,
            max(0.0, numeric),
        )

    def _score_components(
        self,
        *,
        job_match: float,
        skills: float,
        education: float,
        experience: float,
        achievements: float,
        formatting: float,
        contact: float,
        job_context_available: bool,
    ) -> dict[str, float]:
        if job_context_available:
            return {
                "job_match": round(
                    job_match,
                    2,
                ),
                "experience": round(
                    experience,
                    2,
                ),
                "education": round(
                    education,
                    2,
                ),
                "achievements": round(
                    achievements,
                    2,
                ),
                "formatting": round(
                    formatting,
                    2,
                ),
                "contact": round(
                    contact,
                    2,
                ),
            }

        return {
            "skills": round(
                skills,
                2,
            ),
            "experience": round(
                experience,
                2,
            ),
            "education": round(
                education,
                2,
            ),
            "achievements": round(
                achievements,
                2,
            ),
            "formatting": round(
                formatting,
                2,
            ),
            "contact": round(
                contact,
                2,
            ),
        }

    def _recruiter_score(
        self,
        ats_score: float,
        job_match: float,
        education: float,
        experience: float,
        achievements: float,
        built_resume: dict[str, Any],
        skills: float = 0,
        formatting: float = 0,
        contact: float = 0,
        job_context_available: bool = True,
    ) -> float:
        """
        Score independent evidence components.

        ats_score is retained in the signature for backward
        compatibility, but it is intentionally not weighted
        again because it already aggregates the same evidence.
        """

        del ats_score
        del built_resume

        if job_context_available:
            score = (
                0.35 * self._clamp(
                    job_match
                )
                + 0.25 * self._clamp(
                    experience
                )
                + 0.15 * self._clamp(
                    education
                )
                + 0.15 * self._clamp(
                    achievements
                )
                + 0.05 * self._clamp(
                    formatting
                )
                + 0.05 * self._clamp(
                    contact
                )
            )

        else:
            score = (
                0.25 * self._clamp(
                    skills
                )
                + 0.30 * self._clamp(
                    experience
                )
                + 0.20 * self._clamp(
                    education
                )
                + 0.15 * self._clamp(
                    achievements
                )
                + 0.05 * self._clamp(
                    formatting
                )
                + 0.05 * self._clamp(
                    contact
                )
            )

        return round(
            self._clamp(score),
            2,
        )

    def _letter_grade(
        self,
        score: float,
    ) -> str:
        if score >= 90:
            return "A"

        if score >= 85:
            return "A-"

        if score >= 80:
            return "B+"

        if score >= 75:
            return "B"

        if score >= 70:
            return "B-"

        if score >= 60:
            return "C"

        return "D"

    def _recommendation(
        self,
        score: float,
        *,
        job_context_available: bool,
    ) -> str:
        if not job_context_available:
            if score >= 75:
                return (
                    "Strong Profile — Add a Job "
                    "Description for Interview Matching"
                )

            if score >= 60:
                return (
                    "Promising Profile — Role Context "
                    "Required"
                )

            return (
                "Profile Needs Stronger Evidence and "
                "Role Context"
            )

        if score >= 88:
            return (
                "Highly Recommended for Interview"
            )

        if score >= 78:
            return (
                "Recommended for Interview"
            )

        if score >= 68:
            return (
                "Consider After Targeted CV "
                "Improvements"
            )

        if score >= 55:
            return (
                "Potential Candidate With Notable Gaps"
            )

        return (
            "Not Recommended Without Major "
            "Improvements"
        )

    def _confidence(
        self,
        review: dict[str, Any],
        built_resume: dict[str, Any],
        *,
        job_context_available: bool,
    ) -> float:
        confidence = 30.0

        if job_context_available:
            confidence += 20

        parsed_candidate = (
            review.get(
                "parsed_candidate",
                {},
            )
            or {}
        )

        if (
            parsed_candidate.get(
                "name"
            )
            and parsed_candidate.get(
                "email"
            )
        ):
            confidence += 10

        if built_resume.get(
            "professional_experience"
        ):
            confidence += 15

        if built_resume.get(
            "education"
        ):
            confidence += 10

        if built_resume.get(
            "key_achievements"
        ):
            confidence += 10

        if (
            review.get(
                "contact_score",
                0,
            )
            >= 80
        ):
            confidence += 5

        missing = (
            review.get(
                "missing_keywords",
                [],
            )
            or []
        )

        if job_context_available:
            confidence -= min(
                15,
                len(missing),
            )

        return round(
            min(
                95.0,
                max(20.0, confidence),
            ),
            2,
        )

    def _strengths(
        self,
        review: dict[str, Any],
        built_resume: dict[str, Any],
    ) -> List[str]:
        strengths: list[str] = []

        skills = (
            built_resume.get(
                "core_skills",
                [],
            )
            or []
        )

        technical_skills = (
            built_resume.get(
                "technical_skills",
                [],
            )
            or []
        )

        for skill in skills[:4]:
            strengths.append(
                (
                    "Visible CV evidence of "
                    f"{skill}."
                )
            )

        for skill in technical_skills[:2]:
            strengths.append(
                (
                    "Visible practical tool evidence "
                    f"in {skill}."
                )
            )

        if (
            review.get(
                "education_score",
                0,
            )
            >= 80
        ):
            strengths.append(
                (
                    "Relevant academic evidence is "
                    "visible."
                )
            )

        if (
            review.get(
                "experience_score",
                0,
            )
            >= 70
        ):
            strengths.append(
                (
                    "Relevant practical experience is "
                    "clearly visible."
                )
            )

        if (
            review.get(
                "job_match_score",
                0,
            )
            >= 80
        ):
            strengths.append(
                (
                    "Strong match between visible CV "
                    "evidence and job requirements."
                )
            )

        return strengths[:7] or [
            (
                "Candidate evidence is limited and "
                "requires recruiter verification."
            )
        ]

    def _risks(
        self,
        review: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        risks = []

        missing = (
            review.get(
                "missing_keywords",
                [],
            )
            or []
        )

        degree_terms = {
            str(item).lower().strip()
            for item in (
                review.get(
                    "degree_requirements",
                    [],
                )
                or []
            )
        }

        for keyword in missing:
            key = str(
                keyword
            ).lower().strip()

            # Degree alternatives are evaluated as
            # a single OR group, not as separate
            # mandatory requirements.
            if key in degree_terms:
                continue

            risks.append(
                {
                    "risk": (
                        f"{str(keyword).title()} "
                        "is not clearly demonstrated "
                        "in the CV."
                    ),
                    "level": "Medium",
                    "mitigation": (
                        f"Only add {keyword} if the "
                        "candidate has truthful "
                        "coursework, training, "
                        "project work or practical "
                        "exposure."
                    ),
                }
            )

            if len(risks) >= 5:
                break

        degree_options = (
            review.get(
                "degree_requirements",
                [],
            )
            or []
        )

        if (
            degree_options
            and not review.get(
                "degree_requirement_satisfied",
                False,
            )
        ):
            risks.append(
                {
                    "risk": (
                        "No clearly matching degree "
                        "discipline was detected from "
                        "the advertised alternatives."
                    ),
                    "level": "Medium",
                    "mitigation": (
                        "Clarify the exact degree, "
                        "major and related coursework "
                        "shown in the submitted CV."
                    ),
                }
            )

        if (
            review.get(
                "experience_score",
                0,
            )
            < 65
        ):
            risks.append(
                {
                    "risk": (
                        "Practical experience may "
                        "appear limited for the role."
                    ),
                    "level": "Medium",
                    "mitigation": (
                        "Clarify internship, "
                        "attachment, project and "
                        "practical responsibilities."
                    ),
                }
            )

        if (
            review.get(
                "achievement_score",
                0,
            )
            < 60
        ):
            risks.append(
                {
                    "risk": (
                        "Few measurable achievements "
                        "are visible."
                    ),
                    "level": "Low",
                    "mitigation": (
                        "Add truthful numbers, "
                        "volumes, reports produced, "
                        "records processed or "
                        "performance metrics where "
                        "available."
                    ),
                }
            )

        return risks[:6]

    def _interview_readiness(
        self,
        review: dict[str, Any],
        score: float,
        *,
        job_context_available: bool,
    ) -> dict[str, Any]:
        if not job_context_available:
            level = "Role Context Required"

        elif score >= 85:
            level = "High"

        elif score >= 70:
            level = "Moderate"

        else:
            level = "Needs Preparation"

        return {
            "level": level,
            "score": round(
                score,
                2,
            ),
            "likely_questions": (
                review.get(
                    "interview_questions",
                    [],
                )[:6]
            ),
            "preparation_focus": (
                self._prep_focus(
                    review
                )
            ),
        }

    def _prep_focus(
        self,
        review: Dict[str, Any],
    ) -> List[str]:
        focus = []

        degree_terms = {
            str(item).lower().strip()
            for item in (
                review.get(
                    "degree_requirements",
                    [],
                )
                or []
            )
        }

        for keyword in (
            review.get(
                "missing_keywords",
                [],
            )
            or []
        ):
            if (
                str(keyword)
                .lower()
                .strip()
                in degree_terms
            ):
                continue

            focus.append(
                "Prepare a truthful answer "
                f"about any exposure to {keyword}."
            )

            if len(focus) >= 4:
                break

        if (
            review.get(
                "degree_requirements"
            )
            and not review.get(
                "degree_requirement_satisfied",
                False,
            )
        ):
            focus.append(
                "Prepare to explain how your "
                "degree and coursework relate "
                "to the accepted study fields."
            )

        job_title = (
            review.get(
                "job_title"
            )
            or "the role"
        ).lower()

        if "finance" in job_title:
            focus.append(
                "Prepare to explain "
                "reconciliations, financial "
                "records, invoices and Excel use."
            )

        if (
            "program" in job_title
            or "programme" in job_title
        ):
            focus.append(
                "Prepare examples of data "
                "collection, stakeholder "
                "communication and programme "
                "support."
            )

        if "data" in job_title:
            focus.append(
                "Prepare to discuss projects, "
                "tools, datasets and measurable "
                "outcomes."
            )

        return focus[:6]

    def _learning_roadmap(
        self,
        review: dict[str, Any],
    ) -> List[dict[str, str]]:
        roadmap: list[
            dict[str, str]
        ] = []

        missing = (
            review.get(
                "missing_keywords",
                [],
            )
            or []
        )

        for index, keyword in enumerate(
            missing[:4],
            start=1,
        ):
            roadmap.append(
                {
                    "week": (
                        f"Week {index}"
                    ),
                    "focus": (
                        str(keyword).title()
                    ),
                    "action": (
                        "Build truthful exposure through "
                        "a short course, reading task or "
                        "mini-project related to "
                        f"{keyword}."
                    ),
                }
            )

        if not roadmap:
            roadmap = [
                {
                    "week": "Week 1",
                    "focus": (
                        "Interview Preparation"
                    ),
                    "action": (
                        "Prepare STAR examples from "
                        "internship, projects and "
                        "academic experience."
                    ),
                },
                {
                    "week": "Week 2",
                    "focus": (
                        "Role-Specific Tools"
                    ),
                    "action": (
                        "Revise the main tools or "
                        "processes mentioned in the "
                        "target role."
                    ),
                },
            ]

        return roadmap

    def _salary_intelligence(
        self,
        review: Dict[str, Any],
        score: float,
    ) -> Dict[str, Any]:
        title = (
            review.get(
                "job_title"
            )
            or ""
        ).lower()

        industry = (
            review.get(
                "industry"
            )
            or ""
        ).lower()

        if any(
            term in title
            for term in (
                "graduate",
                "intern",
                "trainee",
            )
        ):
            low, high = 250, 700
            market_label = (
                "Graduate / entry-level"
            )

        elif (
            "data" in title
            or "analyst" in title
        ):
            low, high = 600, 1500
            market_label = (
                "Data / analytics"
            )

        elif (
            "finance" in title
            or "accounting" in industry
        ):
            low, high = 500, 1200
            market_label = (
                "Finance / accounting"
            )

        else:
            low, high = 400, 1000
            market_label = (
                "General professional"
            )

        if score >= 88:
            recommended = int(
                high * 0.85
            )

        elif score >= 75:
            recommended = int(
                (low + high) / 2
            )

        else:
            recommended = int(
                low * 1.1
            )

        return {
            "currency": "USD",
            "market_category": (
                market_label
            ),
            "estimated_range": (
                f"${low} - ${high}"
            ),
            "recommended_asking_salary": (
                f"${recommended}"
            ),
            "recommended_positioning": (
                "Heuristic estimate only. "
                f"Indicative positioning is around "
                f"${recommended}, subject to employer "
                "budget, location, benefits and "
                "verified experience. This estimate "
                "is not based on live market data."
            ),
            "confidence": (
                "Heuristic only; "
                "not market-verified"
            ),
        }

    def _summary(
        self,
        review: dict[str, Any],
        score: float,
        *,
        job_context_available: bool,
    ) -> str:
        recommendation = (
            self._recommendation(
                score,
                job_context_available=(
                    job_context_available
                ),
            )
        )

        job_title = (
            review.get(
                "job_title"
            )
            or "the target role"
        )

        if not job_context_available:
            return (
                f"{recommendation}. The profile shows "
                "candidate evidence that can be "
                "reviewed, but job-fit conclusions "
                "require a specific job description."
            )

        return (
            f"{recommendation} for {job_title}. "
            "The score is based on visible CV evidence "
            "and job requirements. Final suitability "
            "must still be confirmed through interview "
            "evidence, reference checks and practical "
            "examples."
        )


candidate_intelligence = CandidateIntelligence()
