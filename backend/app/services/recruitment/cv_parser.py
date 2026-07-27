"""
Recruitment CV Parsing Service
Rule-based CV parser for the MVP.

Extracts:
- Candidate name
- Email
- Phone
- Skills
- Education
- Experience
"""

from typing import Dict, Any, List, Optional
import re


class CVParser:
    SKILL_KEYWORDS = [
        "python",
        "sql",
        "machine learning",
        "deep learning",
        "nlp",
        "react",
        "fastapi",
        "docker",
        "postgresql",
        "tableau",
        "excel",
        "power bi",
        "powerbi",
        "statistics",
        "data analysis",
        "data analytics",
        "data visualization",
        "dashboard",
        "dashboards",
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "scikit-learn",
        "sklearn",
        "tensorflow",
        "keras",
        "xgboost",
        "lightgbm",
        "catboost",
        "r",
        "spss",
        "stata",
        "power query",
        "dax",
        "git",
        "github",
        "api",
        "etl",
        "mysql",
        "postgres",
        "data cleaning",
        "data capturing",
        "data verification",
        "reporting",
    ]

    def parse(self, raw_text: str) -> Dict[str, Any]:
        text_lower = raw_text.lower()

        return {
            "name": self._extract_name(raw_text),
            "email": self._extract_email(raw_text),
            "phone": self._extract_phone(raw_text),
            "education_level": self._extract_education(text_lower),
            "experience_years": self._extract_experience(text_lower),
            "extracted_skills": self._extract_skills(text_lower),
        }

    def _extract_name(self, text: str) -> Optional[str]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for line in lines[:10]:
            if "@" in line:
                continue

            if re.search(r"\d", line):
                continue

            lowered = line.lower()
            bad_words = [
                "curriculum",
                "resume",
                "cv",
                "email",
                "phone",
                "address",
                "profile",
                "summary",
            ]

            if any(word in lowered for word in bad_words):
                continue

            if len(line.split()) >= 2 and len(line) <= 60:
                return line.title()

        return None

    def _extract_email(self, text: str) -> Optional[str]:
        match = re.search(
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
            text,
        )
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        match = re.search(
            r"(\+?\d[\d\s\-\(\)]{8,}\d)",
            text,
        )
        return match.group(0).strip() if match else None

    def _extract_skills(self, text: str) -> List[str]:
        found = []

        for skill in self.SKILL_KEYWORDS:
            pattern = r"\b" + re.escape(skill) + r"\b"

            if re.search(pattern, text):
                normalized = skill

                if normalized in ["power bi"]:
                    normalized = "powerbi"

                if normalized == "sklearn":
                    normalized = "scikit-learn"

                if normalized == "dashboards":
                    normalized = "dashboard"

                if normalized not in found:
                    found.append(normalized)

        return sorted(found)

    def _extract_education(self, text: str) -> str:
        if any(word in text for word in ["phd", "doctorate", "doctoral"]):
            return "PhD"

        if any(word in text for word in ["master", "msc", "m.sc", "mba", "mcom"]):
            return "Masters"

        if any(
            word in text
            for word in [
                "bachelor",
                "bsc",
                "b.sc",
                "degree",
                "honours",
                "honors",
                "hons",
                "beng",
                "bcom",
            ]
        ):
            return "Bachelors"

        if any(word in text for word in ["diploma", "higher national diploma", "hnd"]):
            return "Diploma"

        if any(word in text for word in ["a level", "advanced level"]):
            return "A Level"

        return "Unknown"

    def _extract_experience(self, text: str) -> Optional[float]:
        current_year = 2026

        explicit_patterns = [
            r"(\d+(?:\.\d+)?)\+?\s*years?\s*(?:of\s*)?(?:work\s*)?experience",
            r"experience[:\s]+(\d+(?:\.\d+)?)\+?\s*years?",
            r"(\d+(?:\.\d+)?)\+?\s*years?\s*in\s*(?:data|finance|statistics|analytics|analysis|it|technology)",
            r"over\s*(\d+(?:\.\d+)?)\s*years?\s*(?:of\s*)?(?:work\s*)?experience",
            r"more than\s*(\d+(?:\.\d+)?)\s*years?\s*(?:of\s*)?(?:work\s*)?experience",
            r"at least\s*(\d+(?:\.\d+)?)\s*years?\s*(?:of\s*)?(?:work\s*)?experience",
        ]

        for pattern in explicit_patterns:
            match = re.search(pattern, text)
            if match:
                value = float(match.group(1))
                return round(min(value, 40), 1)

        total_years = 0.0

        employment_keywords = [
            "work experience",
            "employment history",
            "professional experience",
            "industrial attachment",
            "internship",
            "attachment",
            "finance department",
            "revenue hall",
            "employment consultant",
            "security guard",
            "data clerk",
            "analyst",
            "intern",
        ]

        lines = [line.strip().lower() for line in text.splitlines() if line.strip()]

        for line in lines:
            if not any(keyword in line for keyword in employment_keywords):
                continue

            ranges = re.findall(
                r"(19\d{2}|20\d{2})\s*(?:-|–|—|to)\s*(19\d{2}|20\d{2}|present|current)",
                line,
                flags=re.IGNORECASE,
            )

            for start, end in ranges:
                start_year = int(start)

                if end.lower() in ["present", "current"]:
                    end_year = current_year
                else:
                    end_year = int(end)

                if end_year >= start_year:
                    total_years += end_year - start_year

        if total_years > 0:
            return round(min(total_years, 40), 1)

        broader_ranges = re.findall(
            r"(?:work experience|employment history|professional experience|industrial attachment|internship|attachment)[\s\S]{0,250}?"
            r"(19\d{2}|20\d{2})\s*(?:-|–|—|to)\s*(19\d{2}|20\d{2}|present|current)",
            text,
            flags=re.IGNORECASE,
        )

        for start, end in broader_ranges:
            start_year = int(start)

            if end.lower() in ["present", "current"]:
                end_year = current_year
            else:
                end_year = int(end)

            if end_year >= start_year:
                total_years += end_year - start_year

        if total_years > 0:
            return round(min(total_years, 40), 1)

        return None


cv_parser = CVParser()