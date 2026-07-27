from typing import Dict, Any, List
import re


class ProfessionalPolisher:
    CANONICAL_SKILLS = {
        "accounting documentation and ledger updates": "Accounting Documentation",
        "transaction recording": "Transaction Recording",
        "cashbook support and bank reconciliation support": "Bank Reconciliation & Cashbook Management",
        "bank reconciliation support": "Bank Reconciliation",
        "cashbook support": "Cashbook Management",
        "invoice processing": "Invoice Processing",
        "payments": "Payment Processing",
        "receipts": "Receipting",
        "filing and financial document control": "Financial Document Control",
        "budget tracking": "Budget Tracking",
        "expenditure monitoring": "Expenditure Monitoring",
        "audit preparation and compliance awareness": "Audit Preparation & Compliance",
        "pastel accounting": "Pastel Accounting",
        "microsoft excel and microsoft office": "Microsoft Excel & Microsoft Office",
        "financial records management": "Financial Records Management",
        "record management": "Records Management",
        "records management": "Records Management",
        "reporting": "Financial Reporting",
        "accounting": "Accounting",
        "monitoring": "",
        "excel": "Microsoft Excel",
    }

    WEAK_SKILLS = {
        "reporting",
        "monitoring",
        "accounting",
        "finance",
        "documentation",
        "analysis",
    }

    REFERENCE_TITLES = {
        "accountant",
        "chief accountant",
        "supervisor",
        "manager",
        "finance manager",
        "lecturer",
        "program coordinator",
        "programme coordinator",
        "m&e officer",
        "meal officer",
        "director",
        "administrator",
        "hr officer",
        "human resources officer",
    }

    def polish(
        self,
        built_resume: Dict[str, Any],
        resume_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        polished = dict(built_resume)

        polished["core_skills"] = self.polish_skills(
            built_resume.get("core_skills", [])
        )

        polished["technical_skills"] = self.polish_skills(
            built_resume.get("technical_skills", []),
            technical=True,
        )

        polished["key_achievements"] = self.polish_achievements(
            achievements=built_resume.get("key_achievements", []),
            experience=built_resume.get("professional_experience", []),
        )

        polished["certifications"] = self.polish_certifications(
            built_resume.get("certifications", [])
        )

        polished["references"] = self.polish_references(
            built_resume.get("references", ""),
            resume_profile=resume_profile,
        )

        return polished

    def polish_skills(self, skills: List[str], technical: bool = False) -> List[str]:
        output = []
        seen = set()

        for skill in skills or []:
            clean = self._clean(skill)
            canonical = self._canonical_skill(clean)
            key = canonical.lower()

            if not canonical:
                continue

            if key in seen:
                continue

            if key in self.WEAK_SKILLS and self._has_stronger_skill(key, seen):
                continue

            if key == "monitoring":
                continue

            seen.add(key)
            output.append(canonical)

        return output[:16 if technical else 18]

    def polish_achievements(
        self,
        achievements: List[str],
        experience: List[Dict[str, Any]],
    ) -> List[str]:
        experience_bullets = []

        for item in experience or []:
            for bullet in item.get("bullets", []) or []:
                experience_bullets.append(self._normalise_sentence(bullet))

        output = []

        for achievement in achievements or []:
            clean = self._clean_sentence(achievement)
            norm = self._normalise_sentence(clean)

            if not clean:
                continue

            if norm in experience_bullets:
                continue

            if self._is_generic_achievement(clean):
                continue

            if clean not in output:
                output.append(clean)

        return output[:5]

    def polish_certifications(self, certifications: List[str]) -> List[str]:
        output = []

        for cert in certifications or []:
            text = self._clean(cert)

            if not text:
                continue

            if text.lower().startswith("completed practical training"):
                if output:
                    output[-1] = output[-1] + " — " + text
                else:
                    output.append(text)
                continue

            if text not in output:
                output.append(text)

        return output[:8]

    def polish_references(
        self,
        references,
        resume_profile: Dict[str, Any],
    ) -> str:
        lines = self._reference_lines(references)

        if not lines:
            return "Available upon request."

        lines = self._remove_bad_reference_lines(lines)

        if not lines:
            return "Available upon request."

        organisation_hint = self._reference_org_hint(lines, resume_profile)
        blocks = self._group_reference_blocks(lines)

        formatted_blocks = []

        for block in blocks:
            parsed = self._parse_reference_block(block)

            if not parsed.get("organisation") and organisation_hint:
                parsed["organisation"] = organisation_hint

            formatted = self._render_reference(parsed)

            if formatted:
                formatted_blocks.append(formatted)

        formatted_blocks = self._dedupe_reference_blocks(formatted_blocks)

        return "\n\n".join(formatted_blocks) if formatted_blocks else "Available upon request."

    def _reference_lines(self, references) -> List[str]:
        if not references:
            return []

        if isinstance(references, str):
            return [line.strip() for line in references.splitlines() if line.strip()]

        if isinstance(references, list):
            return [str(line).strip() for line in references if str(line).strip()]

        return []

    def _remove_bad_reference_lines(self, lines: List[str]) -> List[str]:
        output = []

        for line in lines:
            clean = self._clean(line)
            lower = clean.lower()

            if not clean:
                continue

            if lower in ["reference", "references", "professional references"]:
                continue

            if lower in ["english", "shona", "ndebele"]:
                continue

            if "interest" in lower or "football" in lower or "cricket" in lower:
                continue

            if clean not in output:
                output.append(clean)

        return output

    def _group_reference_blocks(self, lines: List[str]) -> List[List[str]]:
        blocks = []
        current = []

        for line in lines:
            if self._looks_like_reference_name(line) and current:
                blocks.append(current)
                current = [line]
            else:
                current.append(line)

        if current:
            blocks.append(current)

        return blocks

    def _parse_reference_block(self, block: List[str]) -> Dict[str, str]:
        parsed = {
            "name": "",
            "title": "",
            "organisation": "",
            "phone": "",
            "email": "",
        }

        for line in block:
            clean = self._clean(line)
            lower = clean.lower()

            if not clean:
                continue

            if self._looks_like_phone(clean):
                parsed["phone"] = self._normalise_phone(clean)
                continue

            if self._looks_like_email(clean):
                parsed["email"] = self._normalise_email(clean)
                continue

            if self._looks_like_organisation(clean):
                if not parsed["organisation"]:
                    parsed["organisation"] = clean
                continue

            if self._looks_like_reference_title(clean):
                if not parsed["title"]:
                    parsed["title"] = clean
                continue

            if self._looks_like_reference_name(clean):
                if not parsed["name"]:
                    parsed["name"] = clean
                continue

            if not parsed["title"]:
                parsed["title"] = clean
            elif not parsed["organisation"] and self._could_be_organisation(clean):
                parsed["organisation"] = clean

        return parsed

    def _render_reference(self, parsed: Dict[str, str]) -> str:
        lines = []

        if parsed.get("name"):
            lines.append(parsed["name"])

        if parsed.get("title"):
            lines.append(parsed["title"])

        if parsed.get("organisation"):
            lines.append(parsed["organisation"])

        if parsed.get("phone"):
            lines.append(parsed["phone"])

        if parsed.get("email"):
            lines.append(parsed["email"])

        cleaned = []
        seen = set()

        for line in lines:
            key = self._normalise_sentence(line)

            if not line or key in seen:
                continue

            seen.add(key)
            cleaned.append(line)

        return "\n".join(cleaned[:5])

    def _dedupe_reference_blocks(self, blocks: List[str]) -> List[str]:
        output = []
        seen_names = set()

        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue

            name_key = self._normalise_sentence(lines[0])

            if name_key in seen_names:
                continue

            seen_names.add(name_key)
            output.append("\n".join(lines))

        return output

    def _reference_org_hint(
        self,
        lines: List[str],
        resume_profile: Dict[str, Any],
    ) -> str:
        org_counts = {}

        for line in lines:
            if self._looks_like_organisation(line):
                key = self._clean(line)
                org_counts[key] = org_counts.get(key, 0) + 1

        if org_counts:
            return sorted(org_counts.items(), key=lambda item: item[1], reverse=True)[0][0]

        for exp in resume_profile.get("experience", []) or []:
            org = exp.get("organisation")
            if org:
                return org

        return ""

    def _canonical_skill(self, skill: str) -> str:
        key = skill.lower()
        return self.CANONICAL_SKILLS.get(key, skill)

    def _has_stronger_skill(self, weak_skill: str, seen: set) -> bool:
        stronger_map = {
            "reporting": {"financial reporting", "management reports", "excel reporting"},
            "monitoring": {"monitoring & evaluation", "programme monitoring"},
            "accounting": {"accounting documentation", "financial records management"},
            "finance": {"financial records management", "financial reporting"},
            "documentation": {"accounting documentation", "financial document control"},
            "analysis": {"data analysis", "financial reporting"},
        }

        return bool(stronger_map.get(weak_skill, set()).intersection(seen))

    def _is_generic_achievement(self, text: str) -> bool:
        lower = text.lower()

        generic = [
            "applied data analysis and reporting techniques",
            "supported financial reporting, reconciliation and records management",
            "delivered practical support across assigned responsibilities",
        ]

        if lower.strip(".") in generic:
            return True

        if len(text.split()) < 7:
            return True

        return False

    def _looks_like_reference_name(self, line: str) -> bool:
        clean = line.strip()

        if ":" in clean:
            return False

        if self._looks_like_phone(clean):
            return False

        if self._looks_like_email(clean):
            return False

        if self._looks_like_organisation(clean):
            return False

        if self._looks_like_reference_title(clean):
            return False

        if any(ch.isdigit() for ch in clean):
            return False

        words = clean.split()

        if len(words) < 2 or len(words) > 4:
            return False

        titles = {"mr", "mrs", "ms", "dr", "prof"}
        first = words[0].lower().replace(".", "")

        if first in titles:
            return True

        return all(word[0].isupper() or "." in word for word in words if word)

    def _looks_like_reference_title(self, line: str) -> bool:
        lower = line.lower().strip()

        if lower in self.REFERENCE_TITLES:
            return True

        title_words = [
            "accountant",
            "manager",
            "supervisor",
            "coordinator",
            "officer",
            "director",
            "administrator",
            "lecturer",
            "chief",
            "head",
            "finance",
            "human resources",
            "program",
            "programme",
        ]

        return any(word in lower for word in title_words) and not self._looks_like_organisation(line)

    def _looks_like_organisation(self, line: str) -> bool:
        lower = line.lower()

        org_words = [
            "ministry",
            "department",
            "council",
            "university",
            "college",
            "company",
            "agency",
            "authority",
            "organisation",
            "organization",
            "pvt",
            "ltd",
            "limited",
            "corporation",
            "infrastructure",
            "development",
            "transport",
            "ema",
            "environmental management",
        ]

        return any(word in lower for word in org_words)

    def _could_be_organisation(self, line: str) -> bool:
        lower = line.lower()

        if self._looks_like_organisation(line):
            return True

        if len(line.split()) >= 3 and not self._looks_like_reference_title(line):
            return True

        return any(word in lower for word in ["office", "finance department", "revenue hall"])

    def _looks_like_phone(self, line: str) -> bool:
        lower = line.lower()
        digits = re.sub(r"\D", "", line)

        return (
            "phone" in lower
            or "cell" in lower
            or "mobile" in lower
            or line.strip().startswith("+")
            or len(digits) >= 9
        )

    def _normalise_phone(self, line: str) -> str:
        clean = self._clean(line)

        if clean.lower().startswith("phone"):
            return clean

        return f"Phone: {clean}"

    def _looks_like_email(self, line: str) -> bool:
        return bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", line))

    def _normalise_email(self, line: str) -> str:
        match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", line)

        if not match:
            return self._clean(line)

        email = match.group(0).lower()

        if line.lower().startswith("email"):
            return f"Email: {email}"

        return f"Email: {email}"

    def _clean(self, text: str) -> str:
        value = str(text or "").strip()
        value = re.sub(r"\s+", " ", value)
        value = value.replace("Email :", "Email:")
        value = value.replace("Phone :", "Phone:")
        return value.strip(" -–—|•*")

    def _clean_sentence(self, text: str) -> str:
        value = self._clean(text)

        if value and not value.endswith("."):
            value += "."

        return value

    def _normalise_sentence(self, text: str) -> str:
        value = str(text or "").lower()
        value = re.sub(r"[^a-z0-9]+", " ", value)
        value = re.sub(r"\s+", " ", value)
        return value.strip()


professional_polisher = ProfessionalPolisher()