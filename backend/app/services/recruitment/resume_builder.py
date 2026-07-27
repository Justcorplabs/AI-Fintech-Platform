from typing import Dict, Any, List

from app.services.recruitment.resume_intelligence import resume_intelligence
from app.services.recruitment.recruiter_rewriter import recruiter_rewriter
from app.services.recruitment.achievement_extractor import achievement_extractor
from app.services.recruitment.evidence_validator import evidence_validator
from app.services.recruitment.professional_polisher import professional_polisher


class ResumeBuilder:
    def build(self, raw_text: str, review: Dict[str, Any]) -> Dict[str, Any]:
        resume_profile = resume_intelligence.analyse(raw_text)
        coach = review.get("cv_coach", {}) or {}

        core_skills = self._core_skills(resume_profile, review)
        technical_skills = self._technical_skills(resume_profile, review)

        built_resume = {
            "header": resume_profile.get("header", {}),
            "target_role": review.get("job_title", "Target Role"),
            "target_organisation": review.get("organisation", "Target Organisation"),
            "ats_metadata": {
                "current_ats_score": review.get("ats_score"),
                "estimated_optimized_score": coach.get("estimated_new_score"),
                "industry": review.get("industry"),
                "job_match_score": review.get("job_match_score"),
            },
            "professional_summary": recruiter_rewriter.human_summary(
                resume_summary=resume_profile.get("summary", ""),
                review=review,
                skills=core_skills + technical_skills,
            ),
            "key_achievements": achievement_extractor.extract(
                resume_profile=resume_profile,
                review=review,
            ),
            "core_skills": core_skills,
            "technical_skills": technical_skills,
            "professional_experience": self._experience(resume_profile, review),
            "education": self._education(resume_profile, review),
            "projects": self._projects(resume_profile),
            "recommended_projects": [],
            "certifications": self._certifications(resume_profile),
            "recommended_certifications": [],
            "languages": self._languages(resume_profile),
            "references": self._references(resume_profile),
            "cover_letter": "",
            "recruiter_notes": self._recruiter_notes(review),
        }

        validated_resume = evidence_validator.validate_built_resume(
            built_resume=built_resume,
            resume_profile=resume_profile,
            raw_text=raw_text,
        )

        polished_resume = professional_polisher.polish(
            built_resume=validated_resume,
            resume_profile=resume_profile,
        )

        polished_resume["cover_letter"] = self._safe_cover_letter(polished_resume)

        return polished_resume

    def _safe_cover_letter(self, built_resume: Dict[str, Any]) -> str:
        header = built_resume.get("header", {}) or {}
        name = header.get("name") or "Candidate"

        target_role = built_resume.get("target_role") or "the advertised role"
        organisation = built_resume.get("target_organisation") or "your organisation"

        if str(organisation).lower() in ["your organisation", "target organisation", "not detected"]:
            organisation_text = "your organisation"
        else:
            organisation_text = organisation

        summary = built_resume.get("professional_summary") or ""

        core_skills = built_resume.get("core_skills", []) or []
        technical_skills = built_resume.get("technical_skills", []) or []

        verified_skills = []
        for skill in [*core_skills, *technical_skills]:
            if skill and skill not in verified_skills:
                verified_skills.append(skill)

        skill_sentence = self._skill_sentence(verified_skills)

        experience_focus = self._experience_focus(built_resume)

        return (
            "Dear Hiring Team,\n\n"
            f"I am writing to express my interest in the {target_role} position at {organisation_text}. "
            f"{summary}\n\n"
            f"My background has given me practical exposure to {skill_sentence}. "
            f"{experience_focus} I am confident in my ability to learn quickly, work accurately, maintain confidentiality, "
            "and contribute positively to team objectives.\n\n"
            f"I would welcome the opportunity to discuss how my background can support the requirements of the {target_role} role at {organisation_text}.\n\n"
            "Yours faithfully,\n"
            f"{name}"
        )

    def _skill_sentence(self, skills: List[str]) -> str:
        if not skills:
            return "accurate documentation, reporting support and professional communication"

        selected = skills[:6]

        if len(selected) == 1:
            return selected[0]

        if len(selected) == 2:
            return f"{selected[0]} and {selected[1]}"

        return ", ".join(selected[:-1]) + f", and {selected[-1]}"

    def _experience_focus(self, built_resume: Dict[str, Any]) -> str:
        experience = built_resume.get("professional_experience", []) or []

        if not experience:
            return "I bring a strong willingness to apply my academic background and practical skills in a structured professional environment."

        first = experience[0]
        role = first.get("role") or "relevant experience"
        organisation = first.get("organisation") or ""

        if organisation:
            return (
                f"Through my experience as {role} at {organisation}, I developed strong discipline in handling records, "
                "supporting reporting tasks and following workplace procedures."
            )

        return (
            f"Through my experience as {role}, I developed strong discipline in handling records, "
            "supporting reporting tasks and following workplace procedures."
        )

    def _core_skills(self, resume_profile: Dict[str, Any], review: Dict[str, Any]) -> List[str]:
        technical_terms = self._technical_skill_names()
        skills = []

        for group in [
            resume_profile.get("skills", []),
            review.get("found_keywords", []),
            review.get("soft_skills_required", []),
            review.get("technical_skills_required", []),
        ]:
            for skill in group:
                pretty = self._pretty(skill)
                if pretty.lower() not in technical_terms and pretty not in skills:
                    skills.append(pretty)

        return skills[:18]

    def _technical_skills(self, resume_profile: Dict[str, Any], review: Dict[str, Any]) -> List[str]:
        technical_terms = self._technical_skill_names()
        skills = []

        for group in [
            resume_profile.get("skills", []),
            review.get("software_tools_required", []),
            review.get("found_keywords", []),
        ]:
            for skill in group:
                pretty = self._pretty(skill)
                if pretty.lower() in technical_terms and pretty not in skills:
                    skills.append(pretty)

        return skills[:16]

    def _experience(self, resume_profile: Dict[str, Any], review: Dict[str, Any]) -> List[Dict[str, Any]]:
        real_experience = resume_profile.get("experience", []) or []
        coach = review.get("cv_coach", {}) or {}
        fallback_bullets = coach.get("experience_rewrite", []) or []

        if not real_experience:
            return [
                {
                    "role": "Relevant Experience",
                    "organisation": "",
                    "period": "",
                    "bullets": recruiter_rewriter.rewrite_bullets(
                        bullets=fallback_bullets,
                        review=review,
                    ),
                }
            ]

        optimized = []

        for item in real_experience:
            rewritten_bullets = recruiter_rewriter.rewrite_bullets(
                bullets=item.get("bullets", []) or [],
                review=review,
                fallback_bullets=fallback_bullets,
            )

            optimized.append(
                {
                    "role": item.get("role") or "Relevant Experience",
                    "organisation": item.get("organisation") or "",
                    "period": item.get("period") or "",
                    "bullets": rewritten_bullets,
                }
            )

        return optimized[:6]

    def _education(self, resume_profile: Dict[str, Any], review: Dict[str, Any]) -> List[str]:
        education_entries = resume_profile.get("education", []) or []
        output = []

        for item in education_entries:
            qualification = item.get("qualification", "")
            institution = item.get("institution", "")
            period = item.get("period", "")

            line = qualification

            if institution:
                line += f" — {institution}"

            if period and period not in line:
                line += f" ({period})"

            if line.strip():
                output.append(line)

        if output:
            return output[:8]

        degree_requirements = review.get("degree_requirements", []) or []

        if degree_requirements:
            return [
                "Degree or academic background aligned to: "
                + ", ".join([self._pretty(x) for x in degree_requirements])
            ]

        return ["Relevant academic qualifications"]

    def _projects(self, resume_profile: Dict[str, Any]) -> List[str]:
        existing_projects = resume_profile.get("projects", []) or []
        output = []

        for project in existing_projects:
            name = project.get("name") if isinstance(project, dict) else str(project)
            description = project.get("description", "") if isinstance(project, dict) else ""

            if name and name not in output:
                output.append(f"{name}: {description}" if description else name)

        return output[:8]

    def _certifications(self, resume_profile: Dict[str, Any]) -> List[str]:
        certs = list(resume_profile.get("certifications", []) or [])
        return certs[:8]

    def _languages(self, resume_profile: Dict[str, Any]) -> List[str]:
        languages = resume_profile.get("languages", []) or ["English"]
        cleaned = []

        for lang in languages:
            text = str(lang).strip()
            lower = text.lower()

            if not text:
                continue

            if "reference" in lower or "phone" in lower or "email" in lower:
                continue

            if "interest" in lower or "football" in lower or "cricket" in lower:
                continue

            if text not in cleaned:
                cleaned.append(text)

        return cleaned[:5] or ["English"]

    def _references(self, resume_profile: Dict[str, Any]) -> str:
        references = resume_profile.get("references", []) or []
        cleaned = []

        for ref in references:
            text = str(ref).strip()
            if not text:
                continue

            lower = text.lower()
            if lower in ["reference", "references", "professional references"]:
                continue

            if lower in ["english", "shona", "ndebele"]:
                continue

            cleaned.append(text)

        if not cleaned:
            return "Available upon request."

        return "\n".join(cleaned[:10])

    def _recruiter_notes(self, review: Dict[str, Any]) -> List[str]:
        coach = review.get("cv_coach", {}) or {}
        recruiter_view = coach.get("recruiter_view", {}) or {}

        notes = [
            recruiter_view.get("recommendation", "Candidate requires recruiter review."),
            f"Current ATS Score: {review.get('ats_score')}%",
            f"Job Match Score: {review.get('job_match_score')}%",
        ]

        missing = review.get("missing_keywords", []) or []
        if missing:
            notes.append("Main missing requirements: " + ", ".join(missing[:8]))

        return notes

    def _pretty(self, text: str) -> str:
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

        value = str(text).strip()

        if value.lower() in acronyms:
            return acronyms[value.lower()]

        return value.title()

    def _technical_skill_names(self):
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
        }


resume_builder = ResumeBuilder()