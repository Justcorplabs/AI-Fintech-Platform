import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import {
  ArrowLeft,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ShieldAlert,
  FileText,
  Bot,
  User,
  Activity,
  CircleDot,
  Printer,
} from "lucide-react";
import { fraudAPI } from "../services/api";

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

function riskColor(score) {
  if (score >= 0.8) return "text-red-400 border-red-500/30 bg-red-500/10";
  if (score >= 0.6) return "text-orange-400 border-orange-500/30 bg-orange-500/10";
  if (score >= 0.4) return "text-yellow-400 border-yellow-500/30 bg-yellow-500/10";
  return "text-emerald-400 border-emerald-500/30 bg-emerald-500/10";
}

function statusBadge(status) {
  if (status === "flagged") return "bg-red-500/10 text-red-400";
  if (status === "cleared") return "bg-emerald-500/10 text-emerald-400";
  if (status === "investigating") return "bg-yellow-500/10 text-yellow-400";
  return "bg-slate-700 text-slate-300";
}

export default function Investigation() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [transaction, setTransaction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [notes, setNotes] = useState("");

  async function loadTransaction() {
    try {
      setLoading(true);
      const res = await fraudAPI.getTransaction(id);
      setTransaction(res.data);
      setNotes(res.data.analyst_notes || "");
    } catch (err) {
      console.error(err);
      toast.error("Failed to load transaction.");
    } finally {
      setLoading(false);
    }
  }

  async function updateStatus(status) {
    try {
      setSaving(true);

      const res = await fraudAPI.reviewTransaction(id, {
        status,
        analyst_notes: notes,
        reviewed_by: "Joseph",
      });

      setTransaction(res.data);
      toast.success(`Transaction marked as ${status}.`);
    } catch (err) {
      console.error(err);
      toast.error("Failed to update transaction.");
    } finally {
      setSaving(false);
    }
  }

  function generateReport() {
    if (!transaction) return;

    const score = ((transaction.fraud_score || 0) * 100).toFixed(2);

    const shapRows = transaction.shap_values
      ?.map(
        (factor) => `
          <tr>
            <td>${labelFeature(factor.feature)}</td>
            <td>${factor.value}</td>
            <td>${factor.impact}</td>
            <td>${factor.direction}</td>
          </tr>
        `
      )
      .join("");

    const timelineRows = transaction.audit_events
      ?.map(
        (event) => `
          <tr>
            <td>${event.action}</td>
            <td>${event.actor || "System"}</td>
            <td>${event.status || "N/A"}</td>
            <td>${event.notes || ""}</td>
            <td>${event.created_at ? new Date(event.created_at).toLocaleString() : "N/A"}</td>
          </tr>
        `
      )
      .join("");

    const reportHtml = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>SentinelAI Investigation Report</title>
          <style>
            body {
              font-family: Arial, sans-serif;
              margin: 40px;
              color: #111827;
              line-height: 1.5;
            }

            .header {
              border-bottom: 3px solid #0ea5e9;
              padding-bottom: 16px;
              margin-bottom: 24px;
            }

            h1 {
              margin: 0;
              font-size: 28px;
              color: #020617;
            }

            h2 {
              margin-top: 30px;
              color: #0f172a;
              border-bottom: 1px solid #e5e7eb;
              padding-bottom: 8px;
            }

            .subtitle {
              color: #475569;
              margin-top: 6px;
            }

            .badge {
              display: inline-block;
              padding: 6px 12px;
              border-radius: 999px;
              font-weight: bold;
              background: #fee2e2;
              color: #991b1b;
            }

            .grid {
              display: grid;
              grid-template-columns: repeat(2, 1fr);
              gap: 12px;
              margin-top: 12px;
            }

            .box {
              border: 1px solid #e5e7eb;
              border-radius: 10px;
              padding: 12px;
              background: #f8fafc;
            }

            .label {
              font-size: 12px;
              color: #64748b;
              text-transform: uppercase;
              letter-spacing: .06em;
            }

            .value {
              margin-top: 4px;
              font-weight: bold;
              color: #111827;
            }

            table {
              width: 100%;
              border-collapse: collapse;
              margin-top: 12px;
              font-size: 13px;
            }

            th {
              background: #0f172a;
              color: white;
              text-align: left;
              padding: 10px;
            }

            td {
              border: 1px solid #e5e7eb;
              padding: 10px;
              vertical-align: top;
            }

            .notes {
              white-space: pre-wrap;
              border: 1px solid #e5e7eb;
              border-radius: 10px;
              padding: 14px;
              background: #f8fafc;
              min-height: 80px;
            }

            .footer {
              margin-top: 40px;
              font-size: 12px;
              color: #64748b;
              border-top: 1px solid #e5e7eb;
              padding-top: 14px;
            }

            @media print {
              button {
                display: none;
              }
            }
          </style>
        </head>

        <body>
          <div class="header">
            <h1>SentinelAI Investigation Report</h1>
            <p class="subtitle">Enterprise Fraud Intelligence Platform · Powered by JustCorp Labs</p>
            <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
          </div>

          <h2>Case Summary</h2>
          <p><strong>Transaction Reference:</strong> ${transaction.transaction_ref}</p>
          <p><strong>Status:</strong> <span class="badge">${transaction.status}</span></p>
          <p><strong>Fraud Score:</strong> ${score}%</p>
          <p><strong>Model Version:</strong> ${transaction.model_version || "N/A"}</p>

          <h2>Transaction Overview</h2>
          <div class="grid">
            <div class="box">
              <div class="label">Amount</div>
              <div class="value">${transaction.currency} ${transaction.amount}</div>
            </div>

            <div class="box">
              <div class="label">Merchant</div>
              <div class="value">${transaction.merchant_name || "N/A"}</div>
            </div>

            <div class="box">
              <div class="label">Category</div>
              <div class="value">${transaction.merchant_category || "N/A"}</div>
            </div>

            <div class="box">
              <div class="label">Card Type</div>
              <div class="value">${transaction.card_type || "N/A"}</div>
            </div>

            <div class="box">
              <div class="label">Transaction Hour</div>
              <div class="value">${transaction.transaction_hour ?? "N/A"}</div>
            </div>

            <div class="box">
              <div class="label">Distance From Home</div>
              <div class="value">${transaction.distance_from_home ?? 0} km</div>
            </div>

            <div class="box">
              <div class="label">Foreign Transaction</div>
              <div class="value">${transaction.is_foreign ? "Yes" : "No"}</div>
            </div>

            <div class="box">
              <div class="label">Created</div>
              <div class="value">${new Date(transaction.created_at).toLocaleString()}</div>
            </div>
          </div>

          <h2>Explainable AI Risk Factors</h2>
          <table>
            <thead>
              <tr>
                <th>Feature</th>
                <th>Value</th>
                <th>Impact</th>
                <th>Direction</th>
              </tr>
            </thead>
            <tbody>
              ${shapRows || ""}
            </tbody>
          </table>

          <h2>Analyst Notes</h2>
          <div class="notes">${transaction.analyst_notes || "No analyst notes recorded."}</div>

          <h2>Audit Timeline</h2>
          <table>
            <thead>
              <tr>
                <th>Action</th>
                <th>Actor</th>
                <th>Status</th>
                <th>Notes</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              ${timelineRows || ""}
            </tbody>
          </table>

          <div class="footer">
            This report was generated by SentinelAI. Fraud scores are AI-assisted risk indicators and should support, not replace, analyst judgment.
          </div>

          <script>
            window.onload = function() {
              window.print();
            };
          </script>
        </body>
      </html>
    `;

    const reportWindow = window.open("", "_blank");
    reportWindow.document.write(reportHtml);
    reportWindow.document.close();
  }

  useEffect(() => {
    loadTransaction();
  }, [id]);

  if (loading) {
    return <p className="text-slate-400">Loading investigation...</p>;
  }

  if (!transaction) {
    return <p className="text-red-400">Transaction not found.</p>;
  }

  const score = transaction.fraud_score || 0;
  const scorePercent = (score * 100).toFixed(2);

  return (
    <div>
      <div className="mb-6 flex flex-wrap gap-3">
        <button
          onClick={() => navigate("/transactions")}
          className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800"
        >
          <ArrowLeft size={18} />
          Back to Transactions
        </button>

        <button
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800"
        >
          <Activity size={18} />
          Back to Dashboard
        </button>

        <button
          onClick={generateReport}
          className="flex items-center gap-2 rounded-xl border border-sky-500/40 bg-sky-500/10 px-4 py-2 text-sm font-semibold text-sky-300 hover:bg-sky-500/20"
        >
          <Printer size={18} />
          Print / Save PDF Report
        </button>
      </div>

      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">
            Investigation Workspace
          </h1>
          <p className="mt-1 text-slate-400">
            Review fraud evidence, model explanations, analyst notes, and audit trail.
          </p>
        </div>

        <div className={`rounded-full border px-4 py-2 text-sm font-bold ${riskColor(score)}`}>
          Risk Score: {scorePercent}%
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <section className="col-span-2 rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">
                Transaction Overview
              </h2>
              <p className="text-sm text-slate-400">
                {transaction.transaction_ref}
              </p>
            </div>

            <span
              className={`rounded-full px-3 py-1 text-sm font-bold ${statusBadge(transaction.status)}`}
            >
              {transaction.status}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <InfoCard title="Amount" value={`${transaction.currency} ${transaction.amount}`} />
            <InfoCard title="Merchant" value={transaction.merchant_name || "N/A"} />
            <InfoCard title="Category" value={transaction.merchant_category || "N/A"} />
            <InfoCard title="Card Type" value={transaction.card_type || "N/A"} />
            <InfoCard title="Hour" value={transaction.transaction_hour ?? "N/A"} />
            <InfoCard title="Distance" value={`${transaction.distance_from_home ?? 0} km`} />
            <InfoCard title="Foreign" value={transaction.is_foreign ? "Yes" : "No"} />
            <InfoCard title="Model" value={transaction.model_version || "N/A"} />
            <InfoCard title="Created" value={new Date(transaction.created_at).toLocaleString()} />
          </div>
        </section>

        <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-lg font-semibold text-white">Analyst Decision</h2>
          <p className="mt-1 text-sm text-slate-400">
            Update the case outcome after review.
          </p>

          <div className="mt-5 grid gap-3">
            <button
              disabled={saving}
              onClick={() => updateStatus("cleared")}
              className="flex items-center justify-center gap-2 rounded-xl bg-emerald-500 px-4 py-3 font-bold text-white hover:bg-emerald-600 disabled:opacity-60"
            >
              <CheckCircle2 size={18} />
              Clear Transaction
            </button>

            <button
              disabled={saving}
              onClick={() => updateStatus("investigating")}
              className="flex items-center justify-center gap-2 rounded-xl bg-yellow-500 px-4 py-3 font-bold text-slate-950 hover:bg-yellow-400 disabled:opacity-60"
            >
              <Clock size={18} />
              Mark Investigating
            </button>

            <button
              disabled={saving}
              onClick={() => updateStatus("flagged")}
              className="flex items-center justify-center gap-2 rounded-xl bg-red-500 px-4 py-3 font-bold text-white hover:bg-red-600 disabled:opacity-60"
            >
              <ShieldAlert size={18} />
              Keep Flagged
            </button>
          </div>
        </section>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-6">
        <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-5 flex items-center gap-3">
            <AlertTriangle className="text-red-400" />
            <div>
              <h2 className="text-lg font-semibold text-white">
                Explainable AI Factors
              </h2>
              <p className="text-sm text-slate-400">
                SHAP-based model reasoning for this prediction.
              </p>
            </div>
          </div>

          <div className="grid gap-3">
            {transaction.shap_values?.map((factor, index) => (
              <div
                key={index}
                className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950 p-4"
              >
                <div>
                  <p className="font-semibold text-white">
                    {labelFeature(factor.feature)}
                  </p>
                  <p className="text-sm text-slate-400">
                    Value: {factor.value}
                  </p>
                </div>

                <div
                  className={
                    factor.direction === "increases_risk"
                      ? "font-bold text-orange-400"
                      : "font-bold text-emerald-400"
                  }
                >
                  {factor.direction === "increases_risk" ? "↑" : "↓"}{" "}
                  {factor.impact}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-5 flex items-center gap-3">
            <FileText className="text-sky-400" />
            <div>
              <h2 className="text-lg font-semibold text-white">Analyst Notes</h2>
              <p className="text-sm text-slate-400">
                Record investigation findings and decisions.
              </p>
            </div>
          </div>

          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={10}
            placeholder="Add analyst notes here..."
            className="w-full rounded-2xl border border-slate-800 bg-slate-950 p-4 text-slate-100 outline-none focus:border-sky-500"
          />

          <button
            disabled={saving}
            onClick={() => updateStatus(transaction.status)}
            className="mt-4 w-full rounded-xl bg-sky-500 px-4 py-3 font-bold text-white hover:bg-sky-600 disabled:opacity-60"
          >
            Save Notes
          </button>

          {transaction.reviewed_by && (
            <p className="mt-4 text-sm text-slate-400">
              Last reviewed by {transaction.reviewed_by}{" "}
              {transaction.reviewed_at
                ? `on ${new Date(transaction.reviewed_at).toLocaleString()}`
                : ""}
            </p>
          )}
        </section>
      </div>

      <section className="mt-6 rounded-3xl border border-slate-800 bg-slate-900 p-6">
        <div className="mb-6 flex items-center gap-3">
          <Clock className="text-sky-400" />
          <div>
            <h2 className="text-lg font-semibold text-white">
              Investigation Timeline
            </h2>
            <p className="text-sm text-slate-400">
              Full audit trail of transaction scoring and analyst actions.
            </p>
          </div>
        </div>

        {transaction.audit_events?.length === 0 ? (
          <p className="text-slate-400">No audit events recorded yet.</p>
        ) : (
          <div className="relative ml-3 space-y-6 border-l border-slate-700 pl-6">
            {transaction.audit_events?.map((event, index) => (
              <TimelineEvent key={event.id || index} event={event} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function InfoCard({ title, value }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
      <p className="text-xs uppercase tracking-wider text-slate-500">{title}</p>
      <p className="mt-2 font-semibold text-white">{value}</p>
    </div>
  );
}

function TimelineEvent({ event }) {
  const isAI = event.actor === "SentinelAI";
  const isSystem = event.actor === "System";

  return (
    <div className="relative">
      <div className="absolute -left-[34px] flex h-5 w-5 items-center justify-center rounded-full border border-sky-400 bg-slate-950">
        {isAI ? (
          <Bot size={12} className="text-sky-400" />
        ) : isSystem ? (
          <CircleDot size={12} className="text-emerald-400" />
        ) : (
          <User size={12} className="text-yellow-400" />
        )}
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="font-semibold text-white">{event.action}</h3>
            <p className="mt-1 text-sm text-slate-400">
              {event.actor || "System"} ·{" "}
              {event.created_at ? new Date(event.created_at).toLocaleString() : "N/A"}
            </p>
          </div>

          {event.status && (
            <span className={`rounded-full px-3 py-1 text-xs font-bold ${statusBadge(event.status)}`}>
              {event.status}
            </span>
          )}
        </div>

        {event.notes && (
          <p className="mt-3 rounded-xl bg-slate-900 p-3 text-sm text-slate-300">
            {event.notes}
          </p>
        )}
      </div>
    </div>
  );
}