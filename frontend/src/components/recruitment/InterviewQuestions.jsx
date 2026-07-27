import { MessageSquare } from "lucide-react";

export default function InterviewQuestions({ questions }) {
  if (!questions?.length) return null;

  return (
    <section className="mt-6 rounded-3xl border border-slate-800 bg-slate-950 p-6">
      <div className="mb-5 flex items-center gap-3">
        <MessageSquare className="text-sky-400" />
        <h2 className="text-lg font-semibold text-white">
          Interview Questions
        </h2>
      </div>

      <ol className="space-y-3 text-slate-300">
        {questions.map((question, index) => (
          <li key={index}>
            <span className="font-semibold text-sky-400">{index + 1}.</span>{" "}
            {question}
          </li>
        ))}
      </ol>
    </section>
  );
}