from typing import Dict, Any, List


class CVCoach:
    def generate(
        self,
        resume_text: str,
        review: Dict[str, Any],
        job_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        current_score = float(review.get("ats_score", 0))
        missing = review.get("missing_keywords", []) or []
        found = review.get("found_keywords", []) or []

        estimated_gain = self._estimate_gain(current_score, missing)
        estimated_new_score = min(96, round(current_score + estimated_gain, 2))

        return {
            "current_score": current_score,
            "estimated_new_score": estimated_new_score,
            "estimated_gain": round(estimated_new_score - current_score, 2),
            "summary_rewrite": self._summary_rewrite(found, missing, job_profile),
            "skills_to_add": self._skills_to_add(missing),
            "experience_rewrite": self._experience_rewrite(missing, job_profile),
            "projects_to_add": self._projects_to_add(job_profile),
            "priority_missing_requirements": self._priority_missing(missing),
            "ats_gain_breakdown": {
                "summary": 5,
                "skills": 8 if missing else 3,
                "experience": 6,
                "projects": 3,
            },
            "recruiter_view": self._recruiter_view(current_score, estimated_new_score),
        }

    def _estimate_gain(self, current_score: float, missing: List[str]) -> float:
        if current_score >= 85:
            return 5
        if current_score >= 70:
            return 12
        if current_score >= 55:
            return 18
        return 24

    def _summary_rewrite(
        self,
        found: List[str],
        missing: List[str],
        job_profile: Dict[str, Any],
    ) -> str:
        job_title = job_profile.get("job_title", "the advertised role")
        industry = job_profile.get("industry", "the target field")

        key_skills = found[:5] + missing[:4]
        skills_text = ", ".join(dict.fromkeys(key_skills))

        if not skills_text:
            skills_text = "data handling, reporting, communication, accuracy, and operational support"

        return (
            f"Motivated and analytically minded candidate targeting {job_title} within {industry}. "
            f"Brings practical exposure to {skills_text}, with the ability to support accurate records, "
            f"prepare reports, analyse information, communicate with stakeholders, and contribute to "
            f"evidence-based operational decision-making."
        )

    def _skills_to_add(self, missing: List[str]) -> List[str]:
        priority = []

        for skill in missing:
            if skill not in priority:
                priority.append(skill)

        return priority[:12]

    def _experience_rewrite(
        self,
        missing: List[str],
        job_profile: Dict[str, Any],
    ) -> List[str]:
        job_title = job_profile.get("job_title", "the target role")
        industry = job_profile.get("industry", "the target industry")

        bullets = [
            f"Supported accurate data capture, verification, and record management relevant to {industry}.",
            "Prepared and maintained structured records using Microsoft Excel to support reporting and decision-making.",
            "Assisted with documentation, analysis, and follow-up tasks requiring accuracy and attention to detail.",
            "Communicated professionally with stakeholders and supported timely resolution of operational queries.",
        ]

        if any(k in missing for k in ["claims processing", "claims reporting", "medical aid claims"]):
            bullets.append(
                "Add exposure to claims processing, claims reporting, or medical aid finance where applicable."
            )

        if any(k in missing for k in ["quickbooks", "sage", "pastel"]):
            bullets.append(
                "Mention any accounting software exposure, or add QuickBooks/Sage/Pastel training if completed."
            )

        if any(k in missing for k in ["monitoring", "evaluation", "mel", "data collection"]):
            bullets.append(
                "Highlight MEAL-related tasks such as data collection, database updates, surveys, documentation, and reporting."
            )

        return bullets[:7]

    def _projects_to_add(self, job_profile: Dict[str, Any]) -> List[str]:
        industry = job_profile.get("industry", "").lower()

        if "finance" in industry or "accounting" in industry:
            return [
                "Excel Financial Reporting Dashboard",
                "Bank Reconciliation Practice Project",
                "Claims Processing and Reporting Tracker",
                "Budget Data Collection Template",
            ]

        if "monitoring" in industry or "ngo" in industry:
            return [
                "MEAL Data Collection Tracker",
                "Beneficiary Survey Analysis Project",
                "Programme Performance Dashboard",
                "Data Quality Assessment Checklist",
            ]

        if "technology" in industry or "data" in industry:
            return [
                "Data Cleaning and Analysis Project",
                "SQL Reporting Dashboard",
                "Python Exploratory Data Analysis Notebook",
                "Power BI Business Intelligence Dashboard",
            ]

        return [
            "Role-Specific Reporting Template",
            "Operational Data Tracker",
            "Stakeholder Communication Log",
        ]

    def _priority_missing(self, missing: List[str]) -> Dict[str, List[str]]:
        critical_terms = [
            "quickbooks",
            "claims processing",
            "claims reporting",
            "medical aid claims",
            "bank reconciliation",
            "financial statements",
            "monitoring",
            "evaluation",
            "data collection",
            "data quality",
            "sql",
            "powerbi",
            "excel",
        ]

        critical = [m for m in missing if m in critical_terms]
        important = [m for m in missing if m not in critical_terms]

        return {
            "critical": critical[:8],
            "important": important[:8],
        }

    def _recruiter_view(self, current_score: float, estimated_new_score: float) -> Dict[str, Any]:
        if estimated_new_score >= 85:
            recommendation = "Strong interview potential after CV improvements"
        elif estimated_new_score >= 70:
            recommendation = "Potential interview candidate with targeted improvements"
        else:
            recommendation = "Needs significant tailoring before submission"

        return {
            "current_rating": self._stars(current_score),
            "improved_rating": self._stars(estimated_new_score),
            "recommendation": recommendation,
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


cv_coach = CVCoach()