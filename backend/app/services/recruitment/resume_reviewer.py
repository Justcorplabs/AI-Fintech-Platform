from typing import Any, List, Optional

from app.services.recruitment.ats_scorer import (
    ats_scorer,
)
from app.services.recruitment.cover_letter_generator import (
    cover_letter_generator,
)
from app.services.recruitment.cv_parser import (
    cv_parser,
)
from app.services.recruitment.interview_generator import (
    interview_generator,
)
from app.services.recruitment.job_intelligence import (
    job_intelligence,
)
from app.services.recruitment.keyword_extractor import (
    keyword_extractor,
)


class ResumeReviewer:
    def review_resume(
        self,
        raw_text: str,
        target_keywords: Optional[List[str]] = None,
        job_description: Optional[str] = None,
    ) -> dict[str, Any]:
        resume_text = (
            raw_text or ""
        ).lower()

        job_description_text = (
            job_description or ""
        ).strip()

        job_text = (
            job_description_text.lower()
        )

        job_profile = (
            job_intelligence.analyse(
                job_description_text
            )
        )

        job_keywords = (
            job_profile.get(
                "keywords",
                [],
            )
            or []
        )

        if (
            not job_keywords
            and job_description_text
        ):
            job_keywords = (
                keyword_extractor
                .extract_from_job(
                    job_text
                )
            )

        job_context_available = bool(
            job_description_text
            or target_keywords
        )

        if target_keywords:
            selected_keywords = (
                target_keywords
            )

        elif job_keywords:
            selected_keywords = (
                job_keywords
            )

        else:
            selected_keywords = (
                keyword_extractor
                .DOMAIN_KEYWORDS
            )

        active_keywords = (
            self._normalise_keywords(
                selected_keywords
            )
        )

        found_keywords = (
            keyword_extractor
            .find_in_resume(
                resume_text,
                active_keywords,
            )
        )

        found_keywords = (
            self._normalise_keywords(
                found_keywords
            )
        )

        found_norm = {
            keyword_extractor.normalise(
                keyword
            )
            for keyword in found_keywords
        }

        missing_keywords = [
            keyword
            for keyword in active_keywords
            if (
                keyword_extractor.normalise(
                    keyword
                )
                not in found_norm
            )
        ]

        parsed_candidate = (
            cv_parser.parse(
                raw_text
            )
        )

        score_parts = {
            "contact_score": (
                ats_scorer.contact_score(
                    raw_text
                )
            ),
            "skills_score": (
                ats_scorer.skills_score(
                    found_keywords,
                    active_keywords,
                )
            ),
            "education_score": (
                ats_scorer.education_score(
                    raw_text,
                    parsed_candidate.get(
                        "education_level"
                    ),
                )
            ),
            "experience_score": (
                ats_scorer.experience_score(
                    raw_text,
                    parsed_candidate.get(
                        "experience_years"
                    ),
                )
            ),
            "formatting_score": (
                ats_scorer.formatting_score(
                    raw_text
                )
            ),
            "achievement_score": (
                ats_scorer.achievement_score(
                    raw_text
                )
            ),
            "job_match_score": (
                ats_scorer.job_match_score(
                    found_keywords,
                    active_keywords,
                )
                if job_context_available
                else 0.0
            ),
        }

        ats_score = (
            ats_scorer.final_score(
                score_parts,
                job_context_available=(
                    job_context_available
                ),
            )
        )

        job_title = (
            job_profile.get(
                "job_title"
            )
            or "Target Role"
        )

        organisation = (
            job_profile.get(
                "organisation"
            )
            or "Not detected"
        )

        industry = (
            job_profile.get(
                "industry"
            )
            or "General"
        )

        professional_summary = (
            self._professional_summary(
                job_title=job_title,
                industry=industry,
                found_keywords=(
                    found_keywords
                ),
            )
        )

        legacy_summary = (
            cover_letter_generator
            .professional_summary(
                found_keywords=(
                    found_keywords
                ),
                education_score=(
                    score_parts[
                        "education_score"
                    ]
                ),
                experience_score=(
                    score_parts[
                        "experience_score"
                    ]
                ),
                job_title=job_title,
            )
        )

        legacy_cover_letter = (
            cover_letter_generator
            .cover_letter(
                professional_summary=(
                    legacy_summary
                ),
                found_keywords=(
                    found_keywords
                ),
                job_title=job_title,
                organisation=organisation,
            )
        )

        review = {
            "ats_score": ats_score,
            "job_match_score": (
                score_parts[
                    "job_match_score"
                ]
            ),
            "skills_score": (
                score_parts[
                    "skills_score"
                ]
            ),
            "interview_probability": (
                self._interview_probability(
                    ats_score,
                    score_parts,
                    job_context_available=(
                        job_context_available
                    ),
                )
            ),
            "education_score": (
                score_parts[
                    "education_score"
                ]
            ),
            "experience_score": (
                score_parts[
                    "experience_score"
                ]
            ),
            "achievement_score": (
                score_parts[
                    "achievement_score"
                ]
            ),
            "contact_score": (
                score_parts[
                    "contact_score"
                ]
            ),
            "formatting_score": (
                score_parts[
                    "formatting_score"
                ]
            ),
            "job_title": job_title,
            "organisation": organisation,
            "industry": industry,
            "location": job_profile.get(
                "location"
            ),
            "deadline": job_profile.get(
                "deadline"
            ),
            "application_email": (
                job_profile.get(
                    "application_email"
                )
            ),
            "experience_requirement": (
                job_profile.get(
                    "experience_requirement"
                )
            ),
            "technical_skills_required": (
                job_profile.get(
                    "technical_requirements",
                    [],
                )
            ),
            "software_tools_required": (
                job_profile.get(
                    "software_tools",
                    [],
                )
            ),
            "soft_skills_required": (
                job_profile.get(
                    "soft_skills",
                    [],
                )
            ),
            "degree_requirements": (
                job_profile.get(
                    "degree_requirements",
                    [],
                )
            ),
            "responsibilities": (
                job_profile.get(
                    "responsibilities",
                    [],
                )
            ),
            "qualifications": (
                job_profile.get(
                    "qualifications",
                    [],
                )
            ),
            "found_keywords": (
                found_keywords
            ),
            "missing_keywords": (
                missing_keywords
            ),
            "strengths": self._strengths(
                found_keywords,
                score_parts,
            ),
            "improvements": (
                self._improvements(
                    missing_keywords,
                    score_parts,
                    job_context_available=(
                        job_context_available
                    ),
                )
            ),
            "professional_summary": (
                professional_summary
            ),
            "cover_letter": (
                legacy_cover_letter
            ),
            "interview_questions": (
                interview_generator
                .generate(
                    job_title=job_title,
                    found_keywords=(
                        found_keywords
                    ),
                    missing_keywords=(
                        missing_keywords
                    ),
                )
            ),
            "job_profile": job_profile,
            "parsed_candidate": (
                parsed_candidate
            ),
            "score_components": (
                score_parts
            ),
            "scoring_context": {
                "job_context_available": (
                    job_context_available
                ),
                "keyword_source": (
                    "target_keywords"
                    if target_keywords
                    else (
                        "job_description"
                        if job_keywords
                        else "general_domain"
                    )
                ),
            },
        }

        review["cv_coach"] = (
            self._cv_coach(
                review
            )
        )

        return review

    def _normalise_keywords(
        self,
        values: List[str],
    ) -> List[str]:
        output: list[str] = []
        seen: set[str] = set()

        for value in values or []:
            normalised = (
                keyword_extractor.normalise(
                    str(value)
                )
            )

            normalised = (
                str(normalised or "")
                .strip()
                .lower()
            )

            if (
                not normalised
                or normalised in seen
            ):
                continue

            seen.add(
                normalised
            )
            output.append(
                normalised
            )

        return output

    def _interview_probability(
        self,
        ats_score: float,
        score_parts: dict[str, Any],
        *,
        job_context_available: bool,
    ) -> float:
        if job_context_available:
            probability = (
                0.35 * ats_score
                + 0.35
                * score_parts.get(
                    "job_match_score",
                    0,
                )
                + 0.20
                * score_parts.get(
                    "experience_score",
                    0,
                )
                + 0.10
                * score_parts.get(
                    "education_score",
                    0,
                )
            )

        else:
            probability = (
                0.55 * ats_score
                + 0.25
                * score_parts.get(
                    "experience_score",
                    0,
                )
                + 0.20
                * score_parts.get(
                    "education_score",
                    0,
                )
            )

        return round(
            min(
                95.0,
                max(0.0, probability),
            ),
            2,
        )

    def _professional_summary(
        self,
        job_title: str,
        industry: str,
        found_keywords: List[str],
    ) -> str:
        skills = [
            str(skill).strip()
            for skill in found_keywords
            if str(skill).strip()
        ][:6]

        if skills:
            skill_text = ", ".join(
                skills
            )

            return (
                f"Motivated candidate targeting "
                f"{job_title} within {industry}. "
                f"Brings visible CV evidence of "
                f"{skill_text}, with the ability to "
                "support accurate work, reporting, "
                "analysis, communication and effective "
                "team operations."
            )

        return (
            f"Motivated candidate targeting "
            f"{job_title} within {industry}, with "
            "attention to detail, willingness to learn "
            "and the ability to support accurate "
            "documentation and team objectives."
        )

    def _strengths(
        self,
        found_keywords: List[str],
        scores: dict[str, Any],
    ) -> List[str]:
        strengths: list[str] = []

        if found_keywords:
            strengths.append(
                (
                    "The CV contains visible evidence "
                    "of relevant skills or keywords."
                )
            )

        if (
            scores.get(
                "job_match_score",
                0,
            )
            >= 70
        ):
            strengths.append(
                (
                    "Good alignment between the CV "
                    "and the structured job profile."
                )
            )

        if (
            scores.get(
                "education_score",
                0,
            )
            >= 70
        ):
            strengths.append(
                (
                    "Relevant education evidence is "
                    "visible in the CV."
                )
            )

        if (
            scores.get(
                "experience_score",
                0,
            )
            >= 60
        ):
            strengths.append(
                (
                    "Relevant work, internship, "
                    "attachment or practical experience "
                    "is visible."
                )
            )

        if (
            scores.get(
                "achievement_score",
                0,
            )
            >= 60
        ):
            strengths.append(
                (
                    "The CV includes measurable or "
                    "outcome-focused achievements."
                )
            )

        if (
            scores.get(
                "formatting_score",
                0,
            )
            >= 70
        ):
            strengths.append(
                (
                    "The resume structure appears "
                    "clear and ATS-friendly."
                )
            )

        return strengths or [
            (
                "The candidate profile requires "
                "stronger evidence before a reliable "
                "strength assessment can be made."
            )
        ]

    def _improvements(
        self,
        missing_keywords: List[str],
        scores: dict[str, Any],
        *,
        job_context_available: bool,
    ) -> List[str]:
        improvements: list[str] = []

        if (
            job_context_available
            and missing_keywords
        ):
            improvements.append(
                (
                    "Add or make more visible truthful "
                    "evidence for role requirements "
                    "such as: "
                    + ", ".join(
                        missing_keywords[:8]
                    )
                    + "."
                )
            )

        if (
            scores.get(
                "achievement_score",
                0,
            )
            < 60
        ):
            improvements.append(
                (
                    "Quantify truthful achievements "
                    "using numbers, reports, datasets, "
                    "records, transactions or impact."
                )
            )

        if (
            scores.get(
                "formatting_score",
                0,
            )
            < 70
        ):
            improvements.append(
                (
                    "Use clear headings, concise bullet "
                    "points and consistent section "
                    "structure."
                )
            )

        if (
            scores.get(
                "contact_score",
                0,
            )
            < 80
        ):
            improvements.append(
                (
                    "Make essential professional contact "
                    "details clearly visible."
                )
            )

        improvements.append(
            (
                "Use strong action verbs and remove "
                "unsupported generic claims."
            )
        )

        return improvements

    def _cv_coach(
        self,
        review: dict[str, Any],
    ) -> dict[str, Any]:
        current = float(
            review.get(
                "ats_score"
            )
            or 0
        )

        contact = float(
            review.get(
                "contact_score"
            )
            or 0
        )

        formatting = float(
            review.get(
                "formatting_score"
            )
            or 0
        )

        achievements = float(
            review.get(
                "achievement_score"
            )
            or 0
        )

        potential_gain = 0.0

        potential_gain += min(
            4.0,
            max(
                0.0,
                (100 - contact) * 0.04,
            ),
        )

        potential_gain += min(
            4.0,
            max(
                0.0,
                (80 - formatting) * 0.08,
            ),
        )

        potential_gain += min(
            4.0,
            max(
                0.0,
                (70 - achievements) * 0.06,
            ),
        )

        scoring_context = (
            review.get(
                "scoring_context",
                {},
            )
            or {}
        )

        if (
            scoring_context.get(
                "job_context_available"
            )
        ):
            potential_gain += min(
                2.0,
                len(
                    review.get(
                        "missing_keywords",
                        [],
                    )
                    or []
                )
                * 0.25,
            )

        potential_gain = min(
            12.0,
            potential_gain,
        )

        estimated = min(
            100.0,
            current + potential_gain,
        )

        return {
            "current_ats": round(
                current,
                2,
            ),
            "estimated_new_score": round(
                estimated,
                2,
            ),
            "estimated_gain": round(
                estimated - current,
                2,
            ),
            "current_rating": (
                self._stars(
                    current
                )
            ),
            "improved_rating": (
                self._stars(
                    estimated
                )
            ),
            "recommendation": (
                (
                    "Strong interview potential after "
                    "truthful presentation improvements."
                )
                if estimated >= 75
                else (
                    "Candidate needs targeted, truthful "
                    "improvements before application."
                )
            ),
            "recommended_summary": (
                review.get(
                    "professional_summary"
                )
            ),
            "skills_to_add": (
                review.get(
                    "missing_keywords",
                    [],
                )[:8]
            ),
            "experience_rewrite": [],
            "suggested_projects": [],
            "priority_missing_requirements": (
                review.get(
                    "missing_keywords",
                    [],
                )[:8]
            ),
            "recruiter_view": {
                "recommendation": (
                    (
                        "Recommended for recruiter "
                        "review."
                    )
                    if estimated >= 70
                    else (
                        "Requires stronger evidence "
                        "before recruiter review."
                    )
                )
            },
        }

    def _stars(
        self,
        score: float,
    ) -> str:
        if score >= 85:
            return "★★★★★"

        if score >= 70:
            return "★★★★☆"

        if score >= 55:
            return "★★★☆☆"

        if score >= 40:
            return "★★☆☆☆"

        return "★☆☆☆☆"


resume_reviewer = ResumeReviewer()