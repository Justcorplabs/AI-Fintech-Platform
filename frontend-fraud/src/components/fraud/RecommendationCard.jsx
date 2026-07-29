export default function RecommendationCard({ result }) {
  if (!result) return null;

  const color = riskColor(result.risk_level);

  return (
    <div
      style={{
        marginTop: 20,
        padding: 18,
        borderRadius: 14,
        background: result.is_fraud ? "#451a03" : "#052e16",
        border: `1px solid ${color}`,
      }}
    >
      <h3>{result.is_fraud ? "Investigate Transaction" : "Approve Transaction"}</h3>
      <p style={{ color: "#cbd5e1" }}>
        {result.is_fraud
          ? "The AI model detected suspicious behaviour requiring analyst review."
          : "The transaction shows low fraud probability and can be approved."}
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