import { AlertTriangle, CheckCircle2 } from "lucide-react";

export default function ReviewPanels({ review }) {
  if (!review) return null;

  return (
    <div className="grid grid-cols-2 gap-6">
      <Panel title="Strengths" icon={CheckCircle2} positive>
        <List items={review.strengths || []} />
      </Panel>

      <Panel title="Improvements" icon={AlertTriangle}>
        <List items={review.improvements || []} />
      </Panel>

      <Panel title="Found Requirements" icon={CheckCircle2} positive>
        <Tags items={review.found_keywords || []} positive />
      </Panel>

      <Panel title="Missing Requirements" icon={AlertTriangle}>
        <Tags items={review.missing_keywords || []} />
      </Panel>
    </div>
  );
}

function Panel({ title, icon: Icon, children, positive }) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-950 p-5">
      <div className="mb-4 flex items-center gap-2">
        <Icon
          size={18}
          className={positive ? "text-emerald-400" : "text-yellow-400"}
        />
        <h3 className="font-semibold text-white">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function List({ items }) {
  if (!items?.length) {
    return <p className="text-sm text-slate-400">None detected</p>;
  }

  return (
    <ul className="space-y-2 text-sm text-slate-300">
      {items.map((item, index) => (
        <li key={index}>• {item}</li>
      ))}
    </ul>
  );
}

function Tags({ items, positive }) {
  if (!items?.length) {
    return <p className="text-sm text-slate-400">None detected</p>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span
          key={item}
          className={`rounded-full px-3 py-1 text-sm font-semibold ${
            positive
              ? "bg-emerald-500/10 text-emerald-400"
              : "bg-yellow-500/10 text-yellow-400"
          }`}
        >
          {item}
        </span>
      ))}
    </div>
  );
}