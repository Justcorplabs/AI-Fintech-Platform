from typing import Dict, Any, List
import re


class AchievementExtractor:
    METRIC_PATTERN = re.compile(
        r"(\b(?:F1-score|ROC-AUC|AUC|ROI|accuracy|precision|recall)\s*[:=]?\s*\d+(?:\.\d+)?%?\b|"
        r"\b\d+(?:\.\d+)?%|\$[\d,]+(?:\.\d+)?|\b\d+(?:,\d{3})+\b|\b\d+(?:\.\d+)?\b)",
        re.IGNORECASE,
    )

    ACTION_WORDS = [
        "achieved", "improved", "increased", "reduced", "developed", "built",
        "created", "implemented", "analysed", "analyzed", "prepared", "maintained",
        "processed", "supported", "coordinated", "managed", "verified", "captured",
        "reported", "presented", "monitored", "evaluated", "conducted", "generated",
    ]

    CATEGORY_KEYWORDS = {
        "financial": [
            "finance", "financial", "accounting", "invoice", "payment", "receipt",
            "cashbook", "ledger", "reconciliation", "budget", "audit", "claims",
            "bank", "expenditure", "revenue", "transactions",
        ],
        "data": [
            "data", "analysis", "analytics", "dashboard", "reporting", "database",
            "python", "sql", "excel", "power bi", "statistics", "model", "roc",
            "auc", "f1-score", "machine learning", "shap", "lime",
        ],
        "monitoring_evaluation": [
            "monitoring", "evaluation", "meal", "m&e", "programme", "program",
            "beneficiary", "survey", "field", "accountability", "learning",
            "data quality", "stakeholder",
        ],
        "operations": [
            "records", "documentation", "filing", "administration", "front desk",
            "call", "participant", "queries", "support", "coordination",
        ],
        "technical": [
            "python", "sql", "power bi", "excel", "sap", "pastel", "quickbooks",
            "model", "algorithm", "machine learning", "automation", "system",
        ],
    }

    def extract(
        self,
        resume_profile: Dict[str, Any],
        review: Dict[str, Any],
    ) -> List[str]:
        candidates = []

        for exp in resume_profile.get("experience", []) or []:
            for bullet in exp.get("bullets", []) or []:
                candidates.append(self._score_candidate(bullet, review))

        for project in resume_profile.get("projects", []) or []:
            name = project.get("name") if isinstance(project, dict) else str(project)
            desc = project.get("description", "") if isinstance(project, dict) else ""
            text = f"{name}: {desc}" if desc else name
            candidates.append(self._score_candidate(text, review))

        candidates = [c for c in candidates if c["score"] >= 3]
        candidates.sort(key=lambda x: x["score"], reverse=True)

        output = []
        for item in candidates:
            achievement = self._rewrite_achievement(item["text"], item["category"])
            if achievement and achievement not in output:
                output.append(achievement)
            if len(output) >= 5:
                break

        return output

    def _score_candidate(self, text: str, review: Dict[str, Any]) -> Dict[str, Any]:
        clean = self._clean(text)
        lower = clean.lower()

        score = 0

        if self.METRIC_PATTERN.search(clean):
            score += 5

        if any(word in lower for word in self.ACTION_WORDS):
            score += 2

        category = self._category(clean)

        if category:
            score += 2

        job_terms = [
            *(review.get("found_keywords", []) or []),
            *(review.get("technical_skills_required", []) or []),
            *(review.get("software_tools_required", []) or []),
            *(review.get("soft_skills_required", []) or []),
        ]

        for term in job_terms:
            if str(term).lower() in lower:
                score += 1

        if len(clean.split()) >= 8:
            score += 1

        return {
            "text": clean,
            "score": score,
            "category": category or "general",
        }

    def _category(self, text: str) -> str:
        lower = text.lower()
        best_category = ""
        best_score = 0

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in lower)
            if score > best_score:
                best_score = score
                best_category = category

        return best_category

    def _rewrite_achievement(
        self,
        text: str,
        category: str,
    ) -> str:
        del category

        clean = self._clean(text)
        metrics = self.METRIC_PATTERN.findall(
            clean
        )

        if not clean:
            return ""

        lower = clean.lower()

        action_verbs = tuple(
            self.ACTION_WORDS
        ) + (
            "applied",
            "contributed",
            "participated",
            "performed",
            "validated",
        )

        if lower.startswith(action_verbs):
            rewritten = clean

        else:
            evidence_patterns = [
                (
                    r"^(?:data cleaning|"
                    r"data validation|"
                    r"data analysis)\b",
                    "Performed ",
                ),
                (
                    r"^(?:dashboard|dashboards|"
                    r"dashboard inputs?)\b",
                    "Prepared ",
                ),
                (
                    r"^(?:report|reports|reporting)\b",
                    "Prepared ",
                ),
                (
                    r"^(?:field verification|"
                    r"verification activities)\b",
                    "Participated in ",
                ),
            ]

            first_lower = (
                clean[0].lower() + clean[1:]
            )

            rewritten = ""

            for pattern, prefix in evidence_patterns:
                if re.match(
                    pattern,
                    lower,
                    flags=re.IGNORECASE,
                ):
                    rewritten = (
                        prefix + first_lower
                    )
                    break

            if not rewritten:
                # Keep the actual candidate evidence.
                # Do not replace it with a generic,
                # category-based achievement.
                rewritten = (
                    clean[0].upper()
                    + clean[1:]
                )

        if metrics:
            for metric in metrics:
                if metric not in rewritten:
                    rewritten = (
                        rewritten.rstrip(".")
                        + f" ({metric})."
                    )

        return self._final_clean(
            rewritten
        )

    def _clean(self, text: str) -> str:
        value = str(text or "").strip()
        value = re.sub(r"^\s*(?:[-•*●▪▫◦]|\d+[\).])\s*", "", value)
        value = re.sub(r"\s+while strengthening\s+[^.]+\.?", ".", value, flags=re.IGNORECASE)
        value = re.sub(r"\s+with attention to\s+[^.]+\.?", ".", value, flags=re.IGNORECASE)
        value = re.sub(r"\s+", " ", value)
        return value.strip(" -–—|•*")

    def _final_clean(self, text: str) -> str:
        value = str(text or "").strip()
        value = value.replace("..", ".")
        value = value.replace(" .", ".")
        value = re.sub(r"\s+", " ", value)
        if value and not value.endswith("."):
            value += "."
        return value


achievement_extractor = AchievementExtractor()
