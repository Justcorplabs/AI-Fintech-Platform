import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import {
  RefreshCw,
  Search,
  Eye,
  Filter,
  AlertTriangle,
  Clock,
  CheckCircle2,
  ShieldAlert,
  Square,
  CheckSquare,
} from "lucide-react";
import toast from "react-hot-toast";
import { fraudAPI } from "../services/api";

const PAGE_SIZE = 10;

export default function Transactions() {
  const navigate = useNavigate();

  const [transactions, setTransactions] = useState([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("review_queue");
  const [riskFilter, setRiskFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState([]);

  async function loadTransactions() {
    try {
      setLoading(true);
      const res = await fraudAPI.getTransactions({ limit: 200 });
      setTransactions(res.data);
    } catch (err) {
      console.error(err);
      toast.error("Failed to load transactions.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTransactions();
  }, []);

  useEffect(() => {
    setPage(1);
    setSelectedIds([]);
  }, [search, statusFilter, riskFilter]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();

    return transactions.filter((tx) => {
      const matchesSearch =
        tx.transaction_ref.toLowerCase().includes(q) ||
        tx.status.toLowerCase().includes(q) ||
        String(tx.amount).includes(q);

      const matchesStatus =
        statusFilter === "all"
          ? true
          : statusFilter === "review_queue"
          ? tx.status === "pending" || tx.status === "flagged"
          : tx.status === statusFilter;

      const score = tx.fraud_score || 0;

      const matchesRisk =
        riskFilter === "all"
          ? true
          : riskFilter === "low"
          ? score < 0.4
          : riskFilter === "medium"
          ? score >= 0.4 && score < 0.6
          : riskFilter === "high"
          ? score >= 0.6
          : true;

      return matchesSearch && matchesStatus && matchesRisk;
    });
  }, [transactions, search, statusFilter, riskFilter]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const pendingCount = transactions.filter((tx) => tx.status === "pending").length;
  const flaggedCount = transactions.filter((tx) => tx.status === "flagged").length;
  const investigatingCount = transactions.filter(
    (tx) => tx.status === "investigating"
  ).length;
  const clearedCount = transactions.filter((tx) => tx.status === "cleared").length;

  const allCurrentPageSelected =
    paginated.length > 0 && paginated.every((tx) => selectedIds.includes(tx.id));

  function toggleSelected(id) {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  }

  function toggleCurrentPageSelection() {
    if (allCurrentPageSelected) {
      setSelectedIds((prev) =>
        prev.filter((id) => !paginated.some((tx) => tx.id === id))
      );
    } else {
      setSelectedIds((prev) => {
        const next = [...prev];
        paginated.forEach((tx) => {
          if (!next.includes(tx.id)) next.push(tx.id);
        });
        return next;
      });
    }
  }

  async function bulkUpdate(status) {
    if (selectedIds.length === 0) {
      toast.error("Select at least one transaction.");
      return;
    }

    try {
      setBulkLoading(true);

      await Promise.all(
        selectedIds.map((id) =>
          fraudAPI.reviewTransaction(id, {
            status,
            analyst_notes: `Bulk action: marked as ${status}.`,
            reviewed_by: "Joseph",
          })
        )
      );

      toast.success(`${selectedIds.length} transaction(s) marked as ${status}.`);
      setSelectedIds([]);
      await loadTransactions();
    } catch (err) {
      console.error(err);
      toast.error("Bulk update failed.");
    } finally {
      setBulkLoading(false);
    }
  }

  return (
    <div>
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Review Queue</h1>
          <p className="mt-1 text-slate-400">
            Pending and flagged transactions requiring analyst attention.
          </p>
        </div>

        <button
          onClick={loadTransactions}
          className="flex items-center gap-2 rounded-xl bg-sky-500 px-4 py-3 font-bold text-white hover:bg-sky-600"
        >
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      <div className="mb-6 grid grid-cols-4 gap-5">
        <QueueCard
          title="Pending"
          value={pendingCount}
          icon={Clock}
          color="text-slate-300"
          bg="bg-slate-500/10"
        />
        <QueueCard
          title="Flagged"
          value={flaggedCount}
          icon={AlertTriangle}
          color="text-red-400"
          bg="bg-red-500/10"
        />
        <QueueCard
          title="Investigating"
          value={investigatingCount}
          icon={Filter}
          color="text-yellow-400"
          bg="bg-yellow-500/10"
        />
        <QueueCard
          title="Cleared"
          value={clearedCount}
          icon={CheckCircle2}
          color="text-emerald-400"
          bg="bg-emerald-500/10"
        />
      </div>

      <div className="mb-5 grid grid-cols-3 gap-4">
        <div className="flex items-center gap-3 rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3">
          <Search size={18} className="text-slate-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by reference, amount or status..."
            className="w-full bg-transparent text-slate-100 outline-none placeholder:text-slate-500"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-slate-100 outline-none"
        >
          <option value="review_queue">Review Queue: Pending + Flagged</option>
          <option value="pending">Pending Only</option>
          <option value="flagged">Flagged Only</option>
          <option value="investigating">Investigating</option>
          <option value="cleared">Cleared</option>
          <option value="all">All Transactions</option>
        </select>

        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          className="rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-slate-100 outline-none"
        >
          <option value="all">All Risk Levels</option>
          <option value="high">High Risk: 60%+</option>
          <option value="medium">Medium Risk: 40–59%</option>
          <option value="low">Low Risk: Below 40%</option>
        </select>
      </div>

      <div className="mb-5 flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-slate-800 bg-slate-900 p-4">
        <div>
          <p className="font-semibold text-white">
            Bulk Analyst Actions
          </p>
          <p className="text-sm text-slate-400">
            {selectedIds.length} transaction(s) selected
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            disabled={bulkLoading || selectedIds.length === 0}
            onClick={() => bulkUpdate("investigating")}
            className="flex items-center gap-2 rounded-xl bg-yellow-500 px-4 py-2 font-bold text-slate-950 hover:bg-yellow-400 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Clock size={17} />
            Mark Investigating
          </button>

          <button
            disabled={bulkLoading || selectedIds.length === 0}
            onClick={() => bulkUpdate("cleared")}
            className="flex items-center gap-2 rounded-xl bg-emerald-500 px-4 py-2 font-bold text-white hover:bg-emerald-600 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <CheckCircle2 size={17} />
            Clear Selected
          </button>

          <button
            disabled={bulkLoading || selectedIds.length === 0}
            onClick={() => bulkUpdate("flagged")}
            className="flex items-center gap-2 rounded-xl bg-red-500 px-4 py-2 font-bold text-white hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ShieldAlert size={17} />
            Keep Flagged
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900">
        {loading ? (
          <p className="p-6 text-slate-400">Loading transactions...</p>
        ) : filtered.length === 0 ? (
          <p className="p-6 text-slate-400">No transactions found for this view.</p>
        ) : (
          <>
            <table className="w-full border-collapse">
              <thead className="bg-slate-950 text-left text-sm text-slate-400">
                <tr>
                  <th className="p-4">
                    <button
                      onClick={toggleCurrentPageSelection}
                      className="text-slate-300 hover:text-white"
                    >
                      {allCurrentPageSelected ? (
                        <CheckSquare size={18} />
                      ) : (
                        <Square size={18} />
                      )}
                    </button>
                  </th>
                  <th className="p-4">Reference</th>
                  <th className="p-4">Amount</th>
                  <th className="p-4">Risk</th>
                  <th className="p-4">Fraud</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Created</th>
                  <th className="p-4">Action</th>
                </tr>
              </thead>

              <tbody>
                {paginated.map((tx) => {
                  const selected = selectedIds.includes(tx.id);

                  return (
                    <tr
                      key={tx.id}
                      className={`border-t border-slate-800 hover:bg-slate-800/40 ${
                        selected ? "bg-sky-500/5" : ""
                      }`}
                    >
                      <td className="p-4">
                        <button
                          onClick={() => toggleSelected(tx.id)}
                          className="text-slate-300 hover:text-white"
                        >
                          {selected ? (
                            <CheckSquare size={18} className="text-sky-400" />
                          ) : (
                            <Square size={18} />
                          )}
                        </button>
                      </td>

                      <td className="p-4 font-medium text-white">
                        {tx.transaction_ref}
                      </td>

                      <td className="p-4 text-slate-300">
                        {tx.currency} {tx.amount}
                      </td>

                      <td className="p-4">
                        <RiskBadge score={tx.fraud_score || 0} />
                      </td>

                      <td className="p-4">
                        {tx.is_fraud ? (
                          <span className="rounded-full bg-red-500/10 px-3 py-1 text-sm font-bold text-red-400">
                            Yes
                          </span>
                        ) : (
                          <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-sm font-bold text-emerald-400">
                            No
                          </span>
                        )}
                      </td>

                      <td className="p-4">
                        <StatusBadge status={tx.status} />
                      </td>

                      <td className="p-4 text-slate-400">
                        {tx.created_at
                          ? new Date(tx.created_at).toLocaleString()
                          : "N/A"}
                      </td>

                      <td className="p-4">
                        <button
                          onClick={() => navigate(`/investigation/${tx.id}`)}
                          className="flex items-center gap-2 rounded-xl border border-sky-500/40 bg-sky-500/10 px-3 py-2 text-sm font-bold text-sky-300 hover:bg-sky-500/20"
                        >
                          <Eye size={16} />
                          Review
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            <div className="flex items-center justify-between border-t border-slate-800 px-5 py-4">
              <p className="text-sm text-slate-400">
                Showing {paginated.length} of {filtered.length} transactions
              </p>

              <div className="flex items-center gap-2">
                <button
                  disabled={page === 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-bold text-slate-300 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Previous
                </button>

                <span className="text-sm text-slate-400">
                  Page {page} of {totalPages}
                </span>

                <button
                  disabled={page === totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-bold text-slate-300 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function QueueCard({ title, value, icon: Icon, color, bg }) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900 p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">{title}</p>
        <div className={`rounded-xl p-2 ${bg}`}>
          <Icon size={20} className={color} />
        </div>
      </div>
      <h2 className="mt-4 text-3xl font-semibold text-white">{value}</h2>
    </div>
  );
}

function RiskBadge({ score }) {
  const percent = (score * 100).toFixed(2);

  if (score >= 0.6) {
    return (
      <span className="rounded-full bg-red-500/10 px-3 py-1 text-sm font-bold text-red-400">
        {percent}% High
      </span>
    );
  }

  if (score >= 0.4) {
    return (
      <span className="rounded-full bg-yellow-500/10 px-3 py-1 text-sm font-bold text-yellow-400">
        {percent}% Medium
      </span>
    );
  }

  return (
    <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-sm font-bold text-emerald-400">
      {percent}% Low
    </span>
  );
}

function StatusBadge({ status }) {
  const styles = {
    flagged: "bg-red-500/10 text-red-400",
    cleared: "bg-emerald-500/10 text-emerald-400",
    investigating: "bg-yellow-500/10 text-yellow-400",
    pending: "bg-slate-700 text-slate-300",
  };

  return (
    <span
      className={`rounded-full px-3 py-1 text-sm font-bold ${
        styles[status] || styles.pending
      }`}
    >
      {status}
    </span>
  );
}
