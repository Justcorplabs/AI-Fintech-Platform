from typing import Dict, Any, List

from app.services.recruitment.explainability_engine import explainability_engine


class CandidateIntelligence:
    def generate(
        self,
        review: Dict[str, Any],
        built_resume: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        built_resume = built_resume or {}

        ats_score = float(review.get("ats_score") or 0)
        job_match = float(review.get("job_match_score") or 0)
        education = float(review.get("education_score") or 0)
        experience = float(review.get("experience_score") or 0)
        achievements = float(review.get("achievement_score") or 0)

        recruiter_score = self._recruiter_score(
            ats_score=ats_score,
            job_match=job_match,
            education=education,
            experience=experience,
            achievements=achievements,
            built_resume=built_resume,
        )

        explainability = explainability_engine.generate(
            review=review,
            candidate_intelligence={
                "recruiter_score": recruiter_score,
            },
        )

        return {
            "overall_rating": self._letter_grade(recruiter_score),
            "recruiter_score": round(recruiter_score, 2),
            "hiring_recommendation": self._recommendation(recruiter_score),
            "confidence": self._confidence(review, built_resume),
            "candidate_strengths": self._strengths(review, built_resume),
            "hiring_risks": self._risks(review),
            "interview_readiness": self._interview_readiness(review, recruiter_score),
            "learning_roadmap": self._learning_roadmap(review),
            "salary_intelligence": self._salary_intelligence(review, recruiter_score),
            "recruiter_summary": self._summary(review, recruiter_score),
            "explainability": explainability,
        }

    def _recruiter_score(
        self,
        ats_score: float,
        job_match: float,
        education: float,
        experience: float,
        achievements: float,
        built_resume: Dict[str, Any],
    ) -> float:
        evidence_bonus = 0

        if built_resume.get("professional_experience"):
            evidence_bonus += 4

        if built_resume.get("certifications"):
            evidence_bonus += 2

        if built_resume.get("key_achievements"):
            evidence_bonus += 3

        score = (
            0.18 * ats_score
            + 0.22 * job_match
            + 0.22 * education
            + 0.22 * experience
            + 0.10 * achievements
            + evidence_bonus
        )

        return min(100, max(0, score))

    def _letter_grade(self, score: float) -> str:
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

    def _recommendation(self, score: float) -> str:
        if score >= 88:
            return "Highly Recommended for Interview"
        if score >= 78:
            return "Recommended for Interview"
        if score >= 68:
            return "Consider After Targeted CV Improvements"
        if score >= 55:
            return "Potential Candidate With Notable Gaps"
        return "Not Recommended Without Major Improvements"

    def _confidence(self, review: Dict[str, Any], built_resume: Dict[str, Any]) -> float:
        confidence = 70

        if review.get("semantic_results"):
            confidence += 8

        if built_resume.get("professional_experience"):
            confidence += 8

        if built_resume.get("education"):
            confidence += 5

        if built_resume.get("certifications"):
            confidence += 3

        if review.get("missing_keywords"):
            confidence -= min(10, len(review.get("missing_keywords", [])))

        return round(min(98, max(45, confidence)), 2)

    def _strengths(self, review: Dict[str, Any], built_resume: Dict[str, Any]) -> List[str]:
        strengths = []

        skills = built_resume.get("core_skills", []) or []
        technical_skills = built_resume.get("technical_skills", []) or []

        for skill in skills[:4]:
            strengths.append(f"Strong visible evidence of {skill}.")

        for skill in technical_skills[:2]:
            strengths.append(f"Practical tool exposure in {skill}.")

        if review.get("education_score", 0) >= 85:
            strengths.append("Academic background aligns well with the target role.")

        if review.get("experience_score", 0) >= 70:
            strengths.append("Relevant internship, attachment, or practical experience is clearly visible.")

        if review.get("job_match_score", 0) >= 80:
            strengths.append("Strong match between CV evidence and job requirements.")

        return strengths[:7] or ["Candidate has potential but requires stronger positioning."]

    def _risks(self, review: Dict[str, Any]) -> List[Dict[str, str]]:
        risks = []
        missing = review.get("missing_keywords", []) or []

        for keyword in missing[:5]:
            risks.append(
                {
                    "risk": f"{str(keyword).title()} is not clearly demonstrated in the CV.",
                    "level": "Medium",
                    "mitigation": f"Only add {keyword} if the candidate has truthful coursework, training, project work, or practical exposure.",
                }
            )

        if review.get("experience_score", 0) < 65:
            risks.append(
                {
                    "risk": "Practical experience may appear limited for the role.",
                    "level": "Medium",
                    "mitigation": "Clarify internship, attachment, project and practical responsibilities.",
                }
            )

        if review.get("achievement_score", 0) < 60:
            risks.append(
                {
                    "risk": "Few measurable achievements are visible.",
                    "level": "Low",
                    "mitigation": "Add truthful numbers, volumes, reports produced, records processed or performance metrics where available.",
                }
            )

        return risks[:6]

    def _interview_readiness(self, review: Dict[str, Any], score: float) -> Dict[str, Any]:
        if score >= 85:
            level = "High"
        elif score >= 70:
            level = "Moderate"
        else:
            level = "Needs Preparation"

        return {
            "level": level,
            "score": round(score, 2),
            "likely_questions": review.get("interview_questions", [])[:6],
            "preparation_focus": self._prep_focus(review),
        }

    def _prep_focus(self, review: Dict[str, Any]) -> List[str]:
        focus = []

        for keyword in (review.get("missing_keywords", []) or [])[:4]:
            focus.append(f"Prepare a truthful answer about any exposure to {keyword}.")

        job_title = (review.get("job_title") or "the role").lower()

        if "finance" in job_title:
            focus.append("Prepare to explain reconciliations, financial records, invoices and Excel use.")

        if "program" in job_title or "programme" in job_title:
            focus.append("Prepare examples of data collection, stakeholder communication and programme support.")

        if "data" in job_title:
            focus.append("Prepare to discuss projects, tools, datasets and measurable outcomes.")

        return focus[:6]

    def _learning_roadmap(self, review: Dict[str, Any]) -> List[Dict[str, str]]:
        roadmap = []

        missing = review.get("missing_keywords", []) or []

        for index, keyword in enumerate(missing[:4], start=1):
            roadmap.append(
                {
                    "week": f"Week {index}",
                    "focus": str(keyword).title(),
                    "action": f"Build truthful exposure through a short course, reading task, or mini-project related to {keyword}.",
                }
            )

        if not roadmap:
            roadmap = [
                {
                    "week": "Week 1",
                    "focus": "Interview Preparation",
                    "action": "Prepare STAR examples from internship, projects and academic experience.",
                },
                {
                    "week": "Week 2",
                    "focus": "Role-Specific Tools",
                    "action": "Revise the main tools or processes mentioned in the job advert.",
                },
            ]

        return roadmap

    def _salary_intelligence(self, review: Dict[str, Any], score: float) -> Dict[str, Any]:
        title = (review.get("job_title") or "").lower()
        industry = (review.get("industry") or "").lower()

        if "graduate" in title or "intern" in title or "trainee" in title:
            low, high = 250, 700
            market_label = "Graduate / entry-level"
        elif "data" in title or "analyst" in title:
            low, high = 600, 1500
            market_label = "Data / analytics"
        elif "finance" in title or "accounting" in industry:
            low, high = 500, 1200
            market_label = "Finance / accounting"
        else:
            low, high = 400, 1000
            market_label = "General professional"

        if score >= 88:
            recommended = int(high * 0.85)
        elif score >= 75:
            recommended = int((low + high) / 2)
        else:
            recommended = int(low * 1.1)

        return {
            "currency": "USD",
            "market_category": market_label,
            "estimated_range": f"${low} - ${high}",
            "recommended_asking_salary": f"${recommended}",
            "recommended_positioning": f"A reasonable positioning range is around ${recommended}, depending on organisation budget and benefits.",
            "confidence": "Indicative only",
        }

    def _summary(self, review: Dict[str, Any], score: float) -> str:
        recommendation = self._recommendation(score)
        job_title = review.get("job_title") or "the target role"

        return (
            f"{recommendation} for {job_title}. The candidate shows useful alignment through education, "
            f"visible experience and relevant skills, but final suitability should be confirmed through interview evidence, "
            f"reference checks and practical examples."
        )


candidate_intelligence = CandidateIntelligence()