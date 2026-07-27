import re
from typing import List


class KeywordExtractor:
    DOMAIN_KEYWORDS = [
        "python", "sql", "excel", "powerbi", "power bi", "statistics",
        "machine learning", "data analysis", "data cleaning", "dashboard",
        "reporting", "pandas", "numpy", "database", "mysql", "postgresql",
        "etl", "api", "software", "networking", "cybersecurity",

        "accounting", "finance", "bookkeeping", "accounts payable",
        "accounts receivable", "reconciliation", "bank reconciliation",
        "payroll", "tax", "vat", "invoicing", "financial reporting",
        "audit", "budgeting", "sage", "pastel", "quickbooks",
        "debtors", "creditors", "ledger", "journals", "accruals",
        "claims", "claims processing", "claims reporting", "medical aid",
        "financial statements", "management reports",

        "human resources", "hr", "recruitment", "onboarding",
        "employee relations", "performance management", "training",
        "payroll administration", "hris",

        "procurement", "purchasing", "supplier management", "quotations",
        "tendering", "inventory", "stock control", "purchase orders",
        "logistics", "supply chain", "warehouse",

        "monitoring", "evaluation", "learning", "mel", "m&e",
        "data collection", "data quality", "accountability",
        "donor reporting", "programme performance", "results framework",
        "impact measurement", "case management", "adaptive management",
        "ethical data management", "performance reporting",

        "sales", "customer service", "client relations", "marketing",
        "business development", "crm", "communication", "negotiation",

        "administration", "filing", "records management", "office management",
        "report writing", "microsoft office", "planning", "coordination",
    ]

    WEAK_WORDS = {
        "expires", "expiry", "deadline", "closing", "date", "apply", "visit",
        "https", "http", "www", "whatsapp", "channel", "description", "summary",
        "location", "employment", "type", "full-time", "part-time", "in-person",
        "remote", "hybrid", "reports", "report", "manager", "role", "job",
        "candidate", "ideal", "team", "organisation", "organization", "company",
        "department", "responsibilities", "requirements", "duties", "position",
        "post", "must", "should", "will", "able", "ability", "strong", "good",
        "excellent", "required", "preferred", "qualification", "qualifications",
        "experience", "years", "work", "working", "knowledge", "skills",
        "including", "across", "within", "using", "support", "ensure",
        "provide", "assist", "perform", "responsible", "professional",
        "harare", "bulawayo", "zimbabwe", "july", "june", "august",
        "email", "phone", "address", "application", "seeks", "recruit",
        "individual", "self-motivated", "interested", "candidates", "later",
        "goldenknot", "holdings", "financial holdings",
    }

    def normalise(self, keyword: str) -> str:
        keyword = keyword.lower().strip()
        replacements = {
            "power bi": "powerbi",
            "m&e": "mel",
            "monitoring and evaluation": "monitoring evaluation",
            "human resources": "hr",
            "payroll administration": "payroll",
            "performance reporting": "reporting",
            "program performance": "programme performance",
        }
        return replacements.get(keyword, keyword)

    def extract_from_job(self, job_text: str) -> List[str]:
        text = (job_text or "").lower()
        keywords = []

        for phrase in self.DOMAIN_KEYWORDS:
            phrase_lower = phrase.lower().strip()
            if re.search(r"\b" + re.escape(phrase_lower) + r"\b", text):
                normalised = self.normalise(phrase_lower)
                if normalised not in keywords:
                    keywords.append(normalised)

        words = re.findall(r"\b[a-zA-Z][a-zA-Z\-\+]{3,}\b", text)

        for word in words:
            clean = word.lower().strip()

            if clean in self.WEAK_WORDS:
                continue

            if len(clean) < 4:
                continue

            if clean not in keywords:
                keywords.append(clean)

        return keywords[:25]

    def find_in_resume(self, resume_text: str, keywords: List[str]) -> List[str]:
        text = (resume_text or "").lower()
        found = []

        for keyword in keywords:
            kw = keyword.lower().strip()
            normalised = self.normalise(kw)

            variants = {kw, normalised}

            if normalised == "powerbi":
                variants.update({"powerbi", "power bi"})

            if normalised == "mel":
                variants.update({"mel", "m&e", "monitoring and evaluation"})

            if normalised == "hr":
                variants.update({"hr", "human resources"})

            if normalised == "monitoring evaluation":
                variants.update({"monitoring evaluation", "monitoring and evaluation", "m&e", "mel"})

            for variant in variants:
                pattern = r"\b" + re.escape(variant) + r"\b"
                if re.search(pattern, text):
                    if normalised not in found:
                        found.append(normalised)
                    break

        return sorted(found)


keyword_extractor = KeywordExtractor()