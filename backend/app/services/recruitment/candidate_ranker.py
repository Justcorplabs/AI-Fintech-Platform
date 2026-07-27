from typing import Dict, Any, List

from app.services.recruitment.job_intelligence import job_intelligence
from app.services.recruitment.resume_reviewer import resume_reviewer
from app.services.recruitment.resume_builder import resume_builder
from app.services.recruitment.candidate_intelligence import candidate_intelligence


class CandidateRanker:
    def rank_candidates(
        self,
        job_description: str,
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        job_profile = job_intelligence.analyse(job_description or "")
        ranked = []

        for index, candidate in enumerate(candidates, start=1):
            filename = candidate.get("filename") or f"Candidate {index}"
            raw_text = candidate.get("raw_text") or ""

            if not raw_text.strip():
                continue

            review = resume_reviewer.review_resume(
                raw_text=raw_text,
                target_keywords=None,
                job_description=job_description,
            )

            built_resume = resume_builder.build(raw_text, review)

            intelligence = candidate_intelligence.generate(
                review=review,
                built_resume=built_resume,
            )

            ranked.append(
                {
                    "candidate_name": built_resume.get("header", {}).get("name") or filename,
                    "filename": filename,
                    "ats_score": review.get("ats_score", 0),
                    "job_match_score": review.get("job_match_score", 0),
                    "recruiter_score": intelligence.get("recruiter_score", 0),
                    "overall_rating": intelligence.get("overall_rating"),
                    "decision": self._decision(intelligence.get("recruiter_score", 0)),
                    "hiring_recommendation": intelligence.get("hiring_recommendation"),
                    "confidence": intelligence.get("confidence"),
                    "strengths": intelligence.get("candidate_strengths", [])[:5],
                    "risks": intelligence.get("hiring_risks", [])[:5],
                    "missing_requirements": review.get("missing_keywords", [])[:10],
                    "found_requirements": review.get("found_keywords", [])[:10],
                    "interview_questions": review.get("interview_questions", [])[:5],
                    "recruiter_summary": intelligence.get("recruiter_summary"),
                    "review": review,
                    "built_resume": built_resume,
                    "candidate_intelligence": intelligence,
                }
            )

        ranked.sort(key=lambda item: item.get("recruiter_score", 0), reverse=True)

        for position, item in enumerate(ranked, start=1):
            item["rank"] = position

        return {
            "job_profile": job_profile,
            "total_candidates": len(ranked),
            "recommended_for_interview": len(
                [c for c in ranked if c.get("decision") == "Interview"]
            ),
            "reserve_candidates": len(
                [c for c in ranked if c.get("decision") == "Reserve"]
            ),
            "not_recommended": len(
                [c for c in ranked if c.get("decision") == "Not Recommended"]
            ),
            "ranking": ranked,
            "shortlist": self._shortlist(ranked),
            "summary": self._campaign_summary(job_profile, ranked),
        }

    def compare_candidates(
        self,
        candidate_a: Dict[str, Any],
        candidate_b: Dict[str, Any],
    ) -> Dict[str, Any]:
        a_score = float(candidate_a.get("recruiter_score") or 0)
        b_score = float(candidate_b.get("recruiter_score") or 0)

        comparison = {
            "candidate_a": candidate_a.get("candidate_name"),
            "candidate_b": candidate_b.get("candidate_name"),
            "overall_winner": self._winner(candidate_a, candidate_b, "recruiter_score"),
            "categories": {
                "ats_score": self._winner(candidate_a, candidate_b, "ats_score"),
                "job_match_score": self._winner(candidate_a, candidate_b, "job_match_score"),
                "recruiter_score": self._winner(candidate_a, candidate_b, "recruiter_score"),
                "confidence": self._winner(candidate_a, candidate_b, "confidence"),
            },
            "score_gap": round(abs(a_score - b_score), 2),
            "recommendation": self._comparison_recommendation(candidate_a, candidate_b),
        }

        return comparison

    def _decision(self, recruiter_score: float) -> str:
        score = float(recruiter_score or 0)

        if score >= 78:
            return "Interview"

        if score >= 68:
            return "Reserve"

        if score >= 58:
            return "Consider"

        return "Not Recommended"

    def _shortlist(self, ranked: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        shortlist = []

        for candidate in ranked:
            if candidate.get("decision") in ["Interview", "Reserve"]:
                shortlist.append(
                    {
                        "rank": candidate.get("rank"),
                        "candidate_name": candidate.get("candidate_name"),
                        "recruiter_score": candidate.get("recruiter_score"),
                        "decision": candidate.get("decision"),
                        "reason": candidate.get("recruiter_summary"),
                    }
                )

        return shortlist[:10]

    def _campaign_summary(
        self,
        job_profile: Dict[str, Any],
        ranked: List[Dict[str, Any]],
    ) -> str:
        title = job_profile.get("job_title") or "the role"
        organisation = job_profile.get("organisation") or "the organisation"

        if not ranked:
            return f"No candidates were ranked for {title} at {organisation}."

        top = ranked[0]
        interview_count = len([c for c in ranked if c.get("decision") == "Interview"])

        return (
            f"{len(ranked)} candidate(s) were assessed for {title} at {organisation}. "
            f"{interview_count} candidate(s) are recommended for interview. "
            f"The leading candidate is {top.get('candidate_name')} with a recruiter score of "
            f"{top.get('recruiter_score')}%."
        )

    def _winner(
        self,
        candidate_a: Dict[str, Any],
        candidate_b: Dict[str, Any],
        field: str,
    ) -> str:
        a = float(candidate_a.get(field) or 0)
        b = float(candidate_b.get(field) or 0)

        if a > b:
            return candidate_a.get("candidate_name") or "Candidate A"

        if b > a:
            return candidate_b.get("candidate_name") or "Candidate B"

        return "Tie"

    def _comparison_recommendation(
        self,
        candidate_a: Dict[str, Any],
        candidate_b: Dict[str, Any],
    ) -> str:
        winner = self._winner(candidate_a, candidate_b, "recruiter_score")

        if winner == "Tie":
            return "Both candidates are closely matched. Use interviews to assess practical fit, communication, and role-specific exposure."

        return (
            f"{winner} is the stronger candidate based on recruiter score, evidence quality, "
            f"job alignment and overall readiness. Final decision should still consider interview performance."
        )


candidate_ranker = CandidateRanker()