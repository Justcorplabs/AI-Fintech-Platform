import { Building2, Target } from "lucide-react";

export default function StructuredJobProfile({ review }) {
  if (!review) return null;

  return (
    <Section title="Structured Job Profile" icon={Target}>
      <div className="grid grid-cols-4 gap-4">
        <MiniCard title="Job Title" value={review.job_title || "Not detected"} />
        <MiniCard title="Organisation" value={review.organisation || "Not detected"} />
        <MiniCard title="Industry" value={review.industry || "General"} />
        <MiniCard title="Experience" value={review.experience_requirement || "Not specified"} />
      </div>

      <div className="mt-5 grid grid-cols-2 gap-5">
        <ProfilePanel title="Technical Requirements">
          <Tags items={review.technical_skills_required || []} positive />
        </ProfilePanel>

        <ProfilePanel title="Software / Tools">
          <Tags items={review.software_tools_required || []} positive />
        </ProfilePanel>

        <ProfilePanel title="Soft Skills">
          <Tags items={review.soft_skills_required || []} positive />
        </ProfilePanel>

        <ProfilePanel title="Degree Requirements">
          <Tags items={review.degree_requirements || []} positive />
        </ProfilePanel>
      </div>
    </Section>
  );
}

function Section({ title, icon: Icon, children }) {
  return (
    <div className="mb-6 rounded-3xl border border-slate-800 bg-slate-950 p-6">
      <div className="mb-5 flex items-center gap-3">
        <Icon className="text-sky-400" />
        <h2 className="text-lg font-semibold text-white">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function MiniCard({ title, value }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
      <p className="text-xs uppercase tracking-wider text-slate-500">{title}</p>
      <p className="mt-2 break-words font-semibold text-white">{value}</p>
    </div>
  );
}

function ProfilePanel({ title, children }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <div className="mb-3 flex items-center gap-2">
        <Building2 size={17} className="text-sky-400" />
        <h3 className="font-semibold text-white">{title}</h3>
      </div>
      {children}
    </div>
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