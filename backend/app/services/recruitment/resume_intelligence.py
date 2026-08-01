from typing import Dict, Any, List, Optional
import re

from app.services.recruitment.experience_parser import experience_parser


class ResumeIntelligence:
    SECTION_ALIASES = {
        "summary": [
            "profile",
            "professional profile",
            "professional summary",
            "career objective",
            "objective",
            "summary",
            "about me",
        ],
        "skills": [
            "skills",
            "technical skills",
            "core skills",
            "competencies",
            "key skills",
            "professional skills",
            "areas of expertise",
            "strengths",
            "key strengths",
            "selected strengths",
            "selected strengths for artificial intelligence engineering",
        ],
        "experience": [
            "experience",
            "work experience",
            "professional experience",
            "employment history",
            "work history",
            "career history",
            "industrial attachment",
            "attachment",
            "internship",
        ],
        "education": [
            "education",
            "academic background",
            "qualifications",
            "academic qualifications",
            "education and qualifications",
            "education and training",
            "education & training",
            "academic qualifications and training",
        ],
        "projects": [
            "projects",
            "academic projects",
            "research projects",
            "portfolio",
            "project experience",
        ],
        "certifications": [
            "certifications",
            "certificates",
            "training",
            "professional training",
            "courses",
        ],
        "languages": [
            "languages",
            "language proficiency",
            "additional information",
        ],
        "references": [
            "references",
            "referees",
            "professional references",
            "languages and references",
            "languages & references",
            "languages and referees",
            "referees and languages",
        ],
    }

    BULLET_PREFIX = re.compile(r"^\s*(?:[-•*●▪▫◦]|\d+[\).])\s*")

    DATE_PATTERN = re.compile(
        r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s*)?"
        r"(20\d{2}|19\d{2})\s*(?:-|–|—|to)?\s*"
        r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s*)?"
        r"(20\d{2}|19\d{2}|present|current)?",
        re.IGNORECASE,
    )

    def analyse(self, raw_text: str) -> Dict[str, Any]:
        text = self._normalise_text(raw_text or "")
        lines = self._clean_lines(text)
        sections = self._split_sections(lines)

        return {
            "header": self._extract_header(lines),
            "summary": self._extract_summary(sections, lines),
            "skills": self._extract_skills(sections, text),
            "experience": self._extract_experience(sections),
            "education": self._extract_education(sections),
            "projects": self._extract_projects(sections),
            "certifications": self._extract_certifications(sections),
            "languages": self._extract_languages(sections, text),
            "references": self._extract_references(sections),
            "raw_sections": sections,
        }

    def _normalise_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("", "\n• ")
        text = text.replace("•", "\n• ")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def _clean_lines(self, text: str) -> List[str]:
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _normalise_heading(self, line: str) -> str:
        clean = re.sub(r"[^a-zA-Z&/ ]", "", line).strip().lower()
        clean = re.sub(r"\s+", " ", clean)
        return clean

    def _heading_key(self, line: str) -> Optional[str]:
        clean = self._normalise_heading(line)

        if len(clean) > 50:
            return None

        for key, aliases in self.SECTION_ALIASES.items():
            if clean in aliases:
                return key

        return None

    def _split_sections(self, lines: List[str]) -> Dict[str, List[str]]:
        sections: Dict[str, List[str]] = {"top": []}
        current = "top"

        for line in lines:
            key = self._heading_key(line)

            if key:
                current = key
                sections.setdefault(current, [])
                continue

            sections.setdefault(current, []).append(line)

        return sections

    def _extract_header(self, lines: List[str]) -> Dict[str, str]:
        top = lines[:18]
        joined = "\n".join(top)

        email_match = re.search(
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
            joined,
        )

        phone_match = re.search(r"(\+?\d[\d\s\-\(\)]{8,}\d)", joined)

        name = "Candidate"

        for line in top[:6]:
            lower = line.lower()

            if "@" in line:
                continue

            if phone_match and phone_match.group(0) in line:
                continue

            if any(word in lower for word in ["curriculum", "vitae", "resume", "cv"]):
                continue

            if len(line.split()) <= 5 and any(ch.isalpha() for ch in line):
                name = self._title_case_name(line)
                break

        location = ""

        for line in top:
            lower = line.lower()
            if any(city in lower for city in ["harare", "gweru", "bulawayo", "mutare", "masvingo", "zimbabwe"]):
                clean = line
                if email_match:
                    clean = clean.replace(email_match.group(0), "")
                if phone_match:
                    clean = clean.replace(phone_match.group(0), "")
                clean = clean.replace("|", " ")
                clean = re.sub(r"\s+", " ", clean).strip(" ,-")
                location = clean or line
                break

        return {
            "name": name,
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0).strip() if phone_match else "",
            "location": location or "Zimbabwe",
        }

    def _title_case_name(self, name: str) -> str:
        name = re.sub(r"[^a-zA-Z\s\-']", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        return name.title() if name else "Candidate"

    def _extract_summary(self, sections: Dict[str, List[str]], lines: List[str]) -> str:
        summary_lines = sections.get("summary", [])

        if summary_lines:
            cleaned = [
                self._clean_item(line)
                for line in summary_lines
                if len(self._clean_item(line).split()) >= 4
            ]
            return " ".join(cleaned[:5]).strip()

        top = sections.get("top", [])[:10]
        possible = []

        for line in top:
            lower = line.lower()

            if "@" in line or re.search(r"\+?\d[\d\s\-\(\)]{8,}\d", line):
                continue

            if len(line.split()) >= 8:
                possible.append(line)

        return " ".join(possible[:3]).strip()

    def _extract_skills(self, sections: Dict[str, List[str]], text: str) -> List[str]:
        skills = []
        skill_lines = sections.get("skills", [])

        for line in skill_lines:
            clean_line = self._clean_item(line)

            if not clean_line:
                continue

            parts = re.split(r",|;|\||\t| {2,}", clean_line)

            for part in parts:
                clean = self._clean_item(part)

                if 2 <= len(clean) <= 60:
                    self._add_unique(skills, self._pretty(clean))

        common_skills = [
            "python",
            "sql",
            "excel",
            "power bi",
            "powerbi",
            "statistics",
            "data analysis",
            "data cleaning",
            "reporting",
            "database",
            "monitoring",
            "evaluation",
            "mel",
            "m&e",
            "data collection",
            "accounting",
            "finance",
            "reconciliation",
            "quickbooks",
            "pastel",
            "sap",
            "communication",
            "planning",
            "research",
            "documentation",
            "attention to detail",
            "financial records",
            "budget tracking",
            "invoice processing",
        ]

        lower = text.lower()

        for skill in common_skills:
            if re.search(r"\b" + re.escape(skill) + r"\b", lower):
                self._add_unique(skills, self._pretty(skill))

        return skills[:35]

    def _extract_experience(self, sections: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        lines = sections.get("experience", [])
        return experience_parser.parse(lines)

    def _extract_education(self, sections: Dict[str, List[str]]) -> List[Dict[str, str]]:
        lines = sections.get("education", [])
        education = []

        if not lines:
            return education

        current = None

        for line in lines:
            clean = self._clean_item(line)
            lower = clean.lower()

            if not clean:
                continue

            if any(word in lower for word in ["degree", "bachelor", "bsc", "msc", "master", "diploma", "certificate", "a level", "o level"]):
                if current:
                    education.append(current)

                current = {
                    "qualification": clean,
                    "institution": "",
                    "period": self._extract_period(clean),
                }
                continue

            if current is None:
                current = {
                    "qualification": clean,
                    "institution": "",
                    "period": self._extract_period(clean),
                }
            elif not current.get("institution"):
                current["institution"] = clean

        if current:
            education.append(current)

        return education[:8]

    def _extract_period(self, text: str) -> str:
        match = self.DATE_PATTERN.search(text)
        return match.group(0).strip() if match else ""

    def _extract_projects(self, sections: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        lines = sections.get("projects", [])
        projects = []

        for line in lines:
            clean = self._clean_bullet(line)

            if len(clean) > 4:
                projects.append(
                    {
                        "name": clean,
                        "description": "",
                    }
                )

        return projects[:10]

    def _extract_certifications(self, sections: Dict[str, List[str]]) -> List[str]:
        lines = sections.get("certifications", [])
        certs = []

        for line in lines:
            clean = self._clean_bullet(line)

            if len(clean) > 3:
                self._add_unique(certs, clean)

        return certs[:10]

    def _extract_languages(self, sections: Dict[str, List[str]], text: str) -> List[str]:
        languages = []
        language_lines = sections.get("languages", [])

        for line in language_lines:
            clean_line = self._clean_item(line)

            if "language" in clean_line.lower():
                clean_line = re.sub(r"languages?\s*[:\-]?", "", clean_line, flags=re.IGNORECASE)

            parts = re.split(r",|;|\||/|\t| and | {2,}", clean_line)

            for part in parts:
                clean = self._clean_item(part)

                if clean and clean.lower() not in ["interests", "football", "cricket"]:
                    self._add_unique(languages, self._pretty(clean))

        lower = text.lower()

        for lang in ["english", "shona", "ndebele", "portuguese", "french"]:
            if re.search(r"\b" + lang + r"\b", lower):
                self._add_unique(languages, self._pretty(lang))

        return languages or ["English"]

    def _extract_references(self, sections: Dict[str, List[str]]) -> List[str]:
        lines = sections.get("references", [])
        refs = []

        for line in lines:
            clean = self._clean_item(line)

            if len(clean) > 2:
                refs.append(clean)

        return refs[:8]

    def _clean_item(self, value: str) -> str:
        value = str(value or "").strip()
        value = self.BULLET_PREFIX.sub("", value)
        value = value.replace("", "")
        value = re.sub(r"\s+", " ", value)
        return value.strip(" -–—|•*")

    def _clean_bullet(self, line: str) -> str:
        line = self.BULLET_PREFIX.sub("", str(line or "").strip())
        return self._clean_item(line)

    def _pretty(self, value: str) -> str:
        value = str(value or "").strip()

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
            "sap": "SAP",
            "powerbi": "Power BI",
            "power bi": "Power BI",
        }

        lower = value.lower()

        if lower in acronyms:
            return acronyms[lower]

        return value.title()

    def _add_unique(self, items: List[str], value: str):
        if value and value not in items:
            items.append(value)


resume_intelligence = ResumeIntelligence()
