import json
import logging
import os
from typing import Any, Dict, List, Optional

import joblib
import pandas as pd


logger = logging.getLogger(__name__)


class FraudPredictor:
    def __init__(self):
        self.model = None
        self.calibrator = None
        self.explainer = None
        self.model_features = None
        self.model_defaults = None
        self.label_encoders = None
        self.metadata: Dict[str, Any] = {}

        self.model_version = "lightgbm-tuned-v2-calibrated"
        self.low_threshold = 0.40
        self.high_threshold = 0.60

        self.allow_demo_mode = self._read_boolean_env(
            "ALLOW_FRAUD_DEMO_MODE",
            default=False,
        )

        self._load_artifacts()

    @staticmethod
    def _read_boolean_env(name: str, default: bool = False) -> bool:
        value = os.getenv(name)

        if value is None:
            return default

        return value.strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
            "enabled",
        }

    def _project_root(self) -> str:
        return os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../../")
        )

    def _load_artifacts(self) -> None:
        root = self._project_root()

        registry_dir = os.path.join(root, "ml", "registry")
        models_dir = os.path.join(root, "ml", "models")

        self.model = joblib.load(
            os.path.join(
                registry_dir,
                "champion_lightgbm_model.pkl",
            )
        )

        self.calibrator = joblib.load(
            os.path.join(
                registry_dir,
                "champion_isotonic_calibrator.pkl",
            )
        )

        self.explainer = joblib.load(
            os.path.join(
                models_dir,
                "shap_explainer.pkl",
            )
        )

        self.model_features = joblib.load(
            os.path.join(
                models_dir,
                "model_features.pkl",
            )
        )

        self.model_defaults = joblib.load(
            os.path.join(
                models_dir,
                "model_defaults.pkl",
            )
        )

        metadata_path = os.path.join(
            registry_dir,
            "champion_model_card.json",
        )

        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as file:
                self.metadata = json.load(file)

            self.model_version = self.metadata.get(
                "model_version",
                self.model_version,
            )

        encoders_path = os.path.join(
            root,
            "data",
            "processed",
            "label_encoders.pkl",
        )

        if os.path.exists(encoders_path):
            self.label_encoders = joblib.load(encoders_path)

        logger.info(
            "Champion fraud model loaded successfully: %s",
            self.model_version,
        )

        logger.info(
            "Fraud demo mode enabled: %s",
            self.allow_demo_mode,
        )

    def _safe_encode(self, column: str, value: str) -> int:
        if self.label_encoders is None:
            return 0

        if column not in self.label_encoders:
            return 0

        encoder = self.label_encoders[column]
        value = str(value)

        if value in encoder.classes_:
            return int(encoder.transform([value])[0])

        if "Unknown" in encoder.classes_:
            return int(encoder.transform(["Unknown"])[0])

        return 0

    def _get_demo_profile(
        self,
        transaction_data: Dict[str, Any],
    ) -> Optional[str]:
        requested_profile = transaction_data.get("demo_profile")

        if not requested_profile:
            return None

        if not self.allow_demo_mode:
            logger.warning(
                "A fraud demo profile was supplied while demo mode is disabled."
            )
            return None

        profile = str(requested_profile).strip().lower()

        allowed_profiles = {"low", "medium", "high"}

        if profile not in allowed_profiles:
            logger.warning(
                "Unsupported fraud demo profile requested: %s",
                profile,
            )
            return None

        return profile

    def _apply_demo_profile(
        self,
        row: pd.Series,
        profile: str,
    ) -> pd.Series:
        if profile == "low":
            updates = {
                "TransactionAmt": 45,
                "dist1": 5,
                "ProductCD": 4,
                "card6": 1,
                "V70": 1,
                "C13": 1,
                "D15": 52,
            }

        elif profile == "medium":
            updates = {
                "TransactionAmt": 850,
                "dist1": 80,
                "ProductCD": 0,
                "card6": 2,
                "V70": 0,
                "C13": 2,
                "D15": 52,
                "D4": 26,
            }

        elif profile == "high":
            updates = {
                "TransactionAmt": 3500,
                "dist1": 500,
                "ProductCD": 0,
                "card6": 2,
                "V70": 0,
                "C13": 1,
                "D1": 0,
                "D4": 26,
                "D15": 52,
                "card5": 226,
                "P_emaildomain": 54,
                "TransactionDay": 127,
            }

        else:
            updates = {}

        for key, value in updates.items():
            if key in row.index:
                row[key] = value

        return row

    def _build_feature_row(
        self,
        data: Dict[str, Any],
        demo_profile: Optional[str] = None,
    ) -> pd.DataFrame:
        row = self.model_defaults.copy()

        if "TransactionAmt" in row.index:
            row["TransactionAmt"] = float(
                data.get("amount", 0) or 0
            )

        if "dist1" in row.index:
            row["dist1"] = float(
                data.get("distance_from_home", 0) or 0
            )

        if "card6" in row.index:
            row["card6"] = self._safe_encode(
                "card6",
                data.get("card_type") or "Unknown",
            )

        if "ProductCD" in row.index:
            row["ProductCD"] = self._safe_encode(
                "ProductCD",
                data.get("merchant_category") or "Unknown",
            )

        if demo_profile:
            row = self._apply_demo_profile(
                row,
                demo_profile,
            )

        features = pd.DataFrame([row])

        return features[self.model_features]

    def _get_risk_level(self, score: float) -> str:
        if score >= self.high_threshold:
            return "high"

        if score >= self.low_threshold:
            return "medium"

        return "low"

    def _calibrate_demo_score(
        self,
        score: float,
        profile: Optional[str],
    ) -> float:
        if not profile:
            return score

        if profile == "low":
            return min(score, 0.12)

        if profile == "medium":
            return max(
                min(score, 0.59),
                0.42,
            )

        if profile == "high":
            return max(score, 0.86)

        return score

    def _get_top_risk_factors(
        self,
        features: pd.DataFrame,
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        shap_values = self.explainer.shap_values(features)

        if isinstance(shap_values, list):
            values = shap_values[1][0]
        else:
            values = shap_values[0]

        result = pd.DataFrame(
            {
                "feature": features.columns,
                "value": features.iloc[0].values,
                "impact": values,
            }
        )

        result["abs_impact"] = result["impact"].abs()

        result = (
            result.sort_values(
                "abs_impact",
                ascending=False,
            )
            .head(top_n)
        )

        return [
            {
                "feature": row["feature"],
                "value": (
                    float(row["value"])
                    if isinstance(row["value"], (int, float))
                    else row["value"]
                ),
                "impact": round(
                    float(row["impact"]),
                    4,
                ),
                "direction": (
                    "increases_risk"
                    if row["impact"] > 0
                    else "reduces_risk"
                ),
            }
            for _, row in result.iterrows()
        ]

    def predict(
        self,
        transaction_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        demo_profile = self._get_demo_profile(
            transaction_data
        )

        features = self._build_feature_row(
            transaction_data,
            demo_profile=demo_profile,
        )

        calibrated_score = float(
            self.calibrator.predict_proba(features)[0, 1]
        )

        fraud_score = self._calibrate_demo_score(
            calibrated_score,
            demo_profile,
        )

        risk_level = self._get_risk_level(fraud_score)

        is_fraud = fraud_score >= self.high_threshold

        version = self.model_version

        if demo_profile:
            version = (
                f"{self.model_version}-demo-{demo_profile}"
            )

        return {
            "fraud_score": round(fraud_score, 4),
            "is_fraud": bool(is_fraud),
            "risk_level": risk_level,
            "top_risk_factors": self._get_top_risk_factors(
                features
            ),
            "model_version": version,
        }


fraud_predictor = FraudPredictor()