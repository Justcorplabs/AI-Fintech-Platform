"""
Versioned recruitment scoring audit snapshots.

The service stores scoring evidence in the existing
CVApplication.parsed_data JSONB document. It deliberately
uses JSON-serialisable values so no database migration is
required for this audit stage.
"""

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping


SCORING_POLICY_VERSION = "recruitment-score-v2.0"

JOB_CONTEXT_WEIGHTS = {
    "job_match": 0.35,
    "experience": 0.25,
    "education": 0.15,
    "achievements": 0.15,
    "formatting": 0.05,
    "contact": 0.05,
}

PROFILE_WEIGHTS = {
    "skills": 0.25,
    "experience": 0.30,
    "education": 0.20,
    "achievements": 0.15,
    "formatting": 0.05,
    "contact": 0.05,
}

JOB_CONTEXT_THRESHOLDS = {
    "highly_recommended": 88.0,
    "recommended": 78.0,
    "consider_after_improvements": 68.0,
    "potential_with_gaps": 55.0,
}

PROFILE_THRESHOLDS = {
    "strong_profile": 75.0,
    "promising_profile": 60.0,
}


class ScoringAuditService:
    """
    Build and safely update versioned score-audit data.

    The scoring calculation remains owned by
    CandidateIntelligence. This service records the inputs,
    policy weights, output, and later human decision without
    recalculating the candidate score.
    """

    def build_snapshot(
        self,
        *,
        review: Mapping[str, Any] | None,
        intelligence: Mapping[str, Any] | None,
        matched_requirements: list[Any] | None = None,
        missing_requirements: list[Any] | None = None,
        calculated_at: datetime | None = None,
    ) -> dict[str, Any]:
        review_data = dict(
            review or {}
        )
        intelligence_data = dict(
            intelligence or {}
        )

        scoring_context_value = (
            intelligence_data.get(
                "scoring_context",
                {},
            )
            or review_data.get(
                "scoring_context",
                {},
            )
            or {}
        )

        scoring_context = (
            dict(scoring_context_value)
            if isinstance(
                scoring_context_value,
                Mapping,
            )
            else {}
        )

        job_context_available = bool(
            scoring_context.get(
                "job_context_available",
                True,
            )
        )

        components = self._components(
            review=review_data,
            intelligence=intelligence_data,
            job_context_available=(
                job_context_available
            ),
        )

        weights = dict(
            JOB_CONTEXT_WEIGHTS
            if job_context_available
            else PROFILE_WEIGHTS
        )

        final_score = self._clamp(
            intelligence_data.get(
                "recruiter_score",
                0,
            )
        )

        weighted_component_total = round(
            sum(
                components.get(
                    name,
                    0.0,
                )
                * weight
                for name, weight
                in weights.items()
            ),
            2,
        )

        aggregate_ats_used = bool(
            scoring_context.get(
                "aggregate_ats_used_as_score_input",
                False,
            )
        )

        timestamp = (
            calculated_at
            or datetime.now(
                timezone.utc
            )
        )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )

        timestamp = timestamp.astimezone(
            timezone.utc
        )

        recommendation = str(
            intelligence_data.get(
                "hiring_recommendation"
            )
            or "Review required"
        ).strip()

        thresholds = dict(
            JOB_CONTEXT_THRESHOLDS
            if job_context_available
            else PROFILE_THRESHOLDS
        )

        return {
            "policy_version": (
                SCORING_POLICY_VERSION
            ),
            "calculated_at": (
                timestamp.isoformat()
            ),
            "job_context_available": (
                job_context_available
            ),
            "components": components,
            "weights": weights,
            "reference_scores": {
                "ats_score": self._clamp(
                    review_data.get(
                        "ats_score",
                        0,
                    )
                ),
            },
            "adjustments": {
                "evidence_bonus": 0.0,
                "penalty": 0.0,
                "aggregate_ats_used_as_score_input": (
                    aggregate_ats_used
                ),
            },
            "calculation": {
                "weighted_component_total": (
                    weighted_component_total
                ),
                "final_score_matches_weighted_total": (
                    abs(
                        final_score
                        - weighted_component_total
                    )
                    <= 0.01
                ),
            },
            "matched_requirements": (
                self._normalise_requirements(
                    matched_requirements
                )
            ),
            "missing_requirements": (
                self._normalise_requirements(
                    missing_requirements
                )
            ),
            "final_score": final_score,
            "recommendation": recommendation,
            "thresholds": thresholds,
            "human_review": {
                "reviewed": False,
                "reviewed_by_user_id": None,
                "reviewed_by_email": None,
                "reviewed_at": None,
                "decision": None,
                "notes": None,
            },
        }

    def extract_snapshot(
        self,
        parsed_data: Mapping[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(
            parsed_data,
            Mapping,
        ):
            return None

        snapshot = parsed_data.get(
            "scoring_audit"
        )

        if not isinstance(
            snapshot,
            Mapping,
        ):
            return None

        return deepcopy(
            dict(snapshot)
        )

    def record_human_review(
        self,
        *,
        parsed_data: Mapping[str, Any] | None,
        reviewer_id: Any = None,
        reviewer_email: Any = None,
        decision: str,
        notes: str | None = None,
        reviewed_at: datetime | None = None,
    ) -> dict[str, Any]:
        updated_data = deepcopy(
            dict(parsed_data or {})
        )

        snapshot = self.extract_snapshot(
            updated_data
        )

        if snapshot is None:
            return updated_data

        timestamp = (
            reviewed_at
            or datetime.now(
                timezone.utc
            )
        )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )

        timestamp = timestamp.astimezone(
            timezone.utc
        )

        reviewer_id_value = (
            str(reviewer_id)
            if reviewer_id is not None
            else None
        )

        reviewer_email_value = (
            str(reviewer_email).strip().lower()
            if reviewer_email is not None
            else None
        )

        notes_value = (
            str(notes).strip()[:4000]
            if notes
            else None
        )

        snapshot["human_review"] = {
            "reviewed": True,
            "reviewed_by_user_id": (
                reviewer_id_value
            ),
            "reviewed_by_email": (
                reviewer_email_value
            ),
            "reviewed_at": (
                timestamp.isoformat()
            ),
            "decision": (
                str(decision).strip().lower()
            ),
            "notes": notes_value,
        }

        updated_data["scoring_audit"] = (
            snapshot
        )

        return updated_data

    def _components(
        self,
        *,
        review: Mapping[str, Any],
        intelligence: Mapping[str, Any],
        job_context_available: bool,
    ) -> dict[str, float]:
        recorded = intelligence.get(
            "score_components",
            {},
        )

        if isinstance(
            recorded,
            Mapping,
        ):
            required_keys = (
                JOB_CONTEXT_WEIGHTS.keys()
                if job_context_available
                else PROFILE_WEIGHTS.keys()
            )

            if all(
                key in recorded
                for key in required_keys
            ):
                return {
                    key: self._clamp(
                        recorded.get(key)
                    )
                    for key in required_keys
                }

        if job_context_available:
            return {
                "job_match": self._clamp(
                    review.get(
                        "job_match_score",
                        0,
                    )
                ),
                "experience": self._clamp(
                    review.get(
                        "experience_score",
                        0,
                    )
                ),
                "education": self._clamp(
                    review.get(
                        "education_score",
                        0,
                    )
                ),
                "achievements": self._clamp(
                    review.get(
                        "achievement_score",
                        0,
                    )
                ),
                "formatting": self._clamp(
                    review.get(
                        "formatting_score",
                        0,
                    )
                ),
                "contact": self._clamp(
                    review.get(
                        "contact_score",
                        0,
                    )
                ),
            }

        return {
            "skills": self._clamp(
                review.get(
                    "skills_score",
                    0,
                )
            ),
            "experience": self._clamp(
                review.get(
                    "experience_score",
                    0,
                )
            ),
            "education": self._clamp(
                review.get(
                    "education_score",
                    0,
                )
            ),
            "achievements": self._clamp(
                review.get(
                    "achievement_score",
                    0,
                )
            ),
            "formatting": self._clamp(
                review.get(
                    "formatting_score",
                    0,
                )
            ),
            "contact": self._clamp(
                review.get(
                    "contact_score",
                    0,
                )
            ),
        }

    def _normalise_requirements(
        self,
        requirements: list[Any] | None,
    ) -> list[str]:
        output: list[str] = []
        seen: set[str] = set()

        for requirement in (
            requirements or []
        ):
            cleaned = " ".join(
                str(requirement).split()
            )

            if not cleaned:
                continue

            key = cleaned.casefold()

            if key in seen:
                continue

            seen.add(key)
            output.append(
                cleaned
            )

        return output

    def _clamp(
        self,
        value: Any,
    ) -> float:
        try:
            numeric = float(
                value or 0
            )

        except (
            TypeError,
            ValueError,
        ):
            numeric = 0.0

        return round(
            min(
                100.0,
                max(0.0, numeric),
            ),
            2,
        )


scoring_audit_service = ScoringAuditService()