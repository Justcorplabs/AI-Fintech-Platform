import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import {
  AlertTriangle,
  Brain,
  Briefcase,
  CheckCircle2,
  Eye,
  RefreshCw,
  Star,
  Trash2,
  Upload,
  UserRound,
  Users,
  XCircle,
} from "lucide-react";
import { recruitmentAPI } from "../services/api";

export default function Recruitment() {
  const [dashboard, setDashboard] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [applications, setApplications] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const [jobForm, setJobForm] = useState({
    title: "",
    organisation: "",
    required_experience_years: 0,
    required_skills: "",
    description: "",
  });

  const selectedJob = useMemo(
    () => jobs.find((job) => String(job.id) === String(selectedJobId)),
    [jobs, selectedJobId]
  );

  useEffect(() => {
    loadRecruitment();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadRecruitment() {
    try {
      setLoading(true);
      const [dashRes, jobsRes] = await Promise.all([
        recruitmentAPI.getDashboard(),
        recruitmentAPI.getJobs(),
      ]);

      const loadedJobs = jobsRes.data || [];
      setDashboard(dashRes.data);
      setJobs(loadedJobs);

      const jobToLoad = selectedJobId || loadedJobs?.[0]?.id || "";

      if (jobToLoad) {
        setSelectedJobId(String(jobToLoad));
        const appsRes = await recruitmentAPI.getApplications(jobToLoad);
        const loadedApps = appsRes.data || [];
        setApplications(loadedApps);
        setSelectedCandidate(loadedApps?.[0] || null);
      } else {
        setApplications([]);
        setSelectedCandidate(null);
      }
    } catch (err) {
      console.error(err);
      toast.error("Failed to load Recruitment AI.");
    } finally {
      setLoading(false);
    }
  }

  async function loadApplications(jobId) {
    if (!jobId) {
      setSelectedJobId("");
      setApplications([]);
      setSelectedCandidate(null);
      return;
    }

    try {
      setSelectedJobId(String(jobId));
      const res = await recruitmentAPI.getApplications(jobId);
      const loadedApps = res.data || [];
      setApplications(loadedApps);
      setSelectedCandidate(loadedApps?.[0] || null);
    } catch (err) {
      console.error(err);
      toast.error("Failed to load applications.");
    }
  }

  async function createJob(e) {
    e.preventDefault();

    if (!jobForm.title.trim()) {
      toast.error("Job title is required.");
      return;
    }

    try {
      const payload = {
        title: jobForm.title.trim(),
        organisation: jobForm.organisation.trim() || null,
        required_experience_years: Number(jobForm.required_experience_years || 0),
        description: jobForm.description.trim(),
        required_skills: jobForm.required_skills
          .split(",")
          .map((skill) => skill.trim())
          .filter(Boolean),
      };

      const res = await recruitmentAPI.createJob(payload);
      toast.success("Job created.");
      setJobForm({
        title: "",
        organisation: "",
        required_experience_years: 0,
        required_skills: "",
        description: "",
      });

      setSelectedJobId(String(res.data.id));
      await loadRecruitment();
      await loadApplications(res.data.id);
    } catch (err) {
      console.error(err);
      toast.error("Failed to create job.");
    }
  }

  async function deleteJob(jobId) {
    if (!jobId) {
      toast.error("Select a job first.");
      return;
    }

    const job = jobs.find((item) => String(item.id) === String(jobId));
    const confirmed = window.confirm(
      `Delete this job?\n\n${job?.title || "Selected job"}\n\nThis will also delete all uploaded CVs for this job. This cannot be undone.`
    );

    if (!confirmed) return;

    try {
      await recruitmentAPI.deleteJob(jobId);
      toast.success("Job deleted.");
      setApplications([]);
      setSelectedCandidate(null);
      await loadRecruitment();
    } catch (err) {
      console.error(err);
      toast.error("Failed to delete job.");
    }
  }

  async function uploadCV(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!selectedJobId) {
      toast.error("Create or select a job first.");
      e.target.value = "";
      return;
    }

    try {
      setUploading(true);
      const res = await recruitmentAPI.uploadCV(selectedJobId, file);
      toast.success(`CV scored: ${Number(res.data.match_score || 0).toFixed(2)}%`);
      await loadApplications(selectedJobId);
      await loadRecruitment();
    } catch (err) {
      console.error(err);
      toast.error("CV upload/scoring failed.");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function updateStatus(applicationId, status) {
    try {
      await recruitmentAPI.updateApplicationStatus(applicationId, status);
      toast.success(`Candidate ${status}.`);
      await loadApplications(selectedJobId);
      await loadRecruitment();
    } catch (err) {
      console.error(err);
      toast.error("Failed to update candidate status.");
    }
  }

  async function deleteCandidate(applicationId) {
    const confirmed = window.confirm(
      "Delete this candidate application? This cannot be undone."
    );

    if (!confirmed) return;

    try {
      await recruitmentAPI.deleteApplication(applicationId);
      toast.success("Candidate deleted.");
      setSelectedCandidate(null);
      await loadApplications(selectedJobId);
      await loadRecruitment();
    } catch (err) {
      console.error(err);
      toast.error("Failed to delete candidate.");
    }
  }

  if (loading) {
    return <p className="text-slate-400">Loading Recruitment AI...</p>;
  }

  return (
    <div>
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Recruitment AI</h1>
          <p className="mt-1 text-slate-400">
            Intelligent CV screening, candidate scoring, ranking, and shortlist workflow.
          </p>
        </div>

        <button
          onClick={loadRecruitment}
          className="flex items-center gap-2 rounded-xl bg-sky-500 px-4 py-3 font-bold text-white hover:bg-sky-600"
        >
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      <div className="mb-6 grid grid-cols-4 gap-5">
        <RecruitmentCard title="Jobs" value={dashboard?.total_jobs ?? 0} icon={Briefcase} />
        <RecruitmentCard title="Applications" value={dashboard?.total_applications ?? 0} icon={Users} />
        <RecruitmentCard title="Scored" value={dashboard?.scored_applications ?? 0} icon={Star} success />
        <RecruitmentCard title="Shortlisted" value={dashboard?.shortlisted ?? 0} icon={CheckCircle2} success />
      </div>

      <div className="grid grid-cols-3 gap-6">
        <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-lg font-semibold text-white">Create Job</h2>
          <p className="mt-1 text-sm text-slate-400">
            Paste a job advert or define requirements for Sentinel AI candidate ranking.
          </p>

          <form onSubmit={createJob} className="mt-5 grid gap-3">
            <Input label="Job Title" value={jobForm.title} onChange={(value) => setJobForm({ ...jobForm, title: value })} />
            <Input label="Organisation" value={jobForm.organisation} onChange={(value) => setJobForm({ ...jobForm, organisation: value })} />
            <Input label="Required Experience Years" type="number" value={jobForm.required_experience_years} onChange={(value) => setJobForm({ ...jobForm, required_experience_years: value })} />
            <Input label="Required Skills comma-separated" value={jobForm.required_skills} onChange={(value) => setJobForm({ ...jobForm, required_skills: value })} />

            <label className="grid gap-2">
              <span className="text-sm text-slate-400">Description / Full Job Advert</span>
              <textarea
                rows={10}
                value={jobForm.description}
                onChange={(e) => setJobForm({ ...jobForm, description: e.target.value })}
                placeholder="Paste the full job description here..."
                className="rounded-2xl border border-slate-800 bg-slate-950 p-3 text-slate-100 outline-none focus:border-sky-500"
              />
            </label>

            <button className="mt-2 rounded-xl bg-sky-500 px-4 py-3 font-bold text-white hover:bg-sky-600">
              Create Job
            </button>
          </form>
        </section>

        <section className="col-span-2 rounded-3xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-white">Candidate Ranking</h2>
              <p className="text-sm text-slate-400">
                Upload CVs and rank candidates using Sentinel AI Recruiter scoring.
              </p>
            </div>

            <div className="flex items-center gap-3">
              {selectedJobId && (
                <button
                  type="button"
                  onClick={() => deleteJob(selectedJobId)}
                  className="flex items-center gap-2 rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 font-bold text-red-300 hover:bg-red-500/20"
                >
                  <Trash2 size={18} />
                  Delete Job
                </button>
              )}

              <label className="flex cursor-pointer items-center gap-2 rounded-xl bg-emerald-500 px-4 py-3 font-bold text-white hover:bg-emerald-600">
                <Upload size={18} />
                {uploading ? "Uploading..." : "Upload CV"}
                <input type="file" accept=".txt,.pdf,.docx" onChange={uploadCV} className="hidden" />
              </label>
            </div>
          </div>

          <div className="mb-5 grid grid-cols-2 gap-4">
            <select
              value={selectedJobId}
              onChange={(e) => loadApplications(e.target.value)}
              className="w-full rounded-2xl border border-slate-800 bg-slate-950 px-4 py-3 text-slate-100 outline-none"
            >
              <option value="">Select a job</option>
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title} — {job.organisation || "Organisation"}
                </option>
              ))}
            </select>

            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
              <p className="text-xs uppercase tracking-wider text-slate-500">Current Job</p>
              <p className="mt-2 font-semibold text-white">{selectedJob?.title || "No job selected"}</p>
              <p className="text-sm text-slate-400">{selectedJob?.organisation || "Organisation not specified"}</p>
            </div>
          </div>

          {applications.length === 0 ? (
            <p className="rounded-2xl border border-slate-800 bg-slate-950 p-5 text-slate-400">
              No candidates uploaded for this job yet.
            </p>
          ) : (
            <CandidateTable applications={applications} selectedCandidate={selectedCandidate} setSelectedCandidate={setSelectedCandidate} />
          )}
        </section>
      </div>

      {selectedCandidate && (
        <CandidateDetails
          candidate={selectedCandidate}
          onDelete={deleteCandidate}
          onShortlist={(id) => updateStatus(id, "shortlisted")}
          onReject={(id) => updateStatus(id, "rejected")}
        />
      )}
    </div>
  );
}

function CandidateTable({ applications, selectedCandidate, setSelectedCandidate }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-800">
      <table className="w-full min-w-[980px] border-collapse">
        <thead className="bg-slate-950 text-left text-sm text-slate-400">
          <tr>
            <th className="p-4">Candidate</th>
            <th className="p-4">Recruiter Score</th>
            <th className="p-4">Top Evidence</th>
            <th className="p-4">Education</th>
            <th className="p-4">Status</th>
            <th className="p-4 text-center">View</th>
          </tr>
        </thead>
        <tbody>
          {applications.map((app) => {
            const parsed = app.parsed_data || {};
            const review = parsed.sentinel_review || {};
            const intelligence = parsed.candidate_intelligence || {};
            const found = review.found_keywords || app.extracted_skills || [];

            return (
              <tr key={app.id} className={`border-t border-slate-800 hover:bg-slate-800/40 ${selectedCandidate?.id === app.id ? "bg-sky-500/5" : ""}`}>
                <td className="p-4">
                  <p className="font-semibold text-white">{app.candidate_name || app.cv_filename || "Candidate"}</p>
                  <p className="text-sm text-slate-400">{app.candidate_email || "No email found"}</p>
                </td>
                <td className="p-4">
                  <ScoreBadge score={app.match_score || 0} />
                  <p className="mt-1 text-xs text-slate-500">
                    {intelligence.overall_rating || "N/A"} · {intelligence.hiring_recommendation || "Review"}
                  </p>
                </td>
                <td className="max-w-[260px] p-4 text-sm text-slate-300">{found.slice(0, 4).join(", ") || "None"}</td>
                <td className="max-w-[240px] p-4 text-slate-300">{app.education_level || "Unknown"}</td>
                <td className="p-4"><StatusBadge status={app.status} /></td>
                <td className="p-4 text-center">
                  <button onClick={() => setSelectedCandidate(app)} className="inline-flex items-center justify-center rounded-xl border border-sky-500/40 bg-sky-500/10 p-3 text-sky-300 hover:bg-sky-500/20" title="View candidate details">
                    <Eye size={18} />
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function CandidateDetails({ candidate, onDelete, onShortlist, onReject }) {
  const parsed = candidate.parsed_data || {};
  const review = parsed.sentinel_review || {};
  const intelligence = parsed.candidate_intelligence || {};
  const explainability = intelligence.explainability || {};

  const found = review.found_keywords || candidate.extracted_skills || [];
  const missing = review.missing_keywords || [];
  const strengths = intelligence.candidate_strengths || [];
  const risks = intelligence.hiring_risks || [];

  return (
    <section className="mt-6 rounded-3xl border border-slate-800 bg-slate-900 p-6">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Brain className="text-sky-400" />
          <div>
            <h2 className="text-lg font-semibold text-white">Candidate Details & AI Explanation</h2>
            <p className="text-sm text-slate-400">Score breakdown, matched requirements, missing requirements, and recruiter reasoning.</p>
          </div>
        </div>
        <button onClick={() => onDelete(candidate.id)} className="flex items-center gap-2 rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 font-bold text-red-300 hover:bg-red-500/20">
          <Trash2 size={18} /> Delete Candidate
        </button>
      </div>

      <div className="grid grid-cols-4 gap-5">
        <DetailCard title="Candidate" value={candidate.candidate_name || candidate.cv_filename || "Candidate"} />
        <DetailCard title="Recruiter Score" value={`${Number(candidate.match_score || 0).toFixed(2)}%`} />
        <DetailCard title="ATS Score" value={`${Number(review.ats_score || 0).toFixed(2)}%`} />
        <DetailCard title="Confidence" value={`${Number(intelligence.confidence || 0).toFixed(2)}%`} />
      </div>

      <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-950 p-5">
        <p className="text-xs uppercase tracking-wider text-slate-500">Hiring Recommendation</p>
        <h3 className="mt-2 text-xl font-bold text-emerald-400">{intelligence.hiring_recommendation || "Review Required"}</h3>
        <p className="mt-3 leading-7 text-slate-300">{intelligence.recruiter_summary || candidate.llm_reasoning}</p>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-6">
        <Panel title="Matched Requirements" icon={CheckCircle2} positive><TagList items={found} positive /></Panel>
        <Panel title="Missing Requirements" icon={AlertTriangle}><TagList items={missing} /></Panel>
        <Panel title="Candidate Strengths" icon={Star} positive><List items={strengths} /></Panel>
        <Panel title="Hiring Risks" icon={AlertTriangle}>
          {risks.length === 0 ? <p className="text-sm text-slate-400">No major risks detected.</p> : (
            <div className="space-y-3">
              {risks.map((risk, index) => (
                <div key={index} className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
                  <p className="font-semibold text-yellow-400">{risk.risk}</p>
                  <p className="mt-1 text-sm text-slate-400">Level: {risk.level || "N/A"}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{risk.mitigation}</p>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>

      <div className="mt-6 rounded-3xl border border-slate-800 bg-slate-950 p-5">
        <h3 className="mb-4 font-semibold text-white">Why This Score?</h3>
        <p className="mb-4 leading-7 text-slate-300">{explainability.summary || candidate.llm_reasoning || "Reasoning not available."}</p>
        {(explainability.score_breakdown || []).length === 0 ? <p className="text-sm text-slate-400">No score breakdown available.</p> : (
          <div className="grid grid-cols-2 gap-4">
            {explainability.score_breakdown.map((item, index) => (
              <div key={index} className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
                <p className="font-semibold text-white">{item.impact} {item.factor}</p>
                <p className="mt-2 text-sm leading-6 text-slate-300">{item.reason}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-950 p-5">
        <p className="font-semibold text-white">AI Reasoning</p>
        <p className="mt-2 leading-7 text-slate-400">{candidate.llm_reasoning || "Reasoning not available for this candidate."}</p>
      </div>

      <div className="mt-5 flex gap-3">
        <button onClick={() => onShortlist(candidate.id)} className="flex items-center gap-2 rounded-xl bg-emerald-500 px-4 py-3 font-bold text-white hover:bg-emerald-600"><CheckCircle2 size={18} /> Shortlist Candidate</button>
        <button onClick={() => onReject(candidate.id)} className="flex items-center gap-2 rounded-xl bg-red-500 px-4 py-3 font-bold text-white hover:bg-red-600"><XCircle size={18} /> Reject Candidate</button>
      </div>
    </section>
  );
}

function RecruitmentCard({ title, value, icon: Icon, success }) {
  return <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6"><div className="mb-5 flex items-center justify-between"><p className="text-sm text-slate-400">{title}</p><Icon size={22} className={success ? "text-emerald-400" : "text-sky-400"} /></div><h2 className="text-3xl font-semibold text-white">{value}</h2></div>;
}

function Input({ label, value, onChange, type = "text" }) {
  return <label className="grid gap-2"><span className="text-sm text-slate-400">{label}</span><input type={type} value={value} onChange={(e) => onChange(e.target.value)} className="rounded-2xl border border-slate-800 bg-slate-950 px-4 py-3 text-slate-100 outline-none focus:border-sky-500" /></label>;
}

function ScoreBadge({ score }) {
  const numericScore = Number(score || 0);
  const style = numericScore >= 75 ? "bg-emerald-500/10 text-emerald-400" : numericScore >= 50 ? "bg-yellow-500/10 text-yellow-400" : "bg-red-500/10 text-red-400";
  return <span className={`rounded-full px-3 py-1 text-sm font-bold ${style}`}>{numericScore.toFixed(2)}%</span>;
}

function StatusBadge({ status }) {
  const styles = { scored: "bg-sky-500/10 text-sky-400", shortlisted: "bg-emerald-500/10 text-emerald-400", rejected: "bg-red-500/10 text-red-400", parsed: "bg-yellow-500/10 text-yellow-400", uploaded: "bg-slate-700 text-slate-300" };
  return <span className={`rounded-full px-3 py-1 text-sm font-bold ${styles[status] || styles.uploaded}`}>{status}</span>;
}

function DetailCard({ title, value }) {
  return <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4"><p className="text-xs uppercase tracking-wider text-slate-500">{title}</p><p className="mt-2 break-words font-semibold text-white">{value}</p></div>;
}

function Panel({ title, icon: Icon, children, positive }) {
  return <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5"><div className="mb-3 flex items-center gap-2">{Icon && <Icon size={18} className={positive ? "text-emerald-400" : "text-yellow-400"} />}<p className="font-semibold text-white">{title}</p></div>{children}</div>;
}

function TagList({ items, positive }) {
  if (!items?.length) return <p className="text-sm text-slate-400">None detected.</p>;
  return <div className="flex flex-wrap gap-2">{items.map((item) => <span key={item} className={`rounded-full px-3 py-1 text-sm font-semibold ${positive ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"}`}>{item}</span>)}</div>;
}

function List({ items }) {
  if (!items?.length) return <p className="text-sm text-slate-400">None detected.</p>;
  return <ul className="space-y-2 text-sm text-slate-300">{items.map((item, index) => <li key={index}>• {item}</li>)}</ul>;
}
