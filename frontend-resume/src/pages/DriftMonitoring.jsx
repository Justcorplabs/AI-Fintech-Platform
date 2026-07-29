import { useEffect, useMemo, useState } from "react";
import { fraudAPI } from "../services/api";
import {
  Activity,
  AlertTriangle,
  Brain,
  Database,
  Gauge,
  RefreshCw,
  TrendingUp,
} from "lucide-react";

export default function DriftMonitoring() {
  const [transactions, setTransactions] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(true);

  async function loadDriftData() {
    try {
      setLoading(true);

      const [txRes, metadataRes] = await Promise.all([
        fraudAPI.getTransactions({ limit: 500 }),
        fraudAPI.getModelMetadata(),
      ]);

      setTransactions(txRes.data);
      setMetadata(metadataRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDriftData();
  }, []);

  const drift = useMemo(() => {
    const total = transactions.length;
    const avgScore =
      total === 0
        ? 0
        : transactions.reduce((sum, tx) => sum + Number(tx.fraud_score || 0), 0) / total;

    const highRisk = transactions.filter((tx) => (tx.fraud_score || 0) >= 0.6).length;
    const mediumRisk = transactions.filter(
      (tx) => (tx.fraud_score || 0) >= 0.4 && (tx.fraud_score || 0) < 0.6
    ).length;

    const highRiskRatio = total === 0 ? 0 : highRisk / total;
    const mediumRiskRatio = total === 0 ? 0 : mediumRisk / total;

    let status = "stable";
    let recommendation = "No retraining required. Continue monitoring.";

    if (highRiskRatio >= 0.45 || avgScore >= 0.45) {
      status = "warning";
      recommendation =
        "Risk distribution is elevated. Review recent transactions and consider model validation.";
    }

    if (highRiskRatio >= 0.60 || avgScore >= 0.60) {
      status = "critical";
      recommendation =
        "Potential drift detected. Trigger model monitoring review and prepare retraining pipeline.";
    }

    return {
      total,
      avgScore,
      highRisk,
      mediumRisk,
      highRiskRatio,
      mediumRiskRatio,
      status,
      recommendation,
    };
  }, [transactions]);

  if (loading) return <p className="text-slate-400">Loading drift monitoring...</p>;

  return (
    <div>
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Model Drift Monitoring</h1>
          <p className="mt-1 text-slate-400">
            Monitor prediction behaviour, fraud-rate movement, and retraining readiness.
          </p>
        </div>

        <button
          onClick={loadDriftData}
          className="flex items-center gap-2 rounded-xl bg-sky-500 px-4 py-3 font-bold text-white hover:bg-sky-600"
        >
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-4 gap-5">
        <DriftCard
          title="Prediction Volume"
          value={drift.total}
          subtitle="Transactions monitored"
          icon={Database}
        />
        <DriftCard
          title="Average Risk Score"
          value={`${(drift.avgScore * 100).toFixed(2)}%`}
          subtitle="Mean model confidence"
          icon={Gauge}
        />
        <DriftCard
          title="High-Risk Ratio"
          value={`${(drift.highRiskRatio * 100).toFixed(2)}%`}
          subtitle={`${drift.highRisk} high-risk cases`}
          icon={AlertTriangle}
          danger={drift.highRiskRatio >= 0.45}
        />
        <DriftCard
          title="Champion Model"
          value={metadata?.model_version || "N/A"}
          subtitle={metadata?.calibration ? `Calibration: ${metadata.calibration}` : "Registry metadata"}
          icon={Brain}
          success
        />
      </div>

      <div className="mt-6 grid grid-cols-2 gap-6">
        <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-5 flex items-center gap-3">
            <Activity className="text-sky-400" />
            <div>
              <h2 className="text-lg font-semibold text-white">Drift Status</h2>
              <p className="text-sm text-slate-400">
                Heuristic monitoring based on recent production predictions.
              </p>
            </div>
          </div>

          <div
            className={`rounded-3xl border p-6 ${
              drift.status === "critical"
                ? "border-red-500/30 bg-red-500/10"
                : drift.status === "warning"
                ? "border-yellow-500/30 bg-yellow-500/10"
                : "border-emerald-500/30 bg-emerald-500/10"
            }`}
          >
            <p className="text-sm uppercase tracking-wider text-slate-400">Current Status</p>
            <h3
              className={`mt-2 text-3xl font-bold ${
                drift.status === "critical"
                  ? "text-red-400"
                  : drift.status === "warning"
                  ? "text-yellow-400"
                  : "text-emerald-400"
              }`}
            >
              {drift.status.toUpperCase()}
            </h3>
            <p className="mt-4 leading-7 text-slate-300">{drift.recommendation}</p>
          </div>
        </section>

        <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-5 flex items-center gap-3">
            <TrendingUp className="text-yellow-400" />
            <div>
              <h2 className="text-lg font-semibold text-white">Monitoring Signals</h2>
              <p className="text-sm text-slate-400">
                Operational indicators used to decide whether validation is needed.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <SignalRow label="Medium-Risk Ratio" value={`${(drift.mediumRiskRatio * 100).toFixed(2)}%`} />
            <SignalRow label="High-Risk Cases" value={drift.highRisk} />
            <SignalRow label="Medium-Risk Cases" value={drift.mediumRisk} />
            <SignalRow label="Model ROC-AUC" value={`${((metadata?.roc_auc || 0) * 100).toFixed(2)}%`} />
            <SignalRow label="Brier Score" value={metadata?.brier_score ?? "N/A"} />
            <SignalRow label="Retraining Trigger" value="High-risk ratio ≥ 60%" />
          </div>
        </section>
      </div>

      <section className="mt-6 rounded-3xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-lg font-semibold text-white">Model Monitoring Notes</h2>
        <p className="mt-3 leading-7 text-slate-400">
          This page currently performs operational drift monitoring using live prediction
          behaviour. A future production version should compare incoming feature distributions
          against the training baseline using PSI, KS tests, feature-level drift charts, and
          concept-drift validation on confirmed fraud outcomes.
        </p>
      </section>
    </div>
  );
}

function DriftCard({ title, value, subtitle, icon: Icon, danger, success }) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
      <div className="mb-5 flex items-center justify-between">
        <p className="text-sm text-slate-400">{title}</p>
        <Icon
          size={22}
          className={danger ? "text-red-400" : success ? "text-emerald-400" : "text-sky-400"}
        />
      </div>
      <h2 className="break-words text-3xl font-semibold text-white">{value}</h2>
      <p className="mt-2 text-sm text-slate-500">{subtitle}</p>
    </div>
  );
}

function SignalRow({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-slate-800 bg-slate-950 px-4 py-3">
      <span className="text-sm text-slate-400">{label}</span>
      <span className="text-right text-sm font-semibold text-white">{value}</span>
    </div>
  );
}