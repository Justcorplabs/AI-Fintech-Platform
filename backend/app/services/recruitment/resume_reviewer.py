from typing import Dict, Any, List, Optional

from app.services.recruitment.job_intelligence import job_intelligence
from app.services.recruitment.keyword_extractor import keyword_extractor
from app.services.recruitment.ats_scorer import ats_scorer
from app.services.recruitment.cover_letter_generator import cover_letter_generator
from app.services.recruitment.interview_generator import interview_generator


class ResumeReviewer:
    def review_resume(
        self,
        raw_text: str,
        target_keywords: Optional[List[str]] = None,
        job_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        resume_text = raw_text.lower()
        job_text = (job_description or "").lower()

        job_profile = job_intelligence.analyse(job_description or "")
        job_keywords = job_profile.get("keywords", []) or []

        if not job_keywords and job_description:
            job_keywords = keyword_extractor.extract_from_job(job_text)

        active_keywords = target_keywords or job_keywords or keyword_extractor.DOMAIN_KEYWORDS

        found_keywords = keyword_extractor.find_in_resume(
            resume_text,
            active_keywords,
        )

        found_norm = [keyword_extractor.normalise(k) for k in found_keywords]

        missing_keywords = [
            keyword
            for keyword in active_keywords
            if keyword_extractor.normalise(keyword) not in found_norm
        ]

        score_parts = {
            "contact_score": ats_scorer.contact_score(raw_text),
            "skills_score": ats_scorer.skills_score(found_keywords, active_keywords),
            "education_score": ats_scorer.education_score(raw_text),
            "experience_score": ats_scorer.experience_score(raw_text),
            "formatting_score": ats_scorer.formatting_score(raw_text),
            "achievement_score": ats_scorer.achievement_score(raw_text),
            "job_match_score": ats_scorer.job_match_score(found_keywords, active_keywords),
        }

        ats_score = ats_scorer.final_score(score_parts)

        job_title = job_profile.get("job_title") or "Target Role"
        organisation = job_profile.get("organisation") or "Not detected"
        industry = job_profile.get("industry") or "General"

        professional_summary = self._professional_summary(
            job_title=job_title,
            industry=industry,
            found_keywords=found_keywords,
        )

        legacy_summary = cover_letter_generator.professional_summary(
            found_keywords=found_keywords,
            education_score=score_parts["education_score"],
            experience_score=score_parts["experience_score"],
            job_title=job_title,
        )

        legacy_cover_letter = cover_letter_generator.cover_letter(
            professional_summary=legacy_summary,
            found_keywords=found_keywords,
            job_title=job_title,
            organisation=organisation,
        )

        review = {
            "ats_score": ats_score,
            "job_match_score": score_parts["job_match_score"],
            "skills_score": score_parts["skills_score"],
            "interview_probability": self._interview_probability(ats_score, score_parts),
            "education_score": score_parts["education_score"],
            "experience_score": score_parts["experience_score"],
            "achievement_score": score_parts["achievement_score"],
            "contact_score": score_parts["contact_score"],
            "formatting_score": score_parts["formatting_score"],
            "job_title": job_title,
            "organisation": organisation,
            "industry": industry,
            "location": job_profile.get("location"),
            "deadline": job_profile.get("deadline"),
            "application_email": job_profile.get("application_email"),
            "experience_requirement": job_profile.get("experience_requirement"),
            "technical_skills_required": job_profile.get("technical_requirements", []),
            "software_tools_required": job_profile.get("software_tools", []),
            "soft_skills_required": job_profile.get("soft_skills", []),
            "degree_requirements": job_profile.get("degree_requirements", []),
            "responsibilities": job_profile.get("responsibilities", []),
            "qualifications": job_profile.get("qualifications", []),
            "found_keywords": found_keywords,
            "missing_keywords": missing_keywords,
            "strengths": self._strengths(found_keywords, score_parts),
            "improvements": self._improvements(missing_keywords),
            "professional_summary": professional_summary,
            "cover_letter": legacy_cover_letter,
            "interview_questions": interview_generator.generate(
                job_title=job_title,
                found_keywords=found_keywords,
                missing_keywords=missing_keywords,
            ),
            "job_profile": job_profile,
        }

        review["cv_coach"] = self._cv_coach(review)

        return review

    def _interview_probability(
        self,
        ats_score: float,
        score_parts: Dict[str, Any],
    ) -> float:
        probability = (
            0.45 * ats_score
            + 0.25 * score_parts.get("job_match_score", 0)
            + 0.15 * score_parts.get("experience_score", 0)
            + 0.15 * score_parts.get("education_score", 0)
        )

        return round(min(99, max(10, probability)), 2)

    def _professional_summary(
        self,
        job_title: str,
        industry: str,
        found_keywords: List[str],
    ) -> str:
        skills = [str(skill).strip() for skill in found_keywords if str(skill).strip()]
        skills = skills[:6]

        if skills:
            skill_text = ", ".join(skills)
            return (
                f"Motivated candidate targeting {job_title} within {industry}. "
                f"Brings practical exposure to {skill_text}, with the ability to support accurate work, "
                "prepare reports, analyse information, communicate clearly, and contribute to effective operations."
            )

        return (
            f"Motivated candidate targeting {job_title} within {industry}, with strong attention to detail, "
            "willingness to learn, and the ability to support accurate documentation, reporting, and team objectives."
        )

    def _strengths(self, found_keywords: List[str], scores: Dict[str, Any]) -> List[str]:
        strengths = []

        if found_keywords:
            strengths.append("The CV contains several relevant job requirements.")

        if scores.get("job_match_score", 0) >= 70:
            strengths.append("Good alignment between the CV and the structured job profile.")

        if scores.get("education_score", 0) >= 70:
            strengths.append("Strong education profile for the target role.")

        if scores.get("experience_score", 0) >= 60:
            strengths.append("Relevant work, internship, attachment, or practical experience detected.")

        strengths.append("Resume structure appears ATS-friendly and sectioned.")

        return strengths

    def _improvements(self, missing_keywords: List[str]) -> List[str]:
        improvements = []

        if missing_keywords:
            improvements.append(
                "Add or make more visible truthful evidence for role requirements such as: "
                + ", ".join(missing_keywords[:8])
                + "."
            )

        improvements.append("Tailor the professional summary and experience bullets more closely to the job profile.")
        improvements.append("Quantify achievements using numbers, reports, datasets, dashboards, records, transactions, or impact where truthful.")
        improvements.append("Use strong action verbs and remove generic statements like 'hardworking'.")

        return improvements

    def _cv_coach(self, review: Dict[str, Any]) -> Dict[str, Any]:
        current = float(review.get("ats_score") or 0)
        estimated = min(100, current + max(3, len(review.get("missing_keywords", [])) * 0.8))

        return {
            "current_ats": round(current, 2),
            "estimated_new_score": round(estimated, 2),
            "estimated_gain": round(estimated - current, 2),
            "current_rating": self._stars(current),
            "improved_rating": self._stars(estimated),
            "recommendation": (
                "Strong interview potential after truthful CV improvements."
                if estimated >= 75
                else "Candidate needs targeted improvements before application."
            ),
            "recommended_summary": review.get("professional_summary"),
            "skills_to_add": review.get("missing_keywords", [])[:8],
            "experience_rewrite": [],
            "suggested_projects": [],
            "priority_missing_requirements": review.get("missing_keywords", [])[:8],
            "recruiter_view": {
                "recommendation": (
                    "Recommended for recruiter review."
                    if estimated >= 70
                    else "Requires targeted improvement before recruiter review."
                )
            },
        }

    def _stars(self, score: float) -> str:
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