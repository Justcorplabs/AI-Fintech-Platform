import httpClient from "./httpClient";

function makeResumeForm(
  file,
  targetKeywords,
  jobDescription
) {
  const form = new FormData();

  form.append(
    "file",
    file
  );

  form.append(
    "target_keywords",
    targetKeywords || ""
  );

  form.append(
    "job_description",
    jobDescription || ""
  );

  return form;
}

const multipartConfig = {
  headers: {
    "Content-Type":
      "multipart/form-data",
  },
};

export const recruitmentAPI = {
  createJob: (data) =>
    httpClient.post(
      "/recruitment/jobs",
      data
    ),

  getJobs: () =>
    httpClient.get(
      "/recruitment/jobs"
    ),

  deleteJob: (jobId) =>
    httpClient.delete(
      `/recruitment/jobs/${jobId}`
    ),

  uploadCV: (jobId, file) => {
    const form = new FormData();

    form.append(
      "file",
      file
    );

    return httpClient.post(
      `/recruitment/upload-cv/${jobId}`,
      form,
      multipartConfig
    );
  },

  reviewResume: (
    file,
    targetKeywords,
    jobDescription
  ) =>
    httpClient.post(
      "/recruitment/review-resume",
      makeResumeForm(
        file,
        targetKeywords,
        jobDescription
      ),
      multipartConfig
    ),

  rewriteCV: (
    file,
    targetKeywords,
    jobDescription
  ) =>
    httpClient.post(
      "/recruitment/rewrite-cv",
      makeResumeForm(
        file,
        targetKeywords,
        jobDescription
      ),
      multipartConfig
    ),

  downloadCVDocx: (
    file,
    targetKeywords,
    jobDescription
  ) =>
    httpClient.post(
      "/recruitment/download-cv-docx",
      makeResumeForm(
        file,
        targetKeywords,
        jobDescription
      ),
      {
        ...multipartConfig,
        responseType: "blob",
      }
    ),

  downloadApplicationPackDocx: (
    file,
    targetKeywords,
    jobDescription
  ) =>
    httpClient.post(
      (
        "/recruitment/" +
        "download-application-pack-docx"
      ),
      makeResumeForm(
        file,
        targetKeywords,
        jobDescription
      ),
      {
        ...multipartConfig,
        responseType: "blob",
      }
    ),

  getApplications: (jobId) =>
    httpClient.get(
      (
        "/recruitment/applications/" +
        jobId
      )
    ),

  updateApplicationStatus: (
    applicationId,
    status
  ) =>
    httpClient.patch(
      (
        "/recruitment/applications/" +
        `${applicationId}/status`
      ),
      null,
      {
        params: { status },
      }
    ),

  deleteApplication: (
    applicationId
  ) =>
    httpClient.delete(
      (
        "/recruitment/applications/" +
        applicationId
      )
    ),

  getDashboard: () =>
    httpClient.get(
      "/recruitment/dashboard"
    ),
};
