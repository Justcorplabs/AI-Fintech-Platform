from typing import Dict, Any, List
import re


class SemanticMatcher:
    SEMANTIC_MAP = {
        "statistics": [
            "statistical analysis",
            "statistical modelling",
            "statistical modeling",
            "quantitative analysis",
            "data analysis",
            "data analytics",
            "analytics",
            "applied statistics",
        ],
        "monitoring": [
            "monitoring and evaluation",
            "m&e",
            "meal",
            "programme monitoring",
            "program monitoring",
            "tracking",
            "performance monitoring",
        ],
        "evaluation": [
            "monitoring and evaluation",
            "m&e",
            "meal",
            "assessment",
            "programme evaluation",
            "program evaluation",
            "impact evaluation",
        ],
        "learning": [
            "meal",
            "learning agenda",
            "knowledge management",
            "research",
            "evidence generation",
            "lessons learnt",
            "lessons learned",
        ],
        "data collection": [
            "survey",
            "surveys",
            "field data",
            "data capture",
            "data entry",
            "questionnaire",
            "telephonic surveys",
            "beneficiary data",
            "participant data",
        ],
        "database": [
            "data system",
            "datasets",
            "records",
            "data entry",
            "data capture",
            "data management",
            "spreadsheet",
            "excel database",
        ],
        "accountability": [
            "complaints",
            "feedback",
            "participant enquiries",
            "participant inquiries",
            "referral",
            "referral pathways",
            "stakeholder engagement",
            "community feedback",
        ],
        "communication": [
            "stakeholder communication",
            "client communication",
            "customer service",
            "call centre",
            "call center",
            "inbound calls",
            "outbound calls",
            "front desk",
            "liaison",
            "participant support",
        ],
        "planning": [
            "implementation planning",
            "programme planning",
            "program planning",
            "work planning",
            "activity planning",
            "coordination",
        ],
        "excel": [
            "microsoft excel",
            "spreadsheet",
            "spreadsheets",
            "pivot table",
            "pivot tables",
            "vlookup",
            "excel reporting",
        ],
        "powerbi": [
            "power bi",
            "business intelligence",
            "dashboard",
            "dashboards",
            "data visualisation",
            "data visualization",
        ],
        "sql": [
            "mysql",
            "postgresql",
            "sqlite",
            "database querying",
            "queries",
        ],
        "python": [
            "pandas",
            "numpy",
            "scikit-learn",
            "sklearn",
            "matplotlib",
            "seaborn",
            "machine learning",
        ],
        "finance": [
            "financial",
            "financial records",
            "financial reporting",
            "accounts",
            "accounting",
            "payments",
            "receipts",
            "cashbook",
        ],
        "accounting": [
            "accounts",
            "financial records",
            "ledger",
            "ledgers",
            "bookkeeping",
            "cashbook",
            "payments",
            "receipts",
        ],
        "reconciliation": [
            "bank reconciliation",
            "cashbook reconciliation",
            "reconciliations",
            "reconciled",
            "matching transactions",
        ],
        "claims processing": [
            "claims handling",
            "claims administration",
            "medical claims",
            "medical aid claims",
            "claims verification",
            "claims collection",
        ],
        "claims reporting": [
            "claims reports",
            "payment status reports",
            "outstanding claims",
            "claims trends",
            "management reports",
            "financial reports",
            "reporting",
        ],
        "claims collection": [
            "claims collection",
            "medical aid claims",
            "claims verification",
            "supplier invoices",
            "member contributions",
        ],
        "medical aid claims": [
            "medical claims",
            "healthcare finance",
            "patient accounts",
            "billing",
            "claims processing",
        ],
        "supplier invoices": [
            "invoice processing",
            "invoices",
            "supplier payments",
            "accounts payable",
            "payments",
        ],
        "member contributions": [
            "contributions",
            "member accounts",
            "accounts",
            "billing",
            "receipts",
        ],
        "journals": [
            "journal entries",
            "general ledger",
            "ledger updates",
            "accounting entries",
        ],
        "accruals": [
            "month-end accruals",
            "accrual accounting",
            "month-end closing",
        ],
        "month-end closing": [
            "month end",
            "month-end",
            "closing processes",
            "financial close",
            "monthly reporting",
        ],
        "financial statements": [
            "financial reports",
            "management accounts",
            "reporting",
            "financial reporting",
        ],
        "management reports": [
            "management reporting",
            "monthly reports",
            "quarterly reports",
            "reports for management",
            "dashboards",
        ],
        "internal audits": [
            "audit preparation",
            "audit support",
            "compliance",
            "filing",
            "document control",
        ],
        "quickbooks": [
            "quick books",
            "accounting software",
            "sage",
            "pastel",
            "sap",
        ],
        "call centre": [
            "call center",
            "front desk",
            "inbound calls",
            "outbound calls",
            "participant calls",
            "telephone surveys",
            "telephonic surveys",
            "customer service",
        ],
        "participant support": [
            "participant enquiries",
            "participant inquiries",
            "complaints",
            "referral",
            "front desk",
            "stakeholder liaison",
            "community support",
        ],
        "stakeholder engagement": [
            "stakeholder communication",
            "liaison",
            "participant support",
            "community engagement",
            "client communication",
        ],
    }

    STOP_TERMS = {
        "and",
        "or",
        "the",
        "a",
        "an",
        "of",
        "to",
        "in",
        "for",
        "with",
        "on",
        "at",
        "by",
        "from",
    }

    def match(
        self,
        resume_text: str,
        requirements: List[str],
    ) -> Dict[str, Any]:
        text = self._normalise(resume_text)
        results = []

        for requirement in requirements or []:
            req = self._normalise_term(requirement)

            if not req:
                continue

            result = self._match_one(text, req)
            results.append(result)

        matched = [r["requirement"] for r in results if r["status"] == "matched"]
        partial = [r["requirement"] for r in results if r["status"] == "partial"]
        missing = [r["requirement"] for r in results if r["status"] == "missing"]

        weighted_score = self._score(results)

        return {
            "results": results,
            "matched": matched,
            "partial": partial,
            "missing": missing,
            "score": weighted_score,
        }

    def _match_one(self, text: str, requirement: str) -> Dict[str, Any]:
        direct_match = self._contains_phrase(text, requirement)

        if direct_match:
            return {
                "requirement": requirement,
                "status": "matched",
                "confidence": 100,
                "evidence": requirement,
                "match_type": "direct",
            }

        synonyms = self._synonyms_for(requirement)

        for synonym in synonyms:
            if self._contains_phrase(text, synonym):
                return {
                    "requirement": requirement,
                    "status": "matched",
                    "confidence": 92,
                    "evidence": synonym,
                    "match_type": "semantic",
                }

        stem_result = self._stem_match(text, requirement)
        if stem_result:
            return {
                "requirement": requirement,
                "status": "matched",
                "confidence": 85,
                "evidence": stem_result,
                "match_type": "stem",
            }

        partial = self._partial_match(text, requirement, synonyms)
        if partial:
            return {
                "requirement": requirement,
                "status": "partial",
                "confidence": partial["confidence"],
                "evidence": partial["evidence"],
                "match_type": "partial",
            }

        return {
            "requirement": requirement,
            "status": "missing",
            "confidence": 0,
            "evidence": "",
            "match_type": "none",
        }

    def _score(self, results: List[Dict[str, Any]]) -> float:
        if not results:
            return 0.0

        total = sum(result.get("confidence", 0) for result in results)
        return round(total / len(results), 2)

    def _normalise(self, text: str) -> str:
        value = str(text or "").lower()
        value = value.replace("&", " and ")
        value = re.sub(r"[^a-z0-9+\-.% ]+", " ", value)
        value = re.sub(r"\s+", " ", value)
        return f" {value.strip()} "

    def _normalise_term(self, term: str) -> str:
        value = str(term or "").lower().strip()
        value = value.replace("&", " and ")
        value = re.sub(r"[^a-z0-9+\-.% ]+", " ", value)
        value = re.sub(r"\s+", " ", value)
        return value.strip()

    def _contains_phrase(self, text: str, phrase: str) -> bool:
        phrase = self._normalise_term(phrase)

        if not phrase:
            return False

        return f" {phrase} " in text

    def _synonyms_for(self, requirement: str) -> List[str]:
        req = self._normalise_term(requirement)

        synonyms = []

        for key, values in self.SEMANTIC_MAP.items():
            key_norm = self._normalise_term(key)

            if req == key_norm:
                synonyms.extend(values)

            if req in [self._normalise_term(v) for v in values]:
                synonyms.append(key)

        return list(dict.fromkeys([self._normalise_term(s) for s in synonyms if s]))

    def _stem_match(self, text: str, requirement: str) -> str:
        tokens = self._tokens(requirement)

        if not tokens:
            return ""

        stems = [self._stem(token) for token in tokens if token not in self.STOP_TERMS]

        if not stems:
            return ""

        text_tokens = self._tokens(text)
        text_stems = {self._stem(token): token for token in text_tokens}

        matched = [text_stems[stem] for stem in stems if stem in text_stems]

        if len(matched) == len(stems):
            return " ".join(matched)

        return ""

    def _partial_match(
        self,
        text: str,
        requirement: str,
        synonyms: List[str],
    ) -> Dict[str, Any]:
        candidates = [requirement, *synonyms]
        best = {"confidence": 0, "evidence": ""}

        text_tokens = set(self._tokens(text))

        for candidate in candidates:
            tokens = [
                token
                for token in self._tokens(candidate)
                if token not in self.STOP_TERMS
            ]

            if not tokens:
                continue

            matched = [token for token in tokens if token in text_tokens]
            ratio = len(matched) / len(tokens)

            if ratio >= 0.67 and ratio > best["confidence"] / 100:
                best = {
                    "confidence": int(ratio * 70),
                    "evidence": " ".join(matched),
                }

        return best if best["confidence"] >= 45 else {}

    def _tokens(self, text: str) -> List[str]:
        return re.findall(r"[a-z0-9]+", str(text or "").lower())

    def _stem(self, token: str) -> str:
        token = token.lower()

        endings = [
            "ing",
            "tion",
            "sion",
            "ment",
            "ness",
            "ity",
            "ies",
            "ed",
            "es",
            "s",
        ]

        for ending in endings:
            if token.endswith(ending) and len(token) > len(ending) + 3:
                return token[: -len(ending)]

        return token


semantic_matcher = SemanticMatcher()