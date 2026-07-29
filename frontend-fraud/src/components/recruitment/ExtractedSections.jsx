import { ClipboardList } from "lucide-react";

export default function ExtractedSections({ review }) {
  if (!review) return null;

  return (
    <section className="mt-6 rounded-3xl border border-slate-800 bg-slate-950 p-6">
      <div className="mb-5 flex items-center gap-3">
        <ClipboardList className="text-sky-400" />
        <h2 className="text-lg font-semibold text-white">
          Extracted Information
        </h2>
      </div>

      <div className="grid grid-cols-2 gap-6">

        <ExtractedCard
          title="Responsibilities"
          items={review.extracted_responsibilities || []}
        />

        <ExtractedCard
          title="Qualifications"
          items={review.extracted_qualifications || []}
        />

      </div>
    </section>
  );
}

function ExtractedCard({ title, items }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <h3 className="mb-4 font-semibold text-white">
        {title}
      </h3>

      {!items?.length ? (
        <p className="text-sm text-slate-400">
          Nothing extracted.
        </p>
      ) : (
        <ul className="space-y-2">
          {items.map((item, index) => (
            <li
              key={index}
              className="text-sm leading-6 text-slate-300"
            >
              • {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}