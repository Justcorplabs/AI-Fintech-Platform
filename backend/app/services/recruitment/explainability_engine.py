from typing import Dict, Any, List


class ExplainabilityEngine:

    def generate(
        self,
        review: Dict[str, Any],
        candidate_intelligence: Dict[str, Any],
    ) -> Dict[str, Any]:

        positives = []
        negatives = []
        breakdown = []

        ats = review.get("ats_score", 0)
        recruiter = candidate_intelligence.get("recruiter_score", 0)

        if review.get("education_score", 0) >= 80:
            positives.append(
                "Strong educational background matches the role requirements."
            )
            breakdown.append(
                {
                    "factor": "Education",
                    "impact": "+10",
                    "reason": "Relevant degree detected."
                }
            )

        if review.get("experience_score", 0) >= 70:
            positives.append(
                "Relevant practical experience supports the application."
            )
            breakdown.append(
                {
                    "factor": "Experience",
                    "impact": "+12",
                    "reason": "Internship / attachment aligns with role."
                }
            )

        if review.get("found_keywords"):
            breakdown.append(
                {
                    "factor": "Keyword Match",
                    "impact": f"+{len(review['found_keywords'])}",
                    "reason": f"{len(review['found_keywords'])} important requirements matched."
                }
            )

        for keyword in review.get("missing_keywords", [])[:6]:
            negatives.append(
                f"No clear evidence of {keyword}."
            )

            breakdown.append(
                {
                    "factor": keyword.title(),
                    "impact": "-2",
                    "reason": f"The CV does not clearly demonstrate {keyword}."
                }
            )

        summary = self._summary(
            ats,
            recruiter,
            positives,
            negatives,
        )

        return {
            "ats_score": ats,
            "recruiter_score": recruiter,
            "positives": positives,
            "negatives": negatives,
            "score_breakdown": breakdown,
            "summary": summary,
        }

    def _summary(
        self,
        ats: float,
        recruiter: float,
        positives: List[str],
        negatives: List[str],
    ) -> str:

        if recruiter >= 90:
            decision = "Excellent candidate."

        elif recruiter >= 80:
            decision = "Strong candidate."

        elif recruiter >= 70:
            decision = "Good candidate with several improvement opportunities."

        elif recruiter >= 60:
            decision = "Moderate candidate requiring additional evidence."

        else:
            decision = "Substantial improvements are required."

        return (
            f"{decision} "
            f"The ATS score is {ats:.2f}% while the recruiter assessment is "
            f"{recruiter:.2f}%. "
            f"The strongest factors are education, experience and matched evidence, "
            f"while the largest deductions come from missing job-specific evidence."
        )


explainability_engine = ExplainabilityEngine()