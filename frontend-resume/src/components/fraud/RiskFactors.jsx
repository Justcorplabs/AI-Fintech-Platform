const featureLabels = {
  TransactionAmt: "Transaction Amount",
  dist1: "Distance From Home",
  ProductCD: "Product Category",
  card6: "Card Type",
  D15: "Customer Activity Pattern",
  V70: "Behaviour Pattern Indicator",
  D4: "Customer Recency Pattern",
  D1: "Transaction Timing Pattern",
  card1: "Card Identity Signal",
  card2: "Card Issuer Signal",
  card5: "Card Metadata Signal",
  C13: "Transaction Frequency Signal",
  P_emaildomain: "Purchaser Email Domain",
};

function labelFeature(name) {
  return featureLabels[name] || name;
}

export default function RiskFactors({ factors }) {
  return (
    <div style={{ marginTop: 22 }}>
      <h3>Explainable AI Risk Factors</h3>

      <div style={{ display: "grid", gap: 12 }}>
        {factors?.map((factor, index) => (
          <div
            key={index}
            style={{
              padding: 14,
              borderRadius: 12,
              background: "#020617",
              border: "1px solid #1e293b",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <b>{labelFeature(factor.feature)}</b>
              <p style={{ color: "#94a3b8", margin: "4px 0 0" }}>
                Value: {factor.value}
              </p>
            </div>

            <div
              style={{
                color:
                  factor.direction === "increases_risk"
                    ? "#f97316"
                    : "#22c55e",
                fontWeight: "bold",
              }}
            >
              {factor.direction === "increases_risk" ? "↑" : "↓"}{" "}
              {factor.impact}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}