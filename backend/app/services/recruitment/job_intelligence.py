from typing import Dict, Any, List
import re


class JobIntelligence:
    """
    General job advert parser.

    This parser is designed to work across many job posts and many users.
    It avoids employer-specific hard-coding and extracts structured job data
    from the advert itself.
    """

    SECTION_HEADERS = {
        "responsibilities": [
            "duties and responsibilities",
            "key responsibilities",
            "responsibilities",
            "duties",
            "role responsibilities",
            "job responsibilities",
        ],
        "qualifications": [
            "qualifications and experience",
            "qualifications",
            "requirements",
            "minimum requirements",
            "experience and qualifications",
            "education and experience",
        ],
        "skills": [
            "skills and competencies",
            "competencies",
            "skills",
            "required skills",
            "technical skills",
            "key skills",
        ],
        "offer": [
            "what we offer",
            "benefits",
            "remuneration",
        ],
        "apply": [
            "how to apply",
            "application procedure",
            "application",
            "to apply",
        ],
    }

    TOOL_PATTERNS = [
        r"\bpython\b",
        r"\bsql\b",
        r"\br\b",
        r"\bexcel\b",
        r"\bmicrosoft excel\b",
        r"\badvanced formulas\b",
        r"\bpivot ?tables?\b",
        r"\bpower query\b",
        r"\bpower bi\b",
        r"\btableau\b",
        r"\bspss\b",
        r"\bstata\b",
        r"\bsas\b",
        r"\bquickbooks\b",
        r"\bsap\b",
        r"\bpastel\b",
        r"\bmembership management system\b",
        r"\bcustomer management system\b",
        r"\bcrm\b",
        r"\bdatabase\b",
        r"\bdatabases\b",
        r"\bdashboards?\b",
        r"\bdata modelling\b",
        r"\bdata modeling\b",
    ]

    SOFT_SKILL_PATTERNS = [
        r"attention to detail",
        r"communication",
        r"interpersonal",
        r"integrity",
        r"confidentiality",
        r"analytical",
        r"problem[- ]solving",
        r"team",
        r"collaborative",
        r"independent",
        r"organisational",
        r"organizational",
        r"time management",
        r"proactive",
        r"accuracy",
        r"presentation",
        r"report writing",
        r"fast[- ]paced",
        r"results[- ]driven",
    ]

    DEGREE_PATTERNS = [
        r"data science",
        r"statistics",
        r"mathematics",
        r"computer science",
        r"information systems",
        r"business analytics",
        r"actuarial science",
        r"accounting",
        r"finance",
        r"banking",
        r"insurance",
        r"health economics",
        r"monitoring and evaluation",
        r"development studies",
        r"social sciences",
        r"public health",
        r"project management",
        r"business administration",
        r"risk management",
    ]

    GENERIC_HEADERS = {
        "job description",
        "duties and responsibilities",
        "key responsibilities",
        "responsibilities",
        "duties",
        "qualifications and experience",
        "qualifications",
        "requirements",
        "skills and competencies",
        "skills",
        "what we offer",
        "how to apply",
        "application",
    }

    def analyse(self, job_description: str) -> Dict[str, Any]:
        raw = job_description or ""
        text = self._clean_text(raw)
        lines = self._clean_lines(raw)

        sections = self._extract_sections(lines)

        job_title = self._extract_job_title(lines, text)
        organisation = self._extract_organisation(lines, text)
        deadline = self._extract_deadline(text)
        application_email = self._extract_email(text)
        location = self._extract_location(lines, text)

        responsibilities = self._extract_bullets_from_sections(
            sections,
            ["responsibilities"],
        )

        qualifications = self._extract_bullets_from_sections(
            sections,
            ["qualifications"],
        )

        skill_lines = self._extract_bullets_from_sections(
            sections,
            ["skills", "qualifications", "responsibilities"],
        )

        technical_requirements = self._extract_requirement_terms(
            text=text,
            lines=responsibilities + qualifications + skill_lines,
        )

        software_tools = self._extract_patterns(text, self.TOOL_PATTERNS)
        soft_skills = self._extract_patterns(text, self.SOFT_SKILL_PATTERNS)
        degree_requirements = self._extract_patterns(text, self.DEGREE_PATTERNS)

        experience_requirement = self._extract_experience_requirement(text)
        industry = self._infer_industry(text, job_title)

        return {
            "job_title": job_title,
            "organisation": organisation,
            "industry": industry,
            "location": location,
            "deadline": deadline,
            "application_email": application_email,
            "experience_requirement": experience_requirement,
            "responsibilities": responsibilities,
            "qualifications": qualifications,
            "technical_requirements": technical_requirements,
            "software_tools": software_tools,
            "soft_skills": soft_skills,
            "degree_requirements": degree_requirements,
            "degree_requirement_group": {
                "mode": "any",
                "options": degree_requirements,
            },
            "keywords": self._combined_keywords(
                technical_requirements,
                software_tools,
                soft_skills,
            ),
            "raw_text": raw,
        }

    def _clean_text(self, text: str) -> str:
        value = str(text or "")
        value = value.replace("–", " - ").replace("—", " - ")
        value = value.replace("-", "-")
        value = value.replace("*", "")
        value = value.replace("’", "'")
        value = re.sub(r"[ \t]+", " ", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        value = re.sub(r"\s+-\s+", " - ", value)
        return value.strip()

    def _clean_lines(self, text: str) -> List[str]:
        cleaned = self._clean_text(text)
        lines = []

        for line in cleaned.splitlines():
            value = line.strip()
            value = re.sub(r"^[•\-\*\u2022]+\s*", "", value)
            value = re.sub(r"^\d+[\.\)]\s*", "", value)
            value = re.sub(r"\s+", " ", value).strip()

            if value:
                lines.append(value)

        return lines

    def _extract_job_title(self, lines: List[str], text: str) -> str:
        if not lines:
            return "Target Role"

        # Handles copied markdown-style titles such as:
        # *Data Analyst*– Membership
        # Data Analyst*– Membership
        # DATA ANALYST - MEMBERSHIP
        first_clean = self._title_clean(lines[0])
        second_clean = self._title_clean(lines[1]) if len(lines) > 1 else ""

        if self._looks_like_title(first_clean):
            if self._looks_like_title_continuation(second_clean):
                return self._title_clean(f"{first_clean} {second_clean}")
            return first_clean

        # Look in the first few lines for the most title-like line.
        for index, line in enumerate(lines[:10]):
            clean = self._title_clean(line)
            lower = clean.lower()

            if not clean:
                continue

            if lower in self.GENERIC_HEADERS:
                continue

            if lower.startswith("expires"):
                continue

            if "http" in lower or "www." in lower:
                continue

            if lower.startswith("location:"):
                continue

            if self._looks_like_title(clean):
                next_line = self._title_clean(lines[index + 1]) if index + 1 < len(lines) else ""
                if self._looks_like_title_continuation(next_line):
                    return self._title_clean(f"{clean} {next_line}")
                return clean

        # Pattern fallback: detect "position of X", "role of X", etc.
        patterns = [
            r"(?:position|role|post)\s+(?:of|as)\s+([A-Za-z0-9 /\-&]+)",
            r"seeking\s+(?:a|an)\s+([A-Za-z0-9 /\-&]+?)\s+to\s+join",
            r"recruit\s+(?:a|an)\s+([A-Za-z0-9 /\-&]+?)\s+to\s+join",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                title = self._title_clean(match.group(1))
                if self._looks_like_title(title):
                    return title

        return "Target Role"

    def _title_clean(
        self,
        value: str,
    ) -> str:
        clean = str(value or "")

        clean = clean.replace("*", "")

        clean = (
            clean
            .replace("???", " - ")
            .replace("???", " - ")
        )

        clean = re.sub(
            r"^\s{0,3}#{1,6}\s*",
            "",
            clean,
        )

        clean = re.sub(
            (
                r"^\s*(?:sample\s+)?"
                r"job\s+description\s*"
                r"[:\-]\s*"
            ),
            "",
            clean,
            flags=re.IGNORECASE,
        )

        clean = re.sub(
            (
                r"^\s*(?:job\s+title|"
                r"position|role|post)\s*"
                r"[:\-]\s*"
            ),
            "",
            clean,
            flags=re.IGNORECASE,
        )

        clean = re.sub(
            r"\s+",
            " ",
            clean,
        )

        clean = re.sub(
            r"\s*-\s*",
            " - ",
            clean,
        )

        clean = clean.strip(
            " .,:;|-#"
        )

        return clean.strip()

    def _looks_like_title(self, line: str) -> bool:
        clean = str(line or "").strip()
        lower = clean.lower()

        if not clean:
            return False

        if lower in self.GENERIC_HEADERS:
            return False

        if lower.startswith("expires"):
            return False

        if "http" in lower or "www." in lower or "@" in lower:
            return False

        if lower.startswith("location:"):
            return False

        if len(clean.split()) > 9:
            return False

        title_signals = [
            "analyst",
            "officer",
            "assistant",
            "intern",
            "trainee",
            "manager",
            "administrator",
            "developer",
            "engineer",
            "accountant",
            "technician",
            "clerk",
            "coordinator",
            "consultant",
            "specialist",
            "supervisor",
            "graduate",
            "data",
            "finance",
            "programme",
            "program",
            "membership",
        ]

        return any(signal in lower for signal in title_signals)

    def _looks_like_title_continuation(self, line: str) -> bool:
        if not line:
            return False

        lower = line.lower()

        if lower in self.GENERIC_HEADERS:
            return False

        if lower.startswith("expires"):
            return False

        if "http" in lower or "www." in lower:
            return False

        if len(line.split()) > 4:
            return False

        continuation_signals = [
            "membership",
            "finance",
            "data",
            "operations",
            "claims",
            "sales",
            "ict",
            "monitoring",
            "evaluation",
            "administration",
        ]

        return any(signal in lower for signal in continuation_signals)

    def _extract_organisation(self, lines: List[str], text: str) -> str:
        # Organisation is often immediately after the title.
        for line in lines[1:12]:
            lower = line.lower()

            if lower.startswith("expires"):
                continue

            if "http" in lower or "www." in lower:
                continue

            if lower in self.GENERIC_HEADERS:
                continue

            if lower.startswith("location:"):
                continue

            if self._looks_like_org_line(line):
                return self._clean_org(line)

        patterns = [
            r"([A-Z][A-Za-z0-9&\-\s]+?)\s+(?:seeks|is seeking|invites|is looking|wishes)\s+to",
            r"Join the\s+([A-Z][A-Za-z0-9&\-\s]+?)\s+Team",
            r"([A-Z][A-Za-z0-9&\-\s]+?)\s+is\s+(?:a|an)\s+.+?(?:company|society|organisation|organization|provider|institution)",
            r"at\s+([A-Z][A-Za-z0-9&\-\s]+?)(?:\.|,|\n)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                org = self._clean_org(match.group(1))
                if org and len(org.split()) <= 10:
                    return org

        return "Not detected"

    def _looks_like_org_line(self, line: str) -> bool:
        lower = line.lower()

        org_words = [
            "company",
            "holdings",
            "health",
            "care",
            "medical",
            "society",
            "university",
            "college",
            "ministry",
            "council",
            "agency",
            "authority",
            "organisation",
            "organization",
            "pvt",
            "ltd",
            "limited",
            "bank",
            "finance",
            "financial",
            "foundation",
            "trust",
            "labs",
            "corporation",
            "group",
        ]

        if len(line.split()) > 12:
            return False

        return any(word in lower for word in org_words)

    def _clean_org(
        self,
        org: str,
    ) -> str:
        clean = str(org or "").strip()

        clean = re.sub(
            r"^\s{0,3}#{1,6}\s*",
            "",
            clean,
        )

        clean = re.sub(
            (
                r"^\s*(?:company|"
                r"organisation|organization|"
                r"employer)\s*[:\-]\s*"
            ),
            "",
            clean,
            flags=re.IGNORECASE,
        )

        clean = re.sub(
            r"\s+",
            " ",
            clean,
        )

        clean = clean.strip(
            " .,-"
        )

        return (
            clean.title()
            if clean.isupper()
            else clean
        )

    def _extract_location(self, lines: List[str], text: str) -> str:
        for line in lines:
            match = re.search(r"location:\s*(.+)", line, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        common_locations = [
            "Harare",
            "Bulawayo",
            "Gweru",
            "Mutare",
            "Masvingo",
            "Zimbabwe",
        ]

        found = [
            loc
            for loc in common_locations
            if re.search(rf"\b{loc}\b", text, re.IGNORECASE)
        ]

        return ", ".join(found[:2]) if found else "Not specified"

    def _extract_deadline(self, text: str) -> str:
        patterns = [
            r"expires\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            r"no later than\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
            r"by\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
            r"deadline[:\s]+([A-Za-z0-9,\s]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip(" .")

        return "Not specified"

    def _extract_email(self, text: str) -> str:
        match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        return match.group(0).lower() if match else ""

    def _extract_sections(self, lines: List[str]) -> Dict[str, List[str]]:
        sections = {
            "intro": [],
            "responsibilities": [],
            "qualifications": [],
            "skills": [],
            "offer": [],
            "apply": [],
        }

        current = "intro"

        for line in lines:
            detected = self._detect_section(line)

            if detected:
                current = detected
                continue

            sections.setdefault(current, []).append(line)

        return sections

    def _detect_section(self, line: str) -> str:
        lower = line.lower().strip(": ")

        for section, headers in self.SECTION_HEADERS.items():
            if lower in headers:
                return section

        return ""

    def _extract_bullets_from_sections(
        self,
        sections: Dict[str, List[str]],
        keys: List[str],
    ) -> List[str]:
        output = []

        for key in keys:
            for line in sections.get(key, []):
                if self._is_useful_job_line(line):
                    output.append(line)

        return self._dedupe(output)[:30]

    def _is_useful_job_line(self, line: str) -> bool:
        lower = line.lower()

        if len(line.split()) < 3:
            return False

        if lower.startswith("expires"):
            return False

        if "http" in lower or "www." in lower:
            return False

        if "only shortlisted" in lower:
            return False

        return True

    def _extract_requirement_terms(self, text: str, lines: List[str]) -> List[str]:
        candidates = []
        lower_text = text.lower()

        phrase_patterns = [
            r"\bmember records\b",
            r"\bmembership data\b",
            r"\bdata analysis\b",
            r"\bdata cleansing\b",
            r"\bdata cleaning\b",
            r"\bdata validation\b",
            r"\bquality assurance\b",
            r"\bdata quality\b",
            r"\bdashboard\b",
            r"\bdashboards\b",
            r"\bperformance reports\b",
            r"\breport writing\b",
            r"\bforecasting\b",
            r"\banalytical models\b",
            r"\bdata governance\b",
            r"\bconfidentiality\b",
            r"\bmembership management system\b",
            r"\bcustomer management system\b",
            r"\bmember registrations\b",
            r"\brenewals\b",
            r"\bcancellations\b",
            r"\breinstatements\b",
            r"\bpremium collections\b",
            r"\bemployer schedules\b",
            r"\bbroker submissions\b",
            r"\bdata integration\b",
            r"\bbusiness intelligence\b",
            r"\bmembership administration\b",
            r"\bmedical aid\b",
            r"\binsurance\b",
            r"\bbanking\b",
            r"\bfinancial services\b",
            r"\bhealthcare financing\b",
            r"\bstrategic decision-making\b",
            r"\bprocess improvement\b",
            r"\bprocess improvements\b",
        ]

        for pattern in phrase_patterns:
            if re.search(pattern, lower_text, re.IGNORECASE):
                candidates.append(self._pattern_to_term(pattern))

        for line in lines:
            candidates.extend(self._extract_noun_phrases(line))

        return self._clean_terms(candidates)[:40]

    def _pattern_to_term(self, pattern: str) -> str:
        value = pattern
        value = value.replace(r"\b", "")
        value = value.replace("\\", "")
        value = value.replace("?", "")
        value = value.replace("+", "")
        value = value.replace("*", "")
        value = value.strip()
        return value

    def _extract_noun_phrases(self, line: str) -> List[str]:
        phrases = []
        chunks = re.split(r",|;|\band\b|\bor\b", line, flags=re.IGNORECASE)

        for chunk in chunks:
            clean = chunk.strip(" .:")
            words = clean.split()

            if 2 <= len(words) <= 6:
                lower = clean.lower()

                if any(
                    signal in lower
                    for signal in [
                        "data",
                        "records",
                        "reports",
                        "analysis",
                        "membership",
                        "member",
                        "database",
                        "dashboard",
                        "excel",
                        "sql",
                        "quality",
                        "governance",
                        "confidential",
                        "finance",
                        "claims",
                        "sales",
                        "ict",
                        "premium",
                    ]
                ):
                    phrases.append(lower)

        return phrases

    def _extract_patterns(self, text: str, patterns: List[str]) -> List[str]:
        found = []

        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found.append(self._pattern_to_term(pattern))

        return self._clean_terms(found)

    def _extract_experience_requirement(
        self,
        text: str,
    ) -> str:
        labelled = re.search(
            (
                r"(?:experience\s+level|"
                r"seniority\s+level)\s*"
                r"[:\-]\s*([^\n]+)"
            ),
            text,
            flags=re.IGNORECASE,
        )

        if labelled:
            value = re.sub(
                r"\s+",
                " ",
                labelled.group(1),
            ).strip(" .,-")

            lower = value.lower()

            if any(
                term in lower
                for term in (
                    "entry",
                    "junior",
                    "graduate",
                    "intern",
                    "trainee",
                )
            ):
                return "Entry Level"

            if "mid" in lower:
                return "Mid Level"

            if any(
                term in lower
                for term in (
                    "senior",
                    "lead",
                    "management",
                )
            ):
                return "Senior Level"

            return value

        patterns = [
            (
                r"(?:minimum|at least)?\s*"
                r"(\d+)\+?\s*years?"
                r"(?:\s+of)?\s+"
                r"(?:relevant\s+)?experience"
            ),
            (
                r"(\d+)\+?\s*years?"
                r"['?]?\s+experience"
            ),
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                return (
                    f"{match.group(1)}+ years"
                )

        if re.search(
            (
                r"\bgraduate\b|"
                r"\bintern\b|"
                r"\btrainee\b|"
                r"\bentry[- ]level\b"
            ),
            text,
            flags=re.IGNORECASE,
        ):
            return "Entry Level"

        return "Not specified"

    def _infer_industry(self, text: str, job_title: str) -> str:
        lower = f"{text} {job_title}".lower()

        signals = [
            (["medical aid", "healthcare", "health care", "medical", "patient"], "Medical Aid / Healthcare Financing"),
            (["insurance", "claims"], "Insurance / Claims"),
            (["banking", "financial services", "finance", "premium collections"], "Finance / Financial Services"),
            (["ngo", "programme", "programmes", "beneficiary", "meal", "monitoring and evaluation"], "NGO / MEAL"),
            (["data analyst", "business intelligence", "dashboards", "sql", "data science"], "Data Analytics / Business Intelligence"),
            (["software", "developer", "api", "frontend", "backend"], "Software / Technology"),
            (["accounting", "audit", "reconciliation"], "Accounting / Auditing"),
        ]

        matched = []

        for keywords, label in signals:
            if any(keyword in lower for keyword in keywords):
                matched.append(label)

        if matched:
            return " / ".join(self._dedupe(matched[:2]))

        return "General"

    def _combined_keywords(self, *groups: List[str]) -> List[str]:
        output = []

        for group in groups:
            for item in group or []:
                clean = self._clean_term(item)
                if clean and clean not in output:
                    output.append(clean)

        return output[:60]

    def _clean_terms(self, items: List[str]) -> List[str]:
        output = []

        for item in items:
            clean = self._clean_term(item)

            if not clean:
                continue

            if len(clean) < 2:
                continue

            if clean not in output:
                output.append(clean)

        return output

    def _clean_term(
        self,
        item: str,
    ) -> str:
        value = str(
            item or ""
        ).lower().strip()

        value = value.replace(
            "\\",
            "",
        )

        value = value.replace(
            "?",
            "",
        )

        value = value.replace(
            "*",
            "",
        )

        value = re.sub(
            r"[^a-z0-9&/\- ]+",
            " ",
            value,
        )

        value = re.sub(
            r"[-??]+",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

        aliases = {
            "dashboard": "dashboards",
            "dashboards": "dashboards",
            "database": "databases",
            "databases": "databases",
            "excel": "microsoft excel",
            "microsoft excel": (
                "microsoft excel"
            ),
            "powerbi": "power bi",
            "power bi": "power bi",
            "problem solving": (
                "problem solving"
            ),
            "problem-solving": (
                "problem solving"
            ),
            "teamwork": "team",
            "collaborative": "team",
        }

        return aliases.get(
            value,
            value,
        )

    def _dedupe(self, items: List[str]) -> List[str]:
        output = []
        seen = set()

        for item in items or []:
            clean = str(item).strip()
            key = clean.lower()

            if not clean or key in seen:
                continue

            seen.add(key)
            output.append(clean)

        return output


job_intelligence = JobIntelligence()
