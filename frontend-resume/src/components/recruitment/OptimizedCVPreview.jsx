import { FileText } from "lucide-react";

export default function OptimizedCVPreview({ builtResume }) {
  if (!builtResume) return null;

  const header = builtResume.header || {};

  return (
    <section className="mb-6 rounded-3xl border border-emerald-500/30 bg-emerald-500/5 p-6">
      <div className="mb-5 flex items-center gap-3">
        <FileText className="text-emerald-400" />
        <div>
          <h2 className="text-lg font-semibold text-white">
            Optimized CV Preview
          </h2>
          <p className="text-sm text-slate-400">
            Preview of the AI-generated recruiter-ready CV.
          </p>
        </div>
      </div>

      <div className="rounded-3xl border border-slate-800 bg-slate-950 p-6">

        <h1 className="text-3xl font-bold text-white">
          {header.name || "Candidate"}
        </h1>

        <p className="mt-2 text-slate-300">
          {header.email}
        </p>

        <p className="text-slate-300">
          {header.phone}
        </p>

        <p className="mt-1 text-slate-400">
          Target Role: {builtResume.target_role}
        </p>

        <Section
          title="Professional Summary"
          content={builtResume.professional_summary}
        />

        <SkillsSection
          title="Core Skills"
          items={builtResume.core_skills}
        />

        <SkillsSection
          title="Technical Skills"
          items={builtResume.technical_skills}
        />

        <ExperienceSection
          experience={builtResume.professional_experience}
        />

        <SimpleSection
          title="Education"
          items={builtResume.education}
        />

        <SimpleSection
          title="Projects"
          items={builtResume.projects}
        />

        <SimpleSection
          title="Certifications"
          items={builtResume.certifications}
        />

        <SimpleSection
          title="Languages"
          items={builtResume.languages}
        />

        <Section
          title="References"
          content={builtResume.references}
          preserveLines
        />
      </div>
    </section>
  );
}

function Section({ title, content, preserveLines = false }) {
  if (!content) return null;

  return (
    <div className="mt-6">
      <h3 className="mb-2 text-lg font-semibold text-emerald-400">
        {title}
      </h3>

      {preserveLines ? (
        <pre className="whitespace-pre-wrap font-sans text-slate-300">
          {content}
        </pre>
      ) : (
        <p className="leading-7 text-slate-300">
          {content}
        </p>
      )}
    </div>
  );
}

function SkillsSection({ title, items }) {
  if (!items?.length) return null;

  return (
    <div className="mt-6">
      <h3 className="mb-3 text-lg font-semibold text-emerald-400">
        {title}
      </h3>

      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span
            key={item}
            className="rounded-full bg-emerald-500/10 px-3 py-1 text-sm text-emerald-400"
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

function ExperienceSection({ experience }) {
  if (!experience?.length) return null;

  return (
    <div className="mt-6">
      <h3 className="mb-4 text-lg font-semibold text-emerald-400">
        Professional Experience
      </h3>

      {experience.map((job, index) => (
        <div
          key={index}
          className="mb-5 rounded-2xl border border-slate-800 p-4"
        >
          <h4 className="font-bold text-white">
            {job.role}
          </h4>

          <p className="text-slate-400">
            {job.organisation}
          </p>

          <p className="mb-3 text-sm text-slate-500">
            {job.period}
          </p>

          <ul className="space-y-2">
            {job.bullets?.map((bullet, i) => (
              <li
                key={i}
                className="text-slate-300"
              >
                • {bullet}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function SimpleSection({ title, items }) {
  if (!items?.length) return null;

  return (
    <div className="mt-6">
      <h3 className="mb-3 text-lg font-semibold text-emerald-400">
        {title}
      </h3>

      <ul className="space-y-2">
        {items.map((item, index) => (
          <li
            key={index}
            className="text-slate-300"
          >
            • {item}
          </li>
        ))}
      </ul>
    </div>
  );
}