export default function FraudGauge({ result }) {
  if (!result) return null;

  const score = result.fraud_score * 100;
  const color = riskColor(result.risk_level);

  return (
    <div style={{ textAlign: "center" }}>
      <div
        style={{
          width: 150,
          height: 150,
          borderRadius: "50%",
          border: `12px solid ${color}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 28,
          fontWeight: "bold",
        }}
      >
        {score.toFixed(2)}%
      </div>

      <p style={{ color, fontWeight: "bold", marginTop: 10 }}>
        {result.risk_level.toUpperCase()} RISK
      </p>
    </div>
  );
}

function riskColor(level) {
  if (level === "critical") return "#ef4444";
  if (level === "high") return "#f97316";
  if (level === "medium") return "#eab308";
  return "#22c55e";
}