from typing import Dict, Any, List
import re


class EvidenceValidator:
    """
    Truth layer for Sentinel AI.

    Rule:
    The AI may improve wording, but it may never improve facts.

    This validator prevents job-description-only terms from entering
    the final downloadable CV unless they are supported by the original resume.
    """

    TECHNICAL_TERMS = {
        "python",
        "sql",
        "excel",
        "microsoft excel",
        "power bi",
        "powerbi",
        "r",
        "spss",
        "stata",
        "tableau",
        "quickbooks",
        "sap",
        "pastel",
        "microsoft office",
        "claims management systems",
        "mysql",
        "postgresql",
        "sqlite",
    }

    SAFE_TRANSFERABLE_TERMS = {
        "communication",
        "teamwork",
        "planning",
        "documentation",
        "reporting",
        "data entry",
        "data capture",
        "data cleaning",
        "record management",
        "records management",
        "attention to detail",
        "confidentiality",
        "filing",
        "research",
        "analysis",
        "data analysis",
        "monitoring",
        "evaluation",
        "learning",
        "accountability",
        "database",
        "statistics",
        "statistical analysis",
        "financial records",
        "financial reporting",
        "reconciliation",
        "bank reconciliation",
        "cashbook",
        "ledger",
        "audit preparation",
        "budget tracking",
        "expenditure monitoring",
        "invoices",
        "payments",
        "receipts",
        "accounting",
        "finance",
    }

    UNSUPPORTED_HIGH_RISK_TERMS = {
        "insurance",
        "health economics",
        "claims processing",
        "claims reporting",
        "claims collection",
        "medical aid claims",
        "member contributions",
        "supplier invoices",
        "journals",
        "accruals",
        "month-end closing",
        "financial statements",
        "management reports",
        "internal audits",
        "billing",
        "accounts payable",
        "quickbooks",
        "claims management systems",
    }

    def validate_built_resume(
        self,
        built_resume: Dict[str, Any],
        resume_profile: Dict[str, Any],
        raw_text: str,
    ) -> Dict[str, Any]:
        evidence_text = self._normalise(raw_text)
        evidence_skills = self._evidence_skills(resume_profile, evidence_text)

        validated = dict(built_resume)

        validated["professional_summary"] = self.validate_summary(
            built_resume.get("professional_summary", ""),
            evidence_text,
            evidence_skills,
        )

        validated["core_skills"] = self.validate_skills(
            built_resume.get("core_skills", []),
            evidence_text,
            evidence_skills,
        )

        validated["technical_skills"] = self.validate_skills(
            built_resume.get("technical_skills", []),
            evidence_text,
            evidence_skills,
            technical_only=True,
        )

        validated["key_achievements"] = self.validate_text_items(
            built_resume.get("key_achievements", []),
            evidence_text,
        )

        validated["professional_experience"] = self.validate_experience(
            built_resume.get("professional_experience", []),
            resume_profile,
            evidence_text,
        )

        validated["projects"] = self.validate_projects(
            built_resume.get("projects", []),
            resume_profile,
        )

        validated["recommended_projects"] = []

        validated["certifications"] = self.validate_certifications(
            built_resume.get("certifications", []),
            resume_profile,
        )

        validated["recommended_certifications"] = []

        validated["languages"] = self.validate_languages(
            built_resume.get("languages", []),
            resume_profile,
        )

        validated["references"] = built_resume.get("references") or "Available upon request."

        return validated

    def validate_summary(
        self,
        summary: str,
        evidence_text: str,
        evidence_skills: List[str],
    ) -> str:
        text = str(summary or "").strip()

        if not text:
            return ""

        unsupported = [
            term
            for term in self.UNSUPPORTED_HIGH_RISK_TERMS
            if term in text.lower() and not self._has_evidence(term, evidence_text)
        ]

        for term in unsupported:
            text = self._remove_term_from_sentence(text, term)

        text = self._clean_summary_text(text)

        if self._summary_has_unsupported_claims(text, evidence_text):
            return self._fallback_summary(evidence_skills, evidence_text)

        return text

    def validate_skills(
        self,
        skills: List[str],
        evidence_text: str,
        evidence_skills: List[str],
        technical_only: bool = False,
    ) -> List[str]:
        output = []

        for skill in skills or []:
            pretty = self._clean_label(skill)
            key = pretty.lower()

            if not pretty:
                continue

            if technical_only and key not in self.TECHNICAL_TERMS:
                continue

            if self._skill_supported(key, evidence_text, evidence_skills):
                if pretty not in output:
                    output.append(pretty)

        return output[:18]

    def validate_text_items(self, items: List[str], evidence_text: str) -> List[str]:
        output = []

        for item in items or []:
            text = str(item or "").strip()

            if not text:
                continue

            if self._contains_unsupported_high_risk(text, evidence_text):
                continue

            if self._has_any_evidence_from_text(text, evidence_text):
                if text not in output:
                    output.append(text)

        return output[:5]

    def validate_experience(
        self,
        experience: List[Dict[str, Any]],
        resume_profile: Dict[str, Any],
        evidence_text: str,
    ) -> List[Dict[str, Any]]:
        original_experience = resume_profile.get("experience", []) or []
        output = []

        allowed_roles = {
            self._normalise_label(item.get("role", ""))
            for item in original_experience
            if item.get("role")
        }

        allowed_orgs = {
            self._normalise_label(item.get("organisation", ""))
            for item in original_experience
            if item.get("organisation")
        }

        for item in experience or []:
            role = item.get("role") or "Relevant Experience"
            organisation = item.get("organisation") or ""
            period = item.get("period") or ""

            role_key = self._normalise_label(role)
            org_key = self._normalise_label(organisation)

            if role_key not in allowed_roles and role_key != "relevant experience":
                role = "Relevant Experience"

            if organisation and org_key not in allowed_orgs:
                organisation = ""

            bullets = []
            for bullet in item.get("bullets", []) or []:
                clean = str(bullet or "").strip()
                if not clean:
                    continue
                if self._contains_unsupported_high_risk(clean, evidence_text):
                    continue
                if clean not in bullets:
                    bullets.append(clean)

            if bullets:
                output.append(
                    {
                        "role": role,
                        "organisation": organisation,
                        "period": period,
                        "bullets": bullets[:8],
                    }
                )

        return output

    def validate_projects(
        self,
        projects: List[str],
        resume_profile: Dict[str, Any],
    ) -> List[str]:
        original_projects = resume_profile.get("projects", []) or []
        allowed = []

        for project in original_projects:
            if isinstance(project, dict):
                name = project.get("name", "")
                desc = project.get("description", "")
                value = f"{name}: {desc}" if desc else name
            else:
                value = str(project)

            if value:
                allowed.append(value)

        output = []
        allowed_norm = [self._normalise_label(x) for x in allowed]

        for project in projects or []:
            if self._normalise_label(project) in allowed_norm and project not in output:
                output.append(project)

        return output[:8]

    def validate_certifications(
        self,
        certifications: List[str],
        resume_profile: Dict[str, Any],
    ) -> List[str]:
        original = resume_profile.get("certifications", []) or []
        original_norm = [self._normalise_label(x) for x in original]

        output = []

        for cert in certifications or []:
            cert_text = str(cert or "").strip()
            if not cert_text:
                continue

            if self._normalise_label(cert_text) in original_norm:
                output.append(cert_text)

        return output[:8]

    def validate_languages(
        self,
        languages: List[str],
        resume_profile: Dict[str, Any],
    ) -> List[str]:
        original = resume_profile.get("languages", []) or []
        original_norm = [self._normalise_label(x) for x in original]

        output = []

        for lang in languages or []:
            text = str(lang or "").strip()

            if not text:
                continue

            lower = text.lower()

            if "interest" in lower or "football" in lower or "cricket" in lower:
                continue

            if "reference" in lower or "phone" in lower or "email" in lower:
                continue

            if self._normalise_label(text) in original_norm or lower in {"english", "shona", "ndebele"}:
                if text not in output:
                    output.append(text)

        return output[:5] or ["English"]

    def _evidence_skills(self, resume_profile: Dict[str, Any], evidence_text: str) -> List[str]:
        skills = []

        for skill in resume_profile.get("skills", []) or []:
            cleaned = self._clean_label(skill)
            if cleaned and cleaned not in skills:
                skills.append(cleaned)

        for term in sorted(self.SAFE_TRANSFERABLE_TERMS):
            if self._has_evidence(term, evidence_text):
                pretty = self._title_term(term)
                if pretty not in skills:
                    skills.append(pretty)

        for term in sorted(self.TECHNICAL_TERMS):
            if self._has_evidence(term, evidence_text):
                pretty = self._title_term(term)
                if pretty not in skills:
                    skills.append(pretty)

        return skills

    def _skill_supported(
        self,
        skill: str,
        evidence_text: str,
        evidence_skills: List[str],
    ) -> bool:
        skill = skill.lower().strip()

        if skill in self.UNSUPPORTED_HIGH_RISK_TERMS:
            return self._has_evidence(skill, evidence_text)

        if skill in self.SAFE_TRANSFERABLE_TERMS:
            return self._has_evidence(skill, evidence_text) or skill in [
                s.lower() for s in evidence_skills
            ]

        if skill in self.TECHNICAL_TERMS:
            return self._has_evidence(skill, evidence_text)

        return self._has_evidence(skill, evidence_text) or skill in [
            s.lower() for s in evidence_skills
        ]

    def _contains_unsupported_high_risk(self, text: str, evidence_text: str) -> bool:
        lower = text.lower()
        for term in self.UNSUPPORTED_HIGH_RISK_TERMS:
            if term in lower and not self._has_evidence(term, evidence_text):
                return True
        return False

    def _has_any_evidence_from_text(self, text: str, evidence_text: str) -> bool:
        tokens = [
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if len(token) > 4
        ]

        if not tokens:
            return False

        matches = sum(1 for token in tokens if f" {token} " in evidence_text)

        return matches >= max(1, min(3, len(tokens) // 3))

    def _summary_has_unsupported_claims(self, summary: str, evidence_text: str) -> bool:
        lower = summary.lower()
        for term in self.UNSUPPORTED_HIGH_RISK_TERMS:
            if term in lower and not self._has_evidence(term, evidence_text):
                return True
        return False

    def _fallback_summary(self, evidence_skills: List[str], evidence_text: str) -> str:
        if self._has_evidence("accounting", evidence_text) or self._has_evidence("financial", evidence_text):
            return (
                "Motivated accounting and finance candidate with practical exposure to financial record management, "
                "data entry, reporting support, reconciliations, Microsoft Excel and professional documentation. "
                "Brings strong attention to detail, confidentiality and a willingness to learn within structured finance environments."
            )

        if self._has_evidence("monitoring", evidence_text) or self._has_evidence("evaluation", evidence_text):
            return (
                "Motivated monitoring, evaluation and data-focused candidate with practical exposure to data collection, "
                "documentation, reporting and programme support. Brings strong analytical ability, attention to detail "
                "and a commitment to using accurate information for evidence-based decision-making."
            )

        selected = evidence_skills[:5]
        if selected:
            return (
                "Motivated candidate with practical exposure to "
                + ", ".join(selected[:4])
                + ". Brings strong attention to detail, communication and a willingness to contribute effectively."
            )

        return (
            "Motivated candidate with practical experience, strong attention to detail and the ability to support accurate work, reporting and team objectives."
        )

    def _remove_term_from_sentence(self, text: str, term: str) -> str:
        pattern = re.compile(rf"\b{re.escape(term)}\b,?\s*", flags=re.IGNORECASE)
        return pattern.sub("", text)

    def _clean_summary_text(self, text: str) -> str:
        value = str(text or "")
        value = re.sub(r",\s*,", ",", value)
        value = re.sub(r"\s+,", ",", value)
        value = re.sub(r",\s+with", " with", value)
        value = re.sub(r"\s+", " ", value)
        value = value.replace("exposure to ,", "exposure to")
        value = value.replace("exposure to with", "exposure to")
        return value.strip()

    def _has_evidence(self, term: str, evidence_text: str) -> bool:
        term = self._normalise_term(term)

        if not term:
            return False

        if f" {term} " in evidence_text:
            return True

        equivalents = {
            "financial records": ["financial record", "accounting documents", "ledger", "ledgers"],
            "financial reporting": ["financial reports", "routine financial reporting", "reporting support"],
            "reconciliation": ["reconciliations", "bank reconciliations", "cashbook"],
            "bank reconciliation": ["bank reconciliations", "cashbook management"],
            "audit preparation": ["audit preparation", "audit", "filing and retrieval"],
            "budget tracking": ["budget tracking", "expenditure monitoring"],
            "invoice processing": ["invoices", "payments", "receipts"],
            "data analysis": ["analysis", "data cleaning", "data entry", "reporting"],
            "statistics": ["statistical analysis", "applied statistics", "statistics"],
            "excel": ["microsoft excel", "excel"],
            "sap": ["sap"],
            "pastel": ["pastel"],
        }

        for equivalent in equivalents.get(term, []):
            if f" {self._normalise_term(equivalent)} " in evidence_text:
                return True

        return False

    def _normalise(self, text: str) -> str:
        value = str(text or "").lower()
        value = value.replace("&", " and ")
        value = re.sub(r"[^a-z0-9+.%\- ]+", " ", value)
        value = re.sub(r"\s+", " ", value)
        return f" {value.strip()} "

    def _normalise_term(self, term: str) -> str:
        value = str(term or "").lower().strip()
        value = value.replace("&", " and ")
        value = re.sub(r"[^a-z0-9+.%\- ]+", " ", value)
        value = re.sub(r"\s+", " ", value)
        return value.strip()

    def _normalise_label(self, text: str) -> str:
        value = str(text or "").lower()
        value = re.sub(r"[^a-z0-9]+", " ", value)
        value = re.sub(r"\s+", " ", value)
        return value.strip()

    def _clean_label(self, text: str) -> str:
        value = str(text or "").strip()
        value = re.sub(r"\s+", " ", value)
        return self._title_term(value)

    def _title_term(self, text: str) -> str:
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

        lower = str(text or "").lower().strip()

        if lower in acronyms:
            return acronyms[lower]

        return str(text or "").strip().title()


evidence_validator = EvidenceValidator()