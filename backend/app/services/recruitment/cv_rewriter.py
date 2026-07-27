from typing import Dict, Any, List


class CVRewriter:
    def rewrite(
        self,
        review: Dict[str, Any],
    ) -> Dict[str, Any]:
        coach = review.get("cv_coach", {}) or {}

        summary = coach.get("summary_rewrite") or review.get("professional_summary", "")

        skills = self._build_skills(review)
        experience_bullets = coach.get("experience_rewrite", []) or []
        projects = coach.get("projects_to_add", []) or []

        return {
            "optimized_summary": summary,
            "optimized_skills": skills,
            "optimized_experience_bullets": experience_bullets,
            "recommended_projects": projects,
            "cover_letter": review.get("cover_letter", ""),
            "estimated_ats_score": coach.get("estimated_new_score", review.get("ats_score")),
            "change_log": self._change_log(review),
        }

    def _build_skills(self, review: Dict[str, Any]) -> List[str]:
        found = review.get("found_keywords", []) or []
        missing = review.get("missing_keywords", []) or []

        priority_missing = []
        for item in missing:
            if item not in priority_missing:
                priority_missing.append(item)

        skills = []

        for item in found + priority_missing:
            label = self._pretty(item)
            if label not in skills:
                skills.append(label)

        return skills[:18]

    def _change_log(self, review: Dict[str, Any]) -> List[str]:
        coach = review.get("cv_coach", {}) or {}

        return [
            "Rewrote the professional summary to match the target job title and industry.",
            "Prioritised job-relevant skills based on the structured job profile.",
            "Added stronger action-oriented experience bullet suggestions.",
            "Added project suggestions aligned with missing job requirements.",
            f"Estimated ATS improvement from {coach.get('current_score', review.get('ats_score'))}% to {coach.get('estimated_new_score', review.get('ats_score'))}%.",
        ]

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
        }

        value = str(text).strip()

        if value.lower() in acronyms:
            return acronyms[value.lower()]

        return value.title()


cv_rewriter = CVRewriter()