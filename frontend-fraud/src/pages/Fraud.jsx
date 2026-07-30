import { useState } from "react";
import { fraudAPI } from "../services/fraudApi";

import TransactionForm from "../components/fraud/TransactionForm";
import FraudGauge from "../components/fraud/FraudGauge";
import RecommendationCard from "../components/fraud/RecommendationCard";
import RiskFactors from "../components/fraud/RiskFactors";

export default function Fraud() {
  const [form, setForm] = useState({
    transaction_ref: `REAL-TXN-${Date.now()}`,
    amount: 459.99,
    currency: "USD",
    merchant_name: "ABC Electronics",
    merchant_category: "W",
    card_type: "credit",
    transaction_hour: 14,
    distance_from_home: 35,
    is_foreign: false,
    demo_profile: "",
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  function updateField(e) {
    const { name, value, type, checked } = e.target;

    setForm({
      ...form,
      [name]: type === "checkbox" ? checked : type === "number" ? Number(value) : value,
    });
  }

  function loadPreset(type) {
    const presets = {
      low: {
        transaction_ref: `REAL-TXN-${Date.now()}`,
        amount: 45,
        currency: "USD",
        merchant_name: "Local Grocery Store",
        merchant_category: "W",
        card_type: "debit",
        transaction_hour: 10,
        distance_from_home: 5,
        is_foreign: false,
        demo_profile: "low",
      },
      medium: {
        transaction_ref: `REAL-TXN-${Date.now()}`,
        amount: 850,
        currency: "USD",
        merchant_name: "Online Electronics",
        merchant_category: "C",
        card_type: "credit",
        transaction_hour: 21,
        distance_from_home: 80,
        is_foreign: false,
        demo_profile: "medium",
      },
      high: {
        transaction_ref: `REAL-TXN-${Date.now()}`,
        amount: 3500,
        currency: "USD",
        merchant_name: "Foreign Digital Merchant",
        merchant_category: "C",
        card_type: "credit",
        transaction_hour: 3,
        distance_from_home: 500,
        is_foreign: true,
        demo_profile: "high",
      },
    };

    setForm(presets[type]);
    setResult(null);
  }

  async function submitTransaction(e) {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const res = await fraudAPI.predict(form);
      setResult(res.data);

      setForm((prev) => ({
        ...prev,
        transaction_ref: `REAL-TXN-${Date.now()}`,
      }));
    } catch (err) {
      alert("Prediction failed. Check backend terminal.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 1200, marginTop: 32 }}>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 36, marginBottom: 8 }}>Sentinel AI</h1>
        <p style={{ color: "#94a3b8", fontSize: 16 }}>
          Real-time explainable fraud detection powered by tuned LightGBM and SHAP.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.25fr", gap: 24 }}>
        <TransactionForm
          form={form}
          loading={loading}
          updateField={updateField}
          loadPreset={loadPreset}
          submitTransaction={submitTransaction}
        />

        <div
          style={{
            background: "#111827",
            padding: 24,
            borderRadius: 18,
            border: "1px solid #1f2937",
            minHeight: 480,
          }}
        >
          {!result ? (
            <div style={{ color: "#94a3b8" }}>
              <h2>AI Risk Intelligence</h2>
              <p>Submit a transaction to generate a real fraud score and SHAP explanation.</p>
            </div>
          ) : (
            <>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 20 }}>
                <div>
                  <h2 style={{ marginTop: 0 }}>Prediction Result</h2>
                  <p style={{ color: "#94a3b8" }}>{result.transaction_ref}</p>
                </div>

                <FraudGauge result={result} />
              </div>

              <RecommendationCard result={result} />
              <RiskFactors factors={result.top_risk_factors} />

              <div style={{ marginTop: 20, color: "#94a3b8" }}>
                <p>
                  <b>Model:</b> {result.model_version}
                </p>
                <p>
                  <b>Production benchmark:</b> ROC-AUC 97.55%
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
