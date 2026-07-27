import re
from typing import List, Dict, Any


class ATSScorer:
    def contact_score(self, text: str) -> int:
        score = 0

        if re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text):
            score += 50

        if re.search(r"(\+?\d[\d\s\-\(\)]{8,}\d)", text):
            score += 30

        if len([line for line in text.splitlines()[:8] if line.strip()]) >= 2:
            score += 20

        return min(score, 100)

    def skills_score(self, found: List[str], target: List[str]) -> float:
        if not target:
            return 50
        return round((len(found) / len(target)) * 100, 2)

    def education_score(self, text: str) -> int:
        lower = text.lower()

        if any(w in lower for w in ["phd", "doctorate"]):
            return 100
        if any(w in lower for w in ["master", "msc", "mba"]):
            return 95
        if any(w in lower for w in ["degree", "bachelor", "bsc", "honours", "hons"]):
            return 85
        if any(w in lower for w in ["diploma", "hnd"]):
            return 70
        if any(w in lower for w in ["a level", "advanced level"]):
            return 60

        return 40

    def experience_score(self, text: str) -> int:
        lower = text.lower()

        if re.search(r"\b\d+\+?\s*years?\s*(of\s*)?(work\s*)?experience\b", lower):
            return 90

        if re.search(r"20\d{2}\s*(?:-|–|—|to)\s*(20\d{2}|present|current)", lower):
            return 75

        if any(w in lower for w in ["internship", "attachment", "employment", "work experience"]):
            return 65

        return 40

    def formatting_score(self, text: str) -> int:
        score = 60
        lines = [line.strip().lower() for line in text.splitlines() if line.strip()]

        sections = [
            "education", "experience", "employment", "skills", "projects",
            "references", "profile", "summary", "certifications",
            "qualifications", "achievements",
        ]

        found_sections = sum(1 for section in sections if any(section in line for line in lines))
        score += min(found_sections * 5, 30)

        if len(text) > 800:
            score += 10

        return min(score, 100)

    def achievement_score(self, text: str) -> int:
        score = 40
        lower = text.lower()

        if re.search(
            r"\d+%|\$\d+|\d+\s*(records|customers|reports|projects|transactions|datasets|beneficiaries|participants|clients|invoices|accounts)",
            lower,
        ):
            score += 35

        action_words = [
            "developed", "managed", "analysed", "analyzed", "created",
            "improved", "implemented", "automated", "designed", "performed",
            "coordinated", "monitored", "evaluated", "reported", "supported",
            "prepared", "processed", "maintained", "reconciled", "verified",
            "captured", "supervised", "assisted", "administered",
        ]

        if any(word in lower for word in action_words):
            score += 25

        return min(score, 100)

    def job_match_score(
        self,
        found_keywords: List[str],
        active_keywords: List[str],
    ) -> float:
        return self.skills_score(found_keywords, active_keywords)

    def final_score(self, scores: Dict[str, Any]) -> float:
        return round(
            0.12 * scores["contact_score"]
            + 0.18 * scores["skills_score"]
            + 0.12 * scores["education_score"]
            + 0.18 * scores["experience_score"]
            + 0.12 * scores["formatting_score"]
            + 0.13 * scores["achievement_score"]
            + 0.15 * scores["job_match_score"],
            2,
        )


ats_scorer = ATSScorer()