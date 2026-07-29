import { useEffect, useMemo, useState } from "react";
import { fraudAPI } from "../services/api";
import {
  FileText,
  Download,
  ShieldAlert,
  CheckCircle2,
  Clock,
  BarChart3,
} from "lucide-react";

export default function Reports() {
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState(null);

  async function loadReports() {
    const [txRes, statsRes] = await Promise.all([
      fraudAPI.getTransactions({ limit: 500 }),
      fraudAPI.getStats(),
    ]);

    setTransactions(txRes.data);
    setStats(statsRes.data);
  }

  useEffect(() => {
    loadReports();
  }, []);

  const report = useMemo(() => {
    const highRisk = transactions.filter((tx) => (tx.fraud_score || 0) >= 0.6);
    const pending = transactions.filter((tx) => tx.status === "pending");
    const flagged = transactions.filter((tx) => tx.status === "flagged");
    const investigating = transactions.filter((tx) => tx.status === "investigating");
    const cleared = transactions.filter((tx) => tx.status === "cleared");

    const exposure = highRisk.reduce((sum, tx) => sum + Number(tx.amount || 0), 0);

    return { highRisk, pending, flagged, investigating, cleared, exposure };
  }, [transactions]);

  function printReport() {
    window.print();
  }

  return (
    <div>
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Reports</h1>
          <p className="mt-1 text-slate-400">
            Management reporting for fraud operations, exposure, and case workflow.
          </p>
        </div>

        <button
          onClick={printReport}
          className="flex items-center gap-2 rounded-xl bg-sky-500 px-4 py-3 font-bold text-white hover:bg-sky-600"
        >
          <Download size={18} />
          Print / Save Report
        </button>
      </div>

      <div className="grid grid-cols-4 gap-5">
        <ReportCard
          title="Total Transactions"
          value={stats?.total_transactions ?? 0}
          icon={BarChart3}
        />
        <ReportCard
          title="High Risk Cases"
          value={report.highRisk.length}
          icon={ShieldAlert}
          danger
        />
        <ReportCard
          title="Pending Review"
          value={report.pending.length}
          icon={Clock}
        />
        <ReportCard
          title="Cleared Cases"
          value={report.cleared.length}
          icon={CheckCircle2}
          success
        />
      </div>

      <section className="mt-6 rounded-3xl border border-slate-800 bg-slate-900 p-6">
        <div className="mb-5 flex items-center gap-3">
          <FileText className="text-sky-400" />
          <div>
            <h2 className="text-lg font-semibold text-white">
              Executive Fraud Summary
            </h2>
            <p className="text-sm text-slate-400">
              Generated from live SentinelAI transaction data.
            </p>
          </div>
        </div>

        <div className="space-y-4 text-slate-300">
          <p>
            SentinelAI has analysed <b>{transactions.length}</b> transactions in the current
            reporting window.
          </p>

          <p>
            The platform identified <b>{report.highRisk.length}</b> high-risk cases with
            total high-risk exposure of <b>USD {report.exposure.toFixed(2)}</b>.
          </p>

          <p>
            Current workflow status: <b>{report.pending.length}</b> pending,
            <b> {report.flagged.length}</b> flagged,
            <b> {report.investigating.length}</b> investigating, and
            <b> {report.cleared.length}</b> cleared.
          </p>

          <p>
            The active fraud model is <b>LightGBM Tuned v1</b> with a benchmark ROC-AUC of
            <b> 97.55%</b>, supported by SHAP explainability, analyst notes, audit trails,
            and printable investigation reports.
          </p>
        </div>
      </section>

      <section className="mt-6 rounded-3xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-lg font-semibold text-white">High Risk Case Register</h2>

        <div className="overflow-hidden rounded-2xl border border-slate-800">
          <table className="w-full border-collapse">
            <thead className="bg-slate-950 text-left text-sm text-slate-400">
              <tr>
                <th className="p-4">Reference</th>
                <th className="p-4">Amount</th>
                <th className="p-4">Risk Score</th>
                <th className="p-4">Status</th>
                <th className="p-4">Created</th>
              </tr>
            </thead>

            <tbody>
              {report.highRisk.map((tx) => (
                <tr key={tx.id} className="border-t border-slate-800">
                  <td className="p-4 font-medium text-white">{tx.transaction_ref}</td>
                  <td className="p-4 text-slate-300">
                    {tx.currency} {tx.amount}
                  </td>
                  <td className="p-4 text-red-400">
                    {((tx.fraud_score || 0) * 100).toFixed(2)}%
                  </td>
                  <td className="p-4 text-slate-300">{tx.status}</td>
                  <td className="p-4 text-slate-400">
                    {new Date(tx.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function ReportCard({ title, value, icon: Icon, danger, success }) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
      <div className="mb-5 flex items-center justify-between">
        <p className="text-sm text-slate-400">{title}</p>
        <Icon
          size={22}
          className={
            danger ? "text-red-400" : success ? "text-emerald-400" : "text-sky-400"
          }
        />
      </div>
      <h2 className="text-3xl font-semibold text-white">{value}</h2>
    </div>
  );
}