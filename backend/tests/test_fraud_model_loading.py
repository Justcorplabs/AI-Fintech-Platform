import ast
import importlib
import json
from pathlib import Path

import joblib
import pandas as pd
import pytest

from app.services.fraud.predictor import (
    FraudPredictor,
    ModelUnavailableError,
)


PROJECT_ROOT = (
    Path(__file__).resolve().parents[2]
)


def test_predictor_constructor_does_not_load_artifacts(
    monkeypatch,
):
    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "joblib.load must not run during construction."
        )

    monkeypatch.setattr(
        joblib,
        "load",
        fail_if_called,
    )

    predictor = FraudPredictor()

    assert predictor.is_loaded is False


def test_importing_application_does_not_require_model_artifacts():
    module = importlib.import_module(
        "app.main"
    )

    assert module.app is not None


def test_prediction_reports_missing_artifacts(
    tmp_path,
    monkeypatch,
):
    predictor = FraudPredictor()

    monkeypatch.setattr(
        predictor,
        "_project_root",
        lambda: tmp_path,
    )

    with pytest.raises(
        ModelUnavailableError,
        match="unavailable",
    ):
        predictor.predict(
            {
                "amount": 100,
            }
        )


def test_successful_artifact_bundle_is_loaded_once(
    tmp_path,
    monkeypatch,
):
    registry_dir = (
        tmp_path
        / "ml"
        / "registry"
    )
    models_dir = (
        tmp_path
        / "ml"
        / "models"
    )

    registry_dir.mkdir(parents=True)
    models_dir.mkdir(parents=True)

    artifact_paths = {
        registry_dir / "champion_lightgbm_model.pkl": object(),
        registry_dir / "champion_isotonic_calibrator.pkl": object(),
        models_dir / "shap_explainer.pkl": object(),
        models_dir / "model_features.pkl": ["feature_one"],
        models_dir / "model_defaults.pkl": pd.Series(
            {"feature_one": 0.0}
        ),
    }

    for path in artifact_paths:
        path.write_bytes(b"test-artifact")

    (
        registry_dir
        / "champion_model_card.json"
    ).write_text(
        json.dumps(
            {
                "model_version": "test-model-v1",
            }
        ),
        encoding="utf-8",
    )

    load_calls = []

    def fake_load(path):
        resolved_path = Path(path)
        load_calls.append(resolved_path.name)
        return artifact_paths[resolved_path]

    monkeypatch.setattr(
        joblib,
        "load",
        fake_load,
    )

    predictor = FraudPredictor()

    monkeypatch.setattr(
        predictor,
        "_project_root",
        lambda: tmp_path,
    )

    predictor._ensure_artifacts_loaded()
    predictor._ensure_artifacts_loaded()

    assert predictor.is_loaded is True
    assert predictor.model_version == "test-model-v1"
    assert len(load_calls) == 5


def test_fraud_route_maps_missing_model_to_service_unavailable():
    source = (
        PROJECT_ROOT
        / "backend"
        / "app"
        / "api"
        / "routes"
        / "fraud.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "except ModelUnavailableError as exc:" in source
    assert "status.HTTP_503_SERVICE_UNAVAILABLE" in source
    tree = ast.parse(source)

    string_constants = {
        node.value
        for node in ast.walk(tree)
        if isinstance(
            node,
            ast.Constant,
        )
        and isinstance(
            node.value,
            str,
        )
    }

    assert (
        "Fraud prediction model is "
        "temporarily unavailable."
        in string_constants
    )
