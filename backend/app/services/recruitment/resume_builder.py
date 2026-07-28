from typing import Any, List

from app.services.recruitment.achievement_extractor import (
    achievement_extractor,
)
from app.services.recruitment.evidence_validator import (
    evidence_validator,
)
from app.services.recruitment.professional_polisher import (
    professional_polisher,
)
from app.services.recruitment.recruiter_rewriter import (
    recruiter_rewriter,
)
from app.services.recruitment.resume_intelligence import (
    resume_intelligence,
)


class ResumeBuilder:
    def build(
        self,
        raw_text: str,
        review: dict[str, Any],
    ) -> dict[str, Any]:
        resume_profile = (
            resume_intelligence.analyse(
                raw_text
            )
        )

        coach = (
            review.get(
                "cv_coach",
                {},
            )
            or {}
        )

        core_skills = self._core_skills(
            resume_profile,
            review,
        )

        technical_skills = (
            self._technical_skills(
                resume_profile,
                review,
            )
        )

        professional_experience = (
            self._experience(
                resume_profile,
                review,
            )
        )

        education = self._education(
            resume_profile,
            review,
        )

        projects = self._projects(
            resume_profile
        )

        certifications = (
            self._certifications(
                resume_profile
            )
        )

        key_achievements = (
            achievement_extractor.extract(
                resume_profile=(
                    resume_profile
                ),
                review=review,
            )
        )

        built_resume = {
            "header": (
                resume_profile.get(
                    "header",
                    {},
                )
            ),
            "target_role": (
                review.get(
                    "job_title",
                    "Target Role",
                )
            ),
            "target_organisation": (
                review.get(
                    "organisation",
                    "Target Organisation",
                )
            ),
            "ats_metadata": {
                "current_ats_score": (
                    review.get(
                        "ats_score"
                    )
                ),
                "estimated_optimized_score": (
                    coach.get(
                        "estimated_new_score"
                    )
                ),
                "industry": (
                    review.get(
                        "industry"
                    )
                ),
                "job_match_score": (
                    review.get(
                        "job_match_score"
                    )
                ),
            },
            "professional_summary": (
                recruiter_rewriter
                .human_summary(
                    resume_summary=(
                        resume_profile.get(
                            "summary",
                            "",
                        )
                    ),
                    review=review,
                    skills=(
                        core_skills
                        + technical_skills
                    ),
                )
            ),
            "key_achievements": (
                key_achievements
            ),
            "core_skills": (
                core_skills
            ),
            "technical_skills": (
                technical_skills
            ),
            "professional_experience": (
                professional_experience
            ),
            "education": education,
            "projects": projects,
            "recommended_projects": [],
            "certifications": (
                certifications
            ),
            "recommended_certifications": [],
            "languages": (
                self._languages(
                    resume_profile
                )
            ),
            "references": (
                self._references(
                    resume_profile
                )
            ),
            "cover_letter": "",
            "recruiter_notes": (
                self._recruiter_notes(
                    review
                )
            ),
            "evidence_metadata": {
                "experience_present": bool(
                    professional_experience
                ),
                "education_present": bool(
                    education
                ),
                "projects_present": bool(
                    projects
                ),
                "certifications_present": bool(
                    certifications
                ),
                "achievements_present": bool(
                    key_achievements
                ),
                "job_requirements_added_as_candidate_evidence": (
                    False
                ),
            },
        }

        validated_resume = (
            evidence_validator
            .validate_built_resume(
                built_resume=(
                    built_resume
                ),
                resume_profile=(
                    resume_profile
                ),
                raw_text=raw_text,
            )
        )

        polished_resume = (
            professional_polisher.polish(
                built_resume=(
                    validated_resume
                ),
                resume_profile=(
                    resume_profile
                ),
            )
        )

        polished_resume[
            "cover_letter"
        ] = self._safe_cover_letter(
            polished_resume
        )

        return polished_resume

    def _safe_cover_letter(
        self,
        built_resume: dict[str, Any],
    ) -> str:
        header = (
            built_resume.get(
                "header",
                {},
            )
            or {}
        )

        name = (
            header.get(
                "name"
            )
            or "Candidate"
        )

        target_role = (
            built_resume.get(
                "target_role"
            )
            or "the advertised role"
        )

        organisation = (
            built_resume.get(
                "target_organisation"
            )
            or "your organisation"
        )

        if (
            str(organisation).lower()
            in {
                "your organisation",
                "target organisation",
                "not detected",
            }
        ):
            organisation_text = (
                "your organisation"
            )

        else:
            organisation_text = (
                organisation
            )

        summary = (
            built_resume.get(
                "professional_summary"
            )
            or ""
        )

        core_skills = (
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

        verified_skills: list[str] = []

        for skill in [
            *core_skills,
            *technical_skills,
        ]:
            if (
                skill
                and skill
                not in verified_skills
            ):
                verified_skills.append(
                    skill
                )

        skill_sentence = (
            self._skill_sentence(
                verified_skills
            )
        )

        experience_focus = (
            self._experience_focus(
                built_resume
            )
        )

        return (
            "Dear Hiring Team,\n\n"
            f"I am writing to express my interest "
            f"in the {target_role} position at "
            f"{organisation_text}. {summary}\n\n"
            f"My CV shows exposure to "
            f"{skill_sentence}. "
            f"{experience_focus} "
            "I am prepared to learn, work accurately, "
            "maintain confidentiality and contribute "
            "positively to team objectives.\n\n"
            "I would welcome the opportunity to discuss "
            "how my verified background can support the "
            f"requirements of the {target_role} role at "
            f"{organisation_text}.\n\n"
            "Yours faithfully,\n"
            f"{name}"
        )

    def _skill_sentence(
        self,
        skills: List[str],
    ) -> str:
        if not skills:
            return (
                "documentation, reporting support and "
                "professional communication where these "
                "are evidenced in the CV"
            )

        selected = skills[:6]

        if len(selected) == 1:
            return selected[0]

        if len(selected) == 2:
            return (
                f"{selected[0]} and "
                f"{selected[1]}"
            )

        return (
            ", ".join(
                selected[:-1]
            )
            + f", and {selected[-1]}"
        )

    def _experience_focus(
        self,
        built_resume: dict[str, Any],
    ) -> str:
        experience = (
            built_resume.get(
                "professional_experience",
                [],
            )
            or []
        )

        if not experience:
            return (
                "Where direct work experience is "
                "limited, I am ready to explain relevant "
                "academic, project or training evidence "
                "during the interview."
            )

        first = experience[0]

        role = (
            first.get(
                "role"
            )
            or "a relevant role"
        )

        organisation = (
            first.get(
                "organisation"
            )
            or ""
        )

        if organisation:
            return (
                f"Through my verified experience as "
                f"{role} at {organisation}, I developed "
                "discipline in following workplace "
                "procedures and supporting assigned "
                "responsibilities."
            )

        return (
            f"Through my verified experience as "
            f"{role}, I developed discipline in "
            "following workplace procedures and "
            "supporting assigned responsibilities."
        )

    def _core_skills(
        self,
        resume_profile: dict[str, Any],
        review: dict[str, Any],
    ) -> List[str]:
        technical_terms = (
            self._technical_skill_names()
        )

        skills: list[str] = []

        # Only candidate evidence is used. Job requirements
        # are not added to the candidate's CV.
        for group in [
            resume_profile.get(
                "skills",
                [],
            ),
            review.get(
                "found_keywords",
                [],
            ),
        ]:
            for skill in group or []:
                pretty = self._pretty(
                    skill
                )

                if (
                    pretty.lower()
                    not in technical_terms
                    and pretty
                    not in skills
                ):
                    skills.append(
                        pretty
                    )

        return skills[:18]

    def _technical_skills(
        self,
        resume_profile: dict[str, Any],
        review: dict[str, Any],
    ) -> List[str]:
        technical_terms = (
            self._technical_skill_names()
        )

        skills: list[str] = []

        # Required tools are excluded unless they were
        # actually found in the candidate's CV.
        for group in [
            resume_profile.get(
                "skills",
                [],
            ),
            review.get(
                "found_keywords",
                [],
            ),
        ]:
            for skill in group or []:
                pretty = self._pretty(
                    skill
                )

                if (
                    pretty.lower()
                    in technical_terms
                    and pretty
                    not in skills
                ):
                    skills.append(
                        pretty
                    )

        return skills[:16]

    def _experience(
        self,
        resume_profile: dict[str, Any],
        review: dict[str, Any],
    ) -> List[dict[str, Any]]:
        real_experience = (
            resume_profile.get(
                "experience",
                [],
            )
            or []
        )

        if not real_experience:
            return []

        optimized: list[
            dict[str, Any]
        ] = []

        for item in real_experience:
            source_bullets = (
                item.get(
                    "bullets",
                    [],
                )
                or []
            )

            rewritten_bullets = (
                recruiter_rewriter
                .rewrite_bullets(
                    bullets=(
                        source_bullets
                    ),
                    review=review,
                    fallback_bullets=[],
                )
            )

            optimized.append(
                {
                    "role": (
                        item.get(
                            "role"
                        )
                        or "Relevant Experience"
                    ),
                    "organisation": (
                        item.get(
                            "organisation"
                        )
                        or ""
                    ),
                    "period": (
                        item.get(
                            "period"
                        )
                        or ""
                    ),
                    "bullets": (
                        rewritten_bullets
                    ),
                }
            )

        return optimized[:6]

    def _education(
        self,
        resume_profile: dict[str, Any],
        review: dict[str, Any],
    ) -> List[str]:
        del review

        education_entries = (
            resume_profile.get(
                "education",
                [],
            )
            or []
        )

        output: list[str] = []

        for item in education_entries:
            qualification = str(
                item.get(
                    "qualification",
                    "",
                )
                or ""
            ).strip()

            institution = str(
                item.get(
                    "institution",
                    "",
                )
                or ""
            ).strip()

            period = str(
                item.get(
                    "period",
                    "",
                )
                or ""
            ).strip()

            line = qualification

            if institution:
                line += (
                    f" — {institution}"
                    if line
                    else institution
                )

            if (
                period
                and period not in line
            ):
                line += (
                    f" ({period})"
                    if line
                    else period
                )

            if line.strip():
                output.append(
                    line.strip()
                )

        return output[:8]

    def _projects(
        self,
        resume_profile: dict[str, Any],
    ) -> List[str]:
        existing_projects = (
            resume_profile.get(
                "projects",
                [],
            )
            or []
        )

        output: list[str] = []

        for project in existing_projects:
            if isinstance(
                project,
                dict,
            ):
                name = project.get(
                    "name"
                )

                description = (
                    project.get(
                        "description",
                        "",
                    )
                )

            else:
                name = str(
                    project
                )

                description = ""

            if (
                name
                and name not in output
            ):
                output.append(
                    (
                        f"{name}: {description}"
                        if description
                        else str(name)
                    )
                )

        return output[:8]

    def _certifications(
        self,
        resume_profile: dict[str, Any],
    ) -> List[str]:
        certs = list(
            resume_profile.get(
                "certifications",
                [],
            )
            or []
        )

        return certs[:8]

    def _languages(
        self,
        resume_profile: dict[str, Any],
    ) -> List[str]:
        languages = (
            resume_profile.get(
                "languages",
                [],
            )
            or []
        )

        cleaned: list[str] = []

        for language in languages:
            text = str(
                language
            ).strip()

            lower = text.lower()

            if not text:
                continue

            if any(
                blocked in lower
                for blocked in (
                    "reference",
                    "phone",
                    "email",
                    "interest",
                    "football",
                    "cricket",
                )
            ):
                continue

            if text not in cleaned:
                cleaned.append(
                    text
                )

        return cleaned[:5]

    def _references(
        self,
        resume_profile: dict[str, Any],
    ) -> str:
        references = (
            resume_profile.get(
                "references",
                [],
            )
            or []
        )

        cleaned: list[str] = []

        for reference in references:
            text = str(
                reference
            ).strip()

            if not text:
                continue

            lower = text.lower()

            if lower in {
                "reference",
                "references",
                "professional references",
                "english",
                "shona",
                "ndebele",
            }:
                continue

            cleaned.append(
                text
            )

        if not cleaned:
            return (
                "Available upon request."
            )

        return "\n".join(
            cleaned[:10]
        )

    def _recruiter_notes(
        self,
        review: dict[str, Any],
    ) -> List[str]:
        coach = (
            review.get(
                "cv_coach",
                {},
            )
            or {}
        )

        recruiter_view = (
            coach.get(
                "recruiter_view",
                {},
            )
            or {}
        )

        notes = [
            recruiter_view.get(
                "recommendation",
                (
                    "Candidate requires recruiter "
                    "review."
                ),
            ),
            (
                "Current ATS Score: "
                f"{review.get('ats_score')}%"
            ),
            (
                "Job Match Score: "
                f"{review.get('job_match_score')}%"
            ),
        ]

        missing = (
            review.get(
                "missing_keywords",
                [],
            )
            or []
        )

        if missing:
            notes.append(
                (
                    "Main missing requirements: "
                    + ", ".join(
                        missing[:8]
                    )
                )
            )

        return notes

    def _pretty(
        self,
        text: str,
    ) -> str:
        acronyms = {
            "sql": "SQL",
            "ict": "ICT",
            "hr": "HR",
            "mel": "MEAL",
            "m&e": "M&E",
            "api": "API",
            "etl": "ETL",
            "vat": "VAT",
            "iso": "ISO",
            "sap": "SAP",
            "powerbi": "Power BI",
            "power bi": "Power BI",
            "excel": "Microsoft Excel",
        }

        value = str(
            text
        ).strip()

        if value.lower() in acronyms:
            return acronyms[
                value.lower()
            ]

        return value.title()

    def _technical_skill_names(
        self,
    ) -> set[str]:
        return {
            "python",
            "sql",
            "excel",
            "power bi",
            "powerbi",
            "r",
            "spss",
            "stata",
            "tableau",
            "quickbooks",
            "sap",
            "pastel",
            "microsoft excel",
            "microsoft office",
            "claims management systems",
            "database",
            "mysql",
            "postgresql",
            "sqlite",
            "fastapi",
            "docker",
            "git",
            "github",
            "scikit-learn",
            "tensorflow",
            "keras",
            "xgboost",
            "lightgbm",
            "catboost",
            "pandas",
            "numpy",
        }


resume_builder = ResumeBuilder()