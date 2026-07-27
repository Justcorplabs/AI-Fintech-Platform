import re
from typing import Dict, Any, List, Optional


class JobParser:
    WEAK_WORDS = {
        "expires", "expiry", "deadline", "closing", "date", "apply", "visit",
        "https", "http", "www", "whatsapp", "channel", "description", "summary",
        "location", "employment", "type", "reports", "report", "manager",
        "responsibilities", "duties", "requirements", "qualifications",
        "candidate", "ideal", "must", "should", "will", "able", "ability",
        "strong", "good", "excellent", "required", "preferred", "team",
        "company", "organisation", "organization", "department", "role",
        "position", "post", "job", "seeks", "recruit", "individual",
        "self-motivated", "interested", "candidates", "email", "later",
    }

    TITLE_WORDS = [
        "trainee", "officer", "coordinator", "assistant", "analyst",
        "accountant", "clerk", "manager", "administrator", "developer",
        "engineer", "teacher", "nurse", "consultant", "specialist",
        "intern", "technician", "supervisor", "controller", "cashier",
        "auditor", "bookkeeper", "data clerk", "graduate trainee",
    ]

    ORG_SUFFIXES = [
        "holdings", "financial holdings", "pvt ltd", "private limited",
        "ltd", "limited", "inc", "corporation", "company", "bank",
        "foundation", "trust", "university", "council", "services",
        "labs", "group",
    ]

    def parse(self, job_description: str) -> Dict[str, Any]:
        text = job_description or ""
        lower = text.lower()

        return {
            "job_title": self.extract_title(text),
            "organisation": self.extract_organisation(text),
            "location": self.extract_location(text),
            "employment_type": self.extract_employment_type(text),
            "industry": self.detect_industry(lower),
            "experience_requirement": self.extract_experience(lower),
            "qualifications": self.extract_qualifications(text),
            "responsibilities": self.extract_responsibilities(text),
        }

    def clean_lines(self, text: str) -> List[str]:
        return [line.strip().strip("*").strip() for line in text.splitlines() if line.strip()]

    def extract_title(self, text: str) -> str:
        lines = self.clean_lines(text)

        for line in lines[:12]:
            lower = line.lower()

            if any(skip in lower for skip in [
                "expires", "location:", "employment type", "reports to",
                "closing date", "job description", "summary", "how to apply",
                "http", "www", "whatsapp",
            ]):
                continue

            if len(line.split()) <= 8 and len(line) <= 90:
                if any(word in lower for word in self.TITLE_WORDS):
                    return line.title()

        patterns = [
            r"(?:job title|position|post|role)\s*[:\-]\s*(.+)",
            r"\*([^*]+(?:trainee|officer|coordinator|assistant|analyst|accountant|clerk|manager|administrator|developer|engineer|specialist|technician|auditor)[^*]*)\*",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip().strip("*").strip().title()

        return "the advertised role"

    def extract_organisation(self, text: str) -> str:
        lines = self.clean_lines(text)

        for line in lines[:25]:
            clean = re.sub(r"[^A-Za-z0-9&.\- ]", "", line).strip()
            lower = clean.lower()

            if "whatsapp" in lower or "http" in lower or "expires" in lower:
                continue

            if clean.isupper() and len(clean.split()) <= 8:
                if any(suffix in lower for suffix in self.ORG_SUFFIXES):
                    return clean.title()

            if " seeks to recruit" in lower:
                org = clean.split(" seeks to recruit")[0].strip()
                if len(org.split()) <= 8:
                    return org.title()

        org_patterns = [
            r"\b([A-Z][A-Z0-9&.\- ]{3,80}?(?:FINANCIAL HOLDINGS|HOLDINGS|PVT LTD|PRIVATE LIMITED|LTD|LIMITED|BANK|FOUNDATION|TRUST|UNIVERSITY|COUNCIL|SERVICES|GROUP))\b",
            r"\b([A-Za-z0-9&.\-]+\.org)\b",
        ]

        for pattern in org_patterns:
            match = re.search(pattern, text)
            if match:
                org = match.group(1).strip()
                if "whatsapp" not in org.lower():
                    return org.title()

        return "your organisation"

    def extract_location(self, text: str) -> Optional[str]:
        match = re.search(r"location\s*[:\-]\s*(.+)", text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().split("\n")[0]
        return None

    def extract_employment_type(self, text: str) -> Optional[str]:
        match = re.search(r"employment type\s*[:\-]\s*(.+)", text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().split("\n")[0]

        lower = text.lower()
        if "full-time" in lower or "full time" in lower:
            return "Full-Time"
        if "part-time" in lower or "part time" in lower:
            return "Part-Time"
        if "contract" in lower:
            return "Contract"
        return None

    def extract_experience(self, text: str) -> Optional[str]:
        patterns = [
            r"(\d+)\+?\s*years?\s*(?:of\s*)?experience",
            r"at least\s*(\d+)\s*years?",
            r"minimum\s*(\d+)\s*years?",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return f"{match.group(1)} years"

        if "graduate trainee" in text or "trainee" in text:
            return "Graduate / Entry level"

        return None

    def extract_qualifications(self, text: str) -> List[str]:
        lines = self.clean_lines(text)
        results = []
        capture = False

        for line in lines:
            lower = line.lower()

            if "qualifications" in lower or "qualification" in lower:
                capture = True
                continue

            if capture and any(stop in lower for stop in ["how to apply", "duties", "responsibilities"]):
                break

            if capture:
                cleaned = re.sub(r"^\d+[\).]\s*", "", line).strip()
                if len(cleaned) > 8:
                    results.append(cleaned)

        return results[:8]

    def extract_responsibilities(self, text: str) -> List[str]:
        lines = self.clean_lines(text)
        results = []
        capture = False

        for line in lines:
            lower = line.lower()

            if "duties" in lower or "responsibilities" in lower:
                capture = True
                continue

            if capture and any(stop in lower for stop in ["qualifications", "how to apply"]):
                break

            if capture:
                cleaned = re.sub(r"^\d+[\).]\s*", "", line).strip()
                if len(cleaned) > 12:
                    results.append(cleaned)

        return results[:10]

    def detect_industry(self, text: str) -> str:
        if any(w in text for w in ["accounting", "finance", "bank", "audit", "claims", "reconciliation"]):
            return "Finance / Accounting"
        if any(w in text for w in ["monitoring", "evaluation", "mel", "donor", "programme"]):
            return "NGO / Programme / MEL"
        if any(w in text for w in ["software", "developer", "python", "api", "database"]):
            return "Technology / IT"
        if any(w in text for w in ["procurement", "supplier", "inventory", "logistics"]):
            return "Procurement / Supply Chain"
        if any(w in text for w in ["hr", "recruitment", "employee", "onboarding"]):
            return "Human Resources"
        return "General"


job_parser = JobParser()