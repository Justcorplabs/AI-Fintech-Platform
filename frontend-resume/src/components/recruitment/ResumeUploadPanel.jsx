import { Download, Sparkles, Upload, Wand2 } from "lucide-react";

export default function ResumeUploadPanel({
  file,
  setFile,
  keywords,
  setKeywords,
  jobDescription,
  setJobDescription,
  loading,
  rewriting,
  onReview,
  onGenerateCV,
  onDownloadCV,
  onDownloadApplicationPack,
}) {
  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
      <h2 className="text-lg font-semibold text-white">Resume & Job Input</h2>
      <p className="mt-1 text-sm text-slate-400">
        Upload a CV and paste the job description.
      </p>

      <label className="mt-5 flex cursor-pointer flex-col items-center justify-center rounded-3xl border border-dashed border-slate-700 bg-slate-950 p-8 text-center hover:border-sky-500">
        <Upload className="mb-3 text-sky-400" size={34} />
        <p className="font-semibold text-white">
          {file ? file.name : "Choose resume file"}
        </p>
        <p className="mt-1 text-sm text-slate-500">PDF, DOCX, or TXT</p>
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
      </label>

      <label className="mt-5 grid gap-2">
        <span className="text-sm text-slate-400">Optional Target Keywords</span>
        <textarea
          rows={3}
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          placeholder="Leave blank to let AI extract job requirements automatically..."
          className="rounded-2xl border border-slate-800 bg-slate-950 p-3 text-slate-100 outline-none focus:border-sky-500"
        />
      </label>

      <label className="mt-5 grid gap-2">
        <span className="text-sm text-slate-400">Job Description</span>
        <textarea
          rows={11}
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste the full job description here..."
          className="rounded-2xl border border-slate-800 bg-slate-950 p-3 text-slate-100 outline-none focus:border-sky-500"
        />
      </label>

      <div className="mt-5 grid gap-3">
        <button
          onClick={onReview}
          disabled={loading || rewriting}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-sky-500 px-4 py-3 font-bold text-white hover:bg-sky-600 disabled:opacity-60"
        >
          <Sparkles size={18} />
          {loading ? "Analysing..." : "Run AI Job Match Review"}
        </button>

        <button
          onClick={onGenerateCV}
          disabled={loading || rewriting}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-500 px-4 py-3 font-bold text-white hover:bg-emerald-600 disabled:opacity-60"
        >
          <Wand2 size={18} />
          {rewriting ? "Generating..." : "Generate Optimized CV"}
        </button>

        <button
          onClick={onDownloadCV}
          disabled={loading || rewriting}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-500 px-4 py-3 font-bold text-white hover:bg-indigo-600 disabled:opacity-60"
        >
          <Download size={18} />
          Download Optimized CV DOCX
        </button>

        <button
          onClick={onDownloadApplicationPack}
          disabled={loading || rewriting}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-purple-500 px-4 py-3 font-bold text-white hover:bg-purple-600 disabled:opacity-60"
        >
          <Download size={18} />
          Download Application Pack DOCX
        </button>
      </div>
    </section>
  );
}