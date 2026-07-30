import { useEffect, useState } from "react";
import { fraudAPI } from "../services/fraudApi";
import {
  Activity,
  Brain,
  Database,
  FileCheck2,
  Gauge,
  ShieldCheck,
  Wifi,
  GitBranch,
} from "lucide-react";
import toast from "react-hot-toast";

export default function Settings() {
  const [stats, setStats] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(true);

  async function loadSettings() {
    try {
      setLoading(true);

      const [statsRes, metadataRes] = await Promise.all([
        fraudAPI.getStats(),
        fraudAPI.getModelMetadata(),
      ]);

      setStats(statsRes.data);
      setMetadata(metadataRes.data);
    } catch (err) {
      console.error(err);
      toast.error("Failed to load model governance settings.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSettings();
  }, []);

  if (loading) {
    return <p className="text-slate-400">Loading settings...</p>;
  }

  const thresholds = metadata?.recommended_threshold_policy || {};

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white">
          Settings & Model Governance
        </h1>
        <p className="mt-1 text-slate-400">
          Live model governance, monitoring status, compliance controls, and production readiness.
        </p>
      </div>

      <div className="grid grid-cols-4 gap-5">
        <GovernanceCard
          title="Champion Model"
          value={metadata?.champion_model || "N/A"}
          subtitle={metadata?.model_version || "No model version found"}
          icon={Brain}
          success
        />

        <GovernanceCard
          title="ROC-AUC"
          value={`${((metadata?.roc_auc || 0) * 100).toFixed(2)}%`}
          subtitle="Champion validation benchmark"
          icon={Gauge}
          success
        />

        <GovernanceCard
          title="Calibration"
          value={metadata?.calibration || "N/A"}
          subtitle={`Brier score: ${metadata?.brier_score ?? "N/A"}`}
          icon={Activity}
          success
        />

        <GovernanceCard
          title="Registry"
          value={metadata?.registry_available ? "Available" : "Missing"}
          subtitle="Model registry connection"
          icon={GitBranch}
          success={metadata?.registry_available}
        />
      </div>

      <div className="mt-6 grid grid-cols-2 gap-6">
        <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-5 flex items-center gap-3">
            <ShieldCheck className="text-emerald-400" />
            <div>
              <h2 className="text-lg font-semibold text-white">
                Champion Model Governance
              </h2>
              <p className="text-sm text-slate-400">
                Live model card loaded from the backend registry.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <SettingRow label="Model Name" value={metadata?.champion_model || "N/A"} />
            <SettingRow label="Model Version" value={metadata?.model_version || "N/A"} />
            <SettingRow label="Status" value={metadata?.status || "N/A"} />
            <SettingRow label="Calibration" value={metadata?.calibration || "N/A"} />
            <SettingRow label="PR-AUC" value={`${((metadata?.pr_auc || 0) * 100).toFixed(2)}%`} />
            <SettingRow label="Brier Score" value={metadata?.brier_score ?? "N/A"} />
          </div>
        </section>

        <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-5 flex items-center gap-3">
            <Gauge className="text-yellow-400" />
            <div>
              <h2 className="text-lg font-semibold text-white">
                Risk Threshold Policy
              </h2>
              <p className="text-sm text-slate-400">
                Operational routing policy used by SentinelAI.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <SettingRow label="Low Risk" value={thresholds.low_risk || "score < 0.40"} />
            <SettingRow
              label="Manual Review"
              value={thresholds.manual_review || "0.40 <= score < 0.60"}
            />
            <SettingRow label="High Alert" value={thresholds.high_alert || "score >= 0.60"} />
            <SettingRow label="Decision Mode" value="Risk-band routing" />
            <SettingRow label="High-Risk Action" value="Flag transaction" />
            <SettingRow label="Medium-Risk Action" value="Send to review queue" />
          </div>
        </section>

        <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-5 flex items-center gap-3">
            <FileCheck2 className="text-sky-400" />
            <div>
              <h2 className="text-lg font-semibold text-white">
                Compliance Readiness
              </h2>
              <p className="text-sm text-slate-400">
                Controls required for analyst accountability and audit review.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <SettingRow label="Audit Trail" value="Enabled" />
            <SettingRow label="Analyst Notes" value="Enabled" />
            <SettingRow label="Case Review Workflow" value="Enabled" />
            <SettingRow label="PDF Investigation Reports" value="Enabled" />
            <SettingRow label="Bulk Analyst Actions" value="Enabled" />
            <SettingRow label="SHAP Explainability" value="Enabled" />
          </div>
        </section>

        <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-5 flex items-center gap-3">
            <Database className="text-sky-400" />
            <div>
              <h2 className="text-lg font-semibold text-white">
                Operational Status
              </h2>
              <p className="text-sm text-slate-400">
                Live platform health and workflow counts.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <SettingRow label="Database" value="PostgreSQL" />
            <SettingRow label="Live Monitoring" value="WebSocket enabled" />
            <SettingRow label="Total Transactions" value={stats?.total_transactions ?? 0} />
            <SettingRow label="Flagged Cases" value={stats?.flagged_count ?? 0} />
            <SettingRow label="Cleared Cases" value={stats?.cleared_count ?? 0} />
            <SettingRow label="Fraud Rate" value={`${stats?.fraud_rate ?? 0}%`} />
          </div>
        </section>
      </div>

      <section className="mt-6 rounded-3xl border border-slate-800 bg-slate-900 p-6">
        <div className="mb-4 flex items-center gap-3">
          <Wifi className="text-emerald-400" />
          <div>
            <h2 className="text-lg font-semibold text-white">
              Champion Selection Reason
            </h2>
            <p className="text-sm text-slate-400">
              Why this model is currently deployed in production.
            </p>
          </div>
        </div>

        <p className="leading-7 text-slate-300">
          {metadata?.champion_reason ||
            "Champion reason not available from model metadata."}
        </p>

        <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-950 p-4">
          <p className="text-sm font-semibold text-white">Registered Challengers</p>
          <p className="mt-2 text-sm text-slate-400">
            {(metadata?.challengers || []).join(", ") || "No challengers registered"}
          </p>
        </div>
      </section>
    </div>
  );
}

function GovernanceCard({ title, value, subtitle, icon: Icon, success }) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
      <div className="mb-5 flex items-center justify-between">
        <p className="text-sm text-slate-400">{title}</p>
        <Icon size={22} className={success ? "text-emerald-400" : "text-sky-400"} />
      </div>
      <h2 className="break-words text-2xl font-semibold text-white">{value}</h2>
      <p className="mt-2 text-sm text-slate-500">{subtitle}</p>
    </div>
  );
}

function SettingRow({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-slate-800 bg-slate-950 px-4 py-3">
      <span className="text-sm text-slate-400">{label}</span>
      <span className="text-right text-sm font-semibold text-white">{value}</span>
    </div>
  );
}
