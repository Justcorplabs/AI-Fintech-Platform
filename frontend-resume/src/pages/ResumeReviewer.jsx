import { useState } from "react";
import toast from "react-hot-toast";
import { FileText } from "lucide-react";

import { recruitmentAPI } from "../services/api";

import ResumeUploadPanel from "../components/recruitment/ResumeUploadPanel";
import ATSScoreCards from "../components/recruitment/ATSScoreCards";
import StructuredJobProfile from "../components/recruitment/StructuredJobProfile";
import RecruiterIntelligence from "../components/recruitment/RecruiterIntelligence";
import OptimizedCVPreview from "../components/recruitment/OptimizedCVPreview";
import ReviewPanels from "../components/recruitment/ReviewPanels";
import InterviewQuestions from "../components/recruitment/InterviewQuestions";
import ExtractedSections from "../components/recruitment/ExtractedSections";

export default function ResumeReviewer() {
  const [file, setFile] = useState(null);
  const [keywords, setKeywords] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [review, setReview] = useState(null);
  const [builtResume, setBuiltResume] = useState(null);
  const [loading, setLoading] = useState(false);
  const [rewriting, setRewriting] = useState(false);

  async function reviewResume() {
    if (!file) {
      toast.error("Please choose a resume first.");
      return;
    }

    try {
      setLoading(true);
      const res = await recruitmentAPI.reviewResume(
        file,
        keywords,
        jobDescription
      );

      setReview(res.data);
      setBuiltResume(res.data.built_resume || null);
      toast.success("Resume reviewed successfully.");
    } catch (err) {
      console.error(err);
      toast.error("Resume review failed.");
    } finally {
      setLoading(false);
    }
  }

  async function generateOptimizedCV() {
    if (!file) {
      toast.error("Please choose a resume first.");
      return;
    }

    try {
      setRewriting(true);
      const res = await recruitmentAPI.rewriteCV(
        file,
        keywords,
        jobDescription
      );

      setReview(res.data.review || null);
      setBuiltResume(res.data.built_resume || null);
      toast.success("Optimized CV generated.");
    } catch (err) {
      console.error(err);
      toast.error("CV generation failed.");
    } finally {
      setRewriting(false);
    }
  }

  function saveBlob(res, fallbackName) {
    const blob = new Blob([res.data], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });

    const disposition = res.headers["content-disposition"];
    let filename = fallbackName;

    if (disposition) {
      const match = disposition.match(/filename="?([^";]+)"?/);
      if (match?.[1]) filename = match[1];
    }

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  async function downloadCVDocx() {
    if (!file) {
      toast.error("Please choose a resume first.");
      return;
    }

    const toastId = toast.loading("Generating optimized CV DOCX...");

    try {
      const res = await recruitmentAPI.downloadCVDocx(
        file,
        keywords,
        jobDescription
      );

      saveBlob(res, "Optimized_CV.docx");
      toast.success("Optimized CV downloaded.", { id: toastId });
    } catch (err) {
      console.error(err);
      toast.error("DOCX download failed.", { id: toastId });
    }
  }

  async function downloadApplicationPackDocx() {
    if (!file) {
      toast.error("Please choose a resume first.");
      return;
    }

    const toastId = toast.loading("Generating application pack DOCX...");

    try {
      const res = await recruitmentAPI.downloadApplicationPackDocx(
        file,
        keywords,
        jobDescription
      );

      saveBlob(res, "Application_Pack.docx");
      toast.success("Application pack downloaded.", { id: toastId });
    } catch (err) {
      console.error(err);
      toast.error("Application pack download failed.", { id: toastId });
    }
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white">
          AI Resume Reviewer
        </h1>
        <p className="mt-1 text-slate-400">
          Compare a CV against a structured job profile, score fit, generate a
          recruiter-ready CV, and prepare interview guidance.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <ResumeUploadPanel
          file={file}
          setFile={setFile}
          keywords={keywords}
          setKeywords={setKeywords}
          jobDescription={jobDescription}
          setJobDescription={setJobDescription}
          loading={loading}
          rewriting={rewriting}
          onReview={reviewResume}
          onGenerateCV={generateOptimizedCV}
          onDownloadCV={downloadCVDocx}
          onDownloadApplicationPack={downloadApplicationPackDocx}
        />

        <section className="col-span-2 rounded-3xl border border-slate-800 bg-slate-900 p-6">
          {!review ? (
            <EmptyState />
          ) : (
            <div>
              <ATSScoreCards review={review} />

              <RecruiterIntelligence
                intelligence={review.candidate_intelligence}
              />

              <StructuredJobProfile review={review} />

              <OptimizedCVPreview
                builtResume={builtResume || review.built_resume}
              />

              <ReviewPanels review={review} />

              <InterviewQuestions
                questions={review.interview_questions || []}
              />

              <ExtractedSections
                review={{
                  extracted_responsibilities: review.responsibilities || [],
                  extracted_qualifications: review.qualifications || [],
                }}
              />
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex min-h-[520px] flex-col items-center justify-center text-center">
      <FileText size={52} className="text-slate-600" />
      <h2 className="mt-4 text-xl font-semibold text-white">
        No resume reviewed yet
      </h2>
      <p className="mt-2 max-w-md text-slate-400">
        Upload a CV and paste a job description to extract a structured job
        profile, calculate ATS score, recruiter intelligence, missing
        requirements, and interview guidance.
      </p>
    </div>
  );
}