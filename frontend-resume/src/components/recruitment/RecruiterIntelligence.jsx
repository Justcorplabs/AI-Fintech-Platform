import {
  AlertTriangle,
  BadgeCheck,
  BriefcaseBusiness,
  CircleDollarSign,
  GraduationCap,
  ShieldCheck,
  Target,
  TrendingUp,
} from "lucide-react";

export default function RecruiterIntelligence({ intelligence }) {
  if (!intelligence) return null;

  const risks = intelligence.hiring_risks || [];
  const strengths = intelligence.candidate_strengths || [];
  const roadmap = intelligence.learning_roadmap || [];
  const interview = intelligence.interview_readiness || {};
  const salary = intelligence.salary_intelligence || {};

  return (
    <section className="mb-6 rounded-3xl border border-sky-500/30 bg-sky-500/5 p-6">
      <div className="mb-5 flex items-center gap-3">
        <ShieldCheck className="text-sky-400" />
        <div>
          <h2 className="text-lg font-semibold text-white">
            Recruiter Intelligence
          </h2>
          <p className="text-sm text-slate-400">
            Human-style recruiter assessment based on CV evidence and job fit.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          title="Overall Rating"
          value={intelligence.overall_rating || "N/A"}
          icon={BadgeCheck}
        />
        <MetricCard
          title="Recruiter Score"
          value={`${Number(intelligence.recruiter_score || 0).toFixed(2)}%`}
          icon={TrendingUp}
        />
        <MetricCard
          title="Confidence"
          value={`${Number(intelligence.confidence || 0).toFixed(2)}%`}
          icon={Target}
        />
        <MetricCard
          title="Interview Readiness"
          value={interview.level || "N/A"}
          icon={BriefcaseBusiness}
        />
      </div>

      <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-950 p-5">
        <p className="text-xs uppercase tracking-wider text-slate-500">
          Hiring Recommendation
        </p>
        <h3 className="mt-2 text-xl font-bold text-emerald-400">
          {intelligence.hiring_recommendation || "Not available"}
        </h3>
        <p className="mt-3 leading-7 text-slate-300">
          {intelligence.recruiter_summary || ""}
        </p>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-6">
        <InfoPanel title="Candidate Strengths" icon={BadgeCheck} positive>
          <List items={strengths} />
        </InfoPanel>

        <InfoPanel title="Hiring Risks" icon={AlertTriangle}>
          {!risks.length ? (
            <p className="text-sm text-slate-400">No major risks detected.</p>
          ) : (
            <div className="space-y-3">
              {risks.map((risk, index) => (
                <div
                  key={index}
                  className="rounded-2xl border border-slate-800 bg-slate-900 p-4"
                >
                  <p className="font-semibold text-yellow-400">{risk.risk}</p>
                  <p className="mt-1 text-sm text-slate-400">
                    Level: {risk.level || "N/A"}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-slate-300">
                    {risk.mitigation}
                  </p>
                </div>
              ))}
            </div>
          )}
        </InfoPanel>

        <InfoPanel title="Interview Readiness" icon={BriefcaseBusiness} positive>
          <p className="mb-3 text-sm text-slate-300">
            Score: {Number(interview.score || 0).toFixed(2)}%
          </p>
          <h4 className="mb-2 font-semibold text-white">Preparation Focus</h4>
          <List items={interview.preparation_focus || []} />
        </InfoPanel>

        <InfoPanel title="Salary Intelligence" icon={CircleDollarSign} positive>
          <div className="space-y-3 text-sm text-slate-300">
            <p>
              <span className="font-semibold text-white">Range:</span>{" "}
              {salary.estimated_range || "Not available"}
            </p>
            <p>
              <span className="font-semibold text-white">Currency:</span>{" "}
              {salary.currency || "USD"}
            </p>
            <p className="leading-6">{salary.recommended_positioning}</p>
            <p className="text-slate-500">Confidence: {salary.confidence}</p>
          </div>
        </InfoPanel>
      </div>

      {roadmap.length > 0 && (
        <div className="mt-6 rounded-3xl border border-slate-800 bg-slate-950 p-5">
          <div className="mb-4 flex items-center gap-2">
            <GraduationCap size={18} className="text-sky-400" />
            <h3 className="font-semibold text-white">Learning Roadmap</h3>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {roadmap.map((item, index) => (
              <div
                key={index}
                className="rounded-2xl border border-slate-800 bg-slate-900 p-4"
              >
                <p className="text-xs uppercase tracking-wider text-slate-500">
                  {item.week || `Step ${index + 1}`}
                </p>
                <h4 className="mt-1 font-semibold text-white">{item.focus}</h4>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  {item.action}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function MetricCard({ title, value, icon: Icon }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
      <div className="mb-3 flex items-center gap-2">
        <Icon size={18} className="text-sky-400" />
        <p className="text-sm text-slate-400">{title}</p>
      </div>
      <h3 className="break-words text-2xl font-bold text-white">{value}</h3>
    </div>
  );
}

function InfoPanel({ title, icon: Icon, children, positive }) {
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