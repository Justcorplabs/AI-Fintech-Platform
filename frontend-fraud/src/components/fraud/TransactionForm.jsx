export default function TransactionForm({
  form,
  loading,
  updateField,
  loadPreset,
  submitTransaction,
}) {
  return (
    <form
      onSubmit={submitTransaction}
      style={{
        background: "#111827",
        padding: 24,
        borderRadius: 18,
        border: "1px solid #1f2937",
        display: "grid",
        gap: 12,
      }}
    >
      <h2 style={{ marginTop: 0 }}>Score Transaction</h2>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button type="button" onClick={() => loadPreset("low")} style={presetButton("#22c55e", "#052e16")}>
          Low Risk Demo
        </button>

        <button type="button" onClick={() => loadPreset("medium")} style={presetButton("#eab308", "#422006")}>
          Medium Risk Demo
        </button>

        <button type="button" onClick={() => loadPreset("high")} style={presetButton("#ef4444", "#450a0a")}>
          High Risk Demo
        </button>
      </div>

      {[
        "transaction_ref",
        "amount",
        "currency",
        "merchant_name",
        "merchant_category",
        "card_type",
        "transaction_hour",
        "distance_from_home",
      ].map((field) => (
        <input
          key={field}
          name={field}
          value={form[field]}
          onChange={updateField}
          type={["amount", "transaction_hour", "distance_from_home"].includes(field) ? "number" : "text"}
          placeholder={field}
          style={{
            padding: 13,
            borderRadius: 10,
            border: "1px solid #334155",
            background: "#020617",
            color: "white",
          }}
        />
      ))}

      <label style={{ color: "#cbd5e1" }}>
        <input
          type="checkbox"
          name="is_foreign"
          checked={form.is_foreign}
          onChange={updateField}
        />{" "}
        Foreign transaction
      </label>

      <button
        type="submit"
        style={{
          padding: 14,
          borderRadius: 12,
          cursor: "pointer",
          fontWeight: "bold",
          background: "#38bdf8",
          border: "none",
        }}
      >
        {loading ? "Scoring..." : "Run AI Fraud Check"}
      </button>

      <p style={{ color: "#94a3b8", fontSize: 13, lineHeight: 1.5 }}>
        Demo note: presets use realistic hidden feature profiles for product demonstration.
      </p>
    </form>
  );
}

function presetButton(border, background) {
  return {
    padding: "8px 12px",
    borderRadius: 8,
    border: `1px solid ${border}`,
    background,
    color: "white",
    cursor: "pointer",
    fontWeight: "bold",
  };
}