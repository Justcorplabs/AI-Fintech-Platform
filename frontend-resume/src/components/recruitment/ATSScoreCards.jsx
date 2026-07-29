export default function ATSScoreCards({ review }) {
  if (!review) return null;

  return (
    <div className="mb-6 grid grid-cols-4 gap-5">
      <ScoreCard title="ATS Score" value={review.ats_score} main />
      <ScoreCard title="Job Match" value={review.job_match_score} />
      <ScoreCard title="Skills" value={review.skills_score} />
      <ScoreCard title="Interview Chance" value={review.interview_probability} />
    </div>
  );
}

function ScoreCard({ title, value, main }) {
  const score = Number(value || 0);

  const color =
    score >= 80
      ? "text-emerald-400"
      : score >= 60
      ? "text-yellow-400"
      : "text-red-400";

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
      <p className="text-sm text-slate-400">{title}</p>
      <h3 className={`mt-2 font-bold ${color} ${main ? "text-4xl" : "text-3xl"}`}>
        {score.toFixed(2)}%
      </h3>
    </div>
  );
}