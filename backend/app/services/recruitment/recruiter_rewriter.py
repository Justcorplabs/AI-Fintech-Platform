from typing import Dict, Any, List
import re


class RecruiterRewriter:
    METRIC_PATTERN = re.compile(
        r"(\b(?:F1-score|ROC-AUC|AUC|ROI|accuracy|precision|recall)\s*[:=]?\s*\d+(?:\.\d+)?%?\b|"
        r"\b\d+(?:\.\d+)?%|\$[\d,]+(?:\.\d+)?|\b\d+(?:,\d{3})+\b|\b\d+(?:\.\d+)?\b)",
        re.IGNORECASE,
    )

    AI_NOISE_PATTERNS = [
        r"\s+while strengthening\s+[^.]+\.?",
        r"\s+with attention to\s+[^.]+\.?",
        r"\s+while improving\s+[^.]+\.?",
        r"\s+to demonstrate\s+[^.]+\.?",
    ]

    ACTION_REPLACEMENTS = {
        "supported used": "Used",
        "supported prepared": "Prepared",
        "supported recorded": "Recorded",
        "supported organized": "Organised",
        "supported organised": "Organised",
        "supported identified": "Identified",
        "supported maintained": "Maintained",
        "supported assisted": "Assisted",
        "supported documented": "Documented",
        "supported communicated": "Communicated",
        "supported participated": "Participated",
        "supported applied": "Applied",
        "supported developed": "Developed",
        "supported built": "Built",
        "supported approach": "Applied",
        "supported problem solved": "Addressed",
        "supported recommendation": "Recommended",
        "supported tools and methods": "Applied",
        "supported results": "Produced",
    }

    def rewrite_bullets(
        self,
        bullets: List[str],
        review: Dict[str, Any],
        fallback_bullets: List[str] = None,
    ) -> List[str]:
        fallback_bullets = fallback_bullets or []
        output = []

        for bullet in bullets or []:
            rewritten = self.rewrite_bullet(bullet, review)

            if rewritten and rewritten not in output:
                output.append(rewritten)

        if len(output) < 3:
            for bullet in fallback_bullets:
                rewritten = self.rewrite_bullet(bullet, review)
                if rewritten and rewritten not in output:
                    output.append(rewritten)
                if len(output) >= 5:
                    break

        return output[:8]

    def rewrite_bullet(self, bullet: str, review: Dict[str, Any]) -> str:
        original = self._clean(bullet)

        if not original:
            return ""

        metrics = self._extract_metrics(original)

        text = self._remove_ai_noise(original)
        text = self._fix_action_phrases(text)
        text = self._fix_project_labels(text)
        text = self._ensure_action_verb(text, review)
        text = self._role_tailor(text, review)
        text = self._restore_metrics(text, metrics)
        text = self._final_clean(text)

        return text

    def human_summary(
        self,
        resume_summary: str,
        review: Dict[str, Any],
        skills: List[str],
    ) -> str:
        job_title = review.get("job_title") or "target role"
        industry = review.get("industry") or "the target sector"

        top_skills = self._select_best_skills(skills, review, limit=5)

        if "finance" in industry.lower() or "accounting" in industry.lower():
            return (
                f"Motivated finance and accounting candidate targeting {job_title}, "
                f"with practical exposure to financial records, reconciliations, reporting, "
                f"Microsoft Excel and accounting support. Brings strong attention to detail, "
                f"confidentiality and a willingness to learn in structured finance environments."
            )

        if "ngo" in industry.lower() or "monitoring" in industry.lower() or "evaluation" in industry.lower():
            return (
                f"Motivated monitoring, evaluation and data-focused candidate targeting {job_title}, "
                f"with practical exposure to data collection, documentation, reporting and programme support. "
                f"Brings strong analytical ability, attention to detail and a commitment to using accurate information "
                f"to support learning, accountability and evidence-based programme decisions."
            )

        if "data" in industry.lower() or "technology" in industry.lower():
            return (
                f"Analytically minded candidate targeting {job_title}, with practical exposure to data analysis, "
                f"reporting, problem-solving and technology-enabled decision support. Skilled in {', '.join(top_skills[:4])}, "
                f"with the ability to transform raw information into clear insights for operational and strategic use."
            )

        if top_skills:
            return (
                f"Motivated candidate targeting {job_title}, with practical exposure to "
                f"{', '.join(top_skills[:4])}. Brings strong attention to detail, clear communication, "
                f"organisational ability and a willingness to contribute effectively within {industry}."
            )

        return resume_summary or (
            f"Motivated candidate targeting {job_title}, with practical experience, strong attention to detail "
            f"and the ability to support accurate work, reporting and team objectives."
        )

    def _role_tailor(self, text: str, review: Dict[str, Any]) -> str:
        lower = text.lower()
        industry = (review.get("industry") or "").lower()
        job_title = (review.get("job_title") or "").lower()
        responsibilities = " ".join(review.get("responsibilities", []) or []).lower()

        if any(term in responsibilities for term in ["call centre", "call center", "inbound", "outbound", "participant"]):
            if any(term in lower for term in ["stakeholder", "client", "customer", "communication", "front desk", "phone", "call"]):
                return text
            if any(term in lower for term in ["data", "survey", "records", "documentation"]):
                return text.rstrip(".") + " to support participant follow-up, reporting and programme accountability."

        if "finance" in industry or "accounting" in industry or "finance" in job_title:
            if any(term in lower for term in ["invoice", "payment", "receipt", "cashbook", "ledger", "record"]):
                return text
            if "report" in lower:
                return text.rstrip(".") + " for finance and management decision-making."

        if "monitoring" in industry or "evaluation" in industry or "ngo" in industry:
            if any(term in lower for term in ["data", "report", "survey", "stakeholder", "documentation"]):
                return text
            if "analysis" in lower:
                return text.rstrip(".") + " to support programme learning and evidence-based decisions."

        return text

    def _ensure_action_verb(self, text: str, review: Dict[str, Any]) -> str:
        clean = text.strip()
        lower = clean.lower()

        action_verbs = (
            "analysed", "analyzed", "prepared", "maintained", "captured", "verified",
            "assisted", "coordinated", "monitored", "evaluated", "processed", "managed",
            "reported", "documented", "communicated", "developed", "built", "improved",
            "conducted", "created", "updated", "reviewed", "organised", "organized",
            "used", "recorded", "participated", "applied", "produced", "recommended",
            "addressed", "supported",
        )

        if lower.startswith(action_verbs):
            return clean

        if lower.startswith("problem solved:"):
            return "Addressed " + clean.split(":", 1)[1].strip()

        if lower.startswith("approach:"):
            return "Applied " + clean.split(":", 1)[1].strip()

        if lower.startswith("results:"):
            return "Produced " + clean.split(":", 1)[1].strip()

        if lower.startswith("recommendation:"):
            return "Recommended " + clean.split(":", 1)[1].strip()

        if lower.startswith("tools and methods:"):
            return "Applied " + clean.split(":", 1)[1].strip()

        first = clean[0].lower() + clean[1:] if clean else clean
        return "Supported " + first

    def _fix_project_labels(self, text: str) -> str:
        replacements = {
            "Problem solved:": "Addressed",
            "Approach:": "Applied",
            "Results:": "Produced",
            "Recommendation:": "Recommended",
            "Tools and methods:": "Applied",
            "Tools and Methods:": "Applied",
        }

        value = text

        for old, new in replacements.items():
            if value.startswith(old):
                value = value.replace(old, new, 1)

        return value

    def _remove_ai_noise(self, text: str) -> str:
        value = text

        for pattern in self.AI_NOISE_PATTERNS:
            value = re.sub(pattern, ".", value, flags=re.IGNORECASE)

        value = value.replace("attention to attention to detail", "attention to detail")
        value = value.replace("attention to accounting", "accurate accounting records")
        value = value.replace("attention to accounts", "accurate account records")

        return value

    def _fix_action_phrases(self, text: str) -> str:
        value = text.strip()

        lower = value.lower()

        for bad, good in self.ACTION_REPLACEMENTS.items():
            if lower.startswith(bad):
                value = good + value[len(bad):]
                break

        return value

    def _extract_metrics(self, text: str) -> List[str]:
        return list(dict.fromkeys([match.group(0) for match in self.METRIC_PATTERN.finditer(text)]))

    def _restore_metrics(self, text: str, metrics: List[str]) -> str:
        value = text

        for metric in metrics:
            if metric not in value:
                value = value.rstrip(".") + f" ({metric})."

        return value

    def _final_clean(self, text: str) -> str:
        value = str(text or "").strip()

        value = re.sub(r"\s+", " ", value)
        value = value.replace(" .", ".")
        value = value.replace("..", ".")
        value = value.replace(" ,", ",")
        value = value.replace("Supported used", "Used")
        value = value.replace("Supported prepared", "Prepared")
        value = value.replace("Supported recorded", "Recorded")
        value = value.replace("Supported identified", "Identified")
        value = value.replace("Supported applied", "Applied")
        value = value.replace("Supported participated", "Participated")
        value = value.replace("Supported problem solved", "Addressed")
        value = value.replace("Supported approach", "Applied")
        value = value.replace("Supported results", "Produced")
        value = value.replace("Supported recommendation", "Recommended")

        value = value.strip()

        if value and not value.endswith("."):
            value += "."

        return value

    def _select_best_skills(
        self,
        skills: List[str],
        review: Dict[str, Any],
        limit: int = 5,
    ) -> List[str]:
        required = [
            *(review.get("technical_skills_required", []) or []),
            *(review.get("software_tools_required", []) or []),
            *(review.get("soft_skills_required", []) or []),
        ]

        scored = []

        for skill in skills or []:
            score = 1
            lower = skill.lower()

            for req in required:
                if lower == str(req).lower():
                    score += 5
                elif lower in str(req).lower() or str(req).lower() in lower:
                    score += 3

            scored.append((score, skill))

        scored.sort(key=lambda item: item[0], reverse=True)

        output = []
        for _, skill in scored:
            if skill not in output:
                output.append(skill)

        return output[:limit]

    def _clean(self, text: str) -> str:
        value = str(text or "").strip()
        value = re.sub(r"^\s*(?:[-•*●▪▫◦]|\d+[\).])\s*", "", value)
        value = re.sub(r"\s+", " ", value)
        return value.strip(" -–—|•*")


recruiter_rewriter = RecruiterRewriter()