import re
from typing import Any, Iterable


class ATSScorer:
    """
    Deterministic ATS scoring service.

    Each component returns a value from 0 to 100. The final
    score uses different weights depending on whether a real
    job description or target-keyword set is available.
    """

    SKILL_ALIASES = {
        "powerbi": "power bi",
        "power bi": "power bi",
        "microsoft power bi": "power bi",
        "postgres": "postgresql",
        "postgresql": "postgresql",
        "sklearn": "scikit-learn",
        "scikit learn": "scikit-learn",
        "scikit-learn": "scikit-learn",
        "reactjs": "react",
        "react.js": "react",
        "react": "react",
        "restful api": "api",
        "rest api": "api",
        "apis": "api",
        "ml": "machine learning",
        "machine learning": "machine learning",
        "natural language processing": "nlp",
        "nlp": "nlp",
        "microsoft excel": "excel",
        "excel": "excel",
    }

    EMAIL_PATTERN = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    )

    PHONE_PATTERN = re.compile(
        r"\+?\d[\d\s().\-]{7,}\d"
    )

    LINK_PATTERN = re.compile(
        r"(?:linkedin\.com|github\.com|https?://|www\.)",
        flags=re.IGNORECASE,
    )

    QUANTIFIED_ACHIEVEMENT_PATTERN = re.compile(
        (
            r"(?:\b\d+(?:\.\d+)?\s*%|\$\s*\d+|"
            r"\b\d+(?:,\d{3})+\b|"
            r"\b(?:increased|reduced|improved|processed|analysed|"
            r"analyzed|managed|served|trained|delivered|generated)"
            r"\b[^.\n]{0,80}\b\d+\b)"
        ),
        flags=re.IGNORECASE,
    )

    ACTION_VERBS = {
        "achieved",
        "analysed",
        "analyzed",
        "automated",
        "built",
        "created",
        "delivered",
        "designed",
        "developed",
        "implemented",
        "improved",
        "increased",
        "led",
        "managed",
        "optimised",
        "optimized",
        "reduced",
        "resolved",
        "trained",
        "validated",
    }

    SECTION_GROUPS = {
        "summary": {
            "professional summary",
            "profile",
            "career objective",
            "objective",
        },
        "skills": {
            "skills",
            "technical skills",
            "core competencies",
            "competencies",
        },
        "experience": {
            "work experience",
            "professional experience",
            "employment history",
            "experience",
            "industrial attachment",
            "internship",
        },
        "education": {
            "education",
            "academic background",
            "qualifications",
        },
        "projects": {
            "projects",
            "project experience",
        },
        "certifications": {
            "certifications",
            "certificates",
            "training",
        },
    }

    def _clamp(
        self,
        value: float,
    ) -> float:
        return min(
            100.0,
            max(0.0, float(value)),
        )

    def _normalise_skill(
        self,
        value: Any,
    ) -> str:
        skill = re.sub(
            r"\s+",
            " ",
            str(value or "")
            .strip()
            .lower()
            .replace("_", " "),
        )

        skill = skill.strip(
            " .,:;()[]{}"
        )

        return self.SKILL_ALIASES.get(
            skill,
            skill,
        )

    def _normalised_set(
        self,
        values: Iterable[Any] | None,
    ) -> set[str]:
        output: set[str] = set()

        for value in values or []:
            normalised = self._normalise_skill(
                value
            )

            if normalised:
                output.add(
                    normalised
                )

        return output

    def contact_score(
        self,
        text: str,
    ) -> int:
        score = 0

        if self.EMAIL_PATTERN.search(
            text or ""
        ):
            score += 45

        if self.PHONE_PATTERN.search(
            text or ""
        ):
            score += 35

        if self.LINK_PATTERN.search(
            text or ""
        ):
            score += 20

        return int(
            self._clamp(score)
        )

    def skills_score(
        self,
        found: list[str],
        target: list[str],
    ) -> float:
        target_set = self._normalised_set(
            target
        )

        if not target_set:
            return 0.0

        found_set = self._normalised_set(
            found
        )

        matched = (
            target_set
            & found_set
        )

        return round(
            self._clamp(
                100
                * len(matched)
                / len(target_set)
            ),
            2,
        )

    def education_score(
        self,
        text: str,
        education_level: str | None = None,
    ) -> int:
        level = str(
            education_level or ""
        ).strip().lower()

        level_scores = {
            "phd": 100,
            "doctorate": 100,
            "masters": 90,
            "master": 90,
            "bachelors": 80,
            "bachelor": 80,
            "diploma": 65,
            "a level": 45,
            "unknown": 0,
            "": 0,
        }

        if level in level_scores:
            detected_score = (
                level_scores[level]
            )

            if detected_score:
                return detected_score

        lower = (
            text or ""
        ).lower()

        if re.search(
            r"\b(?:ph\.?d|doctorate|doctoral)\b",
            lower,
        ):
            return 100

        if re.search(
            r"\b(?:master(?:'s)?|m\.?sc|mba|mcom)\b",
            lower,
        ):
            return 90

        if re.search(
            r"\b(?:bachelor(?:'s)?|b\.?sc|beng|bcom|honou?rs|hons)\b",
            lower,
        ):
            return 80

        if re.search(
            r"\b(?:higher national diploma|diploma|hnd)\b",
            lower,
        ):
            return 65

        if re.search(
            r"\b(?:a[\s-]?level|advanced level)\b",
            lower,
        ):
            return 45

        if re.search(
            r"\b(?:education|academic background|qualifications)\b",
            lower,
        ):
            return 20

        return 0

    def experience_score(
        self,
        text: str,
        experience_years: float | None = None,
    ) -> int:
        years = experience_years

        if years is None:
            match = re.search(
                (
                    r"\b(\d+(?:\.\d+)?)\+?\s*years?"
                    r"\s*(?:of\s*)?(?:work\s*)?experience\b"
                ),
                text or "",
                flags=re.IGNORECASE,
            )

            if match:
                years = float(
                    match.group(1)
                )

        if years is not None:
            years = max(
                0.0,
                float(years),
            )

            if years >= 5:
                return 100

            if years >= 3:
                return 85

            if years >= 2:
                return 70

            if years >= 1:
                return 55

            if years > 0:
                return 40

        lower = (
            text or ""
        ).lower()

        if any(
            phrase in lower
            for phrase in (
                "industrial attachment",
                "internship",
                "work experience",
                "professional experience",
                "employment history",
            )
        ):
            return 35

        return 0

    def formatting_score(
        self,
        text: str,
    ) -> int:
        raw_text = (
            text or ""
        ).strip()

        if not raw_text:
            return 0

        lower = raw_text.lower()
        score = 0

        found_groups = 0

        for headings in (
            self.SECTION_GROUPS.values()
        ):
            if any(
                heading in lower
                for heading in headings
            ):
                found_groups += 1

        score += min(
            found_groups * 12,
            60,
        )

        lines = [
            line.strip()
            for line in raw_text.splitlines()
            if line.strip()
        ]

        if 5 <= len(lines) <= 250:
            score += 10

        if 200 <= len(raw_text) <= 20_000:
            score += 10

        bullet_count = sum(
            1
            for line in lines
            if re.match(
                r"^(?:[-•*]|\d+[.)])\s+",
                line,
            )
        )

        if bullet_count >= 2:
            score += 10

        excessively_long_lines = sum(
            1
            for line in lines
            if len(line) > 180
        )

        if lines and (
            excessively_long_lines
            / len(lines)
            <= 0.10
        ):
            score += 10

        return int(
            self._clamp(score)
        )

    def achievement_score(
        self,
        text: str,
    ) -> int:
        raw_text = (
            text or ""
        )

        if not raw_text.strip():
            return 0

        quantified = (
            self.QUANTIFIED_ACHIEVEMENT_PATTERN.findall(
                raw_text
            )
        )

        lower = raw_text.lower()

        verb_count = sum(
            1
            for verb in self.ACTION_VERBS
            if re.search(
                rf"\b{re.escape(verb)}\b",
                lower,
            )
        )

        score = min(
            len(quantified) * 20,
            60,
        )

        score += min(
            verb_count * 5,
            25,
        )

        if any(
            phrase in lower
            for phrase in (
                "resulted in",
                "leading to",
                "which improved",
                "which reduced",
                "on time",
                "ahead of schedule",
                "within budget",
            )
        ):
            score += 15

        return int(
            self._clamp(score)
        )

    def job_match_score(
        self,
        found_keywords: list[str],
        active_keywords: list[str],
    ) -> float:
        return self.skills_score(
            found_keywords,
            active_keywords,
        )

    def final_score(
        self,
        scores: dict[str, Any],
        job_context_available: bool = True,
    ) -> float:
        """
        Produce a calibrated aggregate without counting
        skills and job match twice.
        """

        if job_context_available:
            weights = {
                "contact_score": 0.08,
                "job_match_score": 0.30,
                "education_score": 0.14,
                "experience_score": 0.24,
                "formatting_score": 0.10,
                "achievement_score": 0.14,
            }

        else:
            weights = {
                "contact_score": 0.10,
                "skills_score": 0.25,
                "education_score": 0.15,
                "experience_score": 0.25,
                "formatting_score": 0.10,
                "achievement_score": 0.15,
            }

        score = sum(
            self._clamp(
                scores.get(component, 0)
            )
            * weight
            for component, weight
            in weights.items()
        )

        return round(
            self._clamp(score),
            2,
        )


ats_scorer = ATSScorer()