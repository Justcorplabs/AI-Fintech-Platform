import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

function makeResumeForm(file, targetKeywords, jobDescription) {
  const form = new FormData();
  form.append("file", file);
  form.append("target_keywords", targetKeywords || "");
  form.append("job_description", jobDescription || "");
  return form;
}

export const authAPI = {
  login: (data) => api.post("/auth/login", data),
  register: (data) => api.post("/auth/register", data),
};

export const fraudAPI = {
  predict: (data) => api.post("/fraud/predict", data),
  getTransactions: (params) => api.get("/fraud/transactions", { params }),
  getTransaction: (id) => api.get(`/fraud/transactions/${id}`),
  reviewTransaction: (id, data) =>
    api.patch(`/fraud/transactions/${id}/review`, data),
  getStats: () => api.get("/fraud/stats"),
  getModelMetadata: () => api.get("/fraud/model/metadata"),
};

export const recruitmentAPI = {
  createJob: (data) => api.post("/recruitment/jobs", data),
  getJobs: () => api.get("/recruitment/jobs"),
  deleteJob: (jobId) => api.delete(`/recruitment/jobs/${jobId}`),

  uploadCV: (jobId, file) => {
    const form = new FormData();
    form.append("file", file);
    return api.post(`/recruitment/upload-cv/${jobId}`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  reviewResume: (file, targetKeywords, jobDescription) =>
    api.post(
      "/recruitment/review-resume",
      makeResumeForm(file, targetKeywords, jobDescription),
      { headers: { "Content-Type": "multipart/form-data" } }
    ),

  rewriteCV: (file, targetKeywords, jobDescription) =>
    api.post(
      "/recruitment/rewrite-cv",
      makeResumeForm(file, targetKeywords, jobDescription),
      { headers: { "Content-Type": "multipart/form-data" } }
    ),

  downloadCVDocx: (file, targetKeywords, jobDescription) =>
    api.post(
      "/recruitment/download-cv-docx",
      makeResumeForm(file, targetKeywords, jobDescription),
      {
        headers: { "Content-Type": "multipart/form-data" },
        responseType: "blob",
      }
    ),

  downloadApplicationPackDocx: (file, targetKeywords, jobDescription) =>
    api.post(
      "/recruitment/download-application-pack-docx",
      makeResumeForm(file, targetKeywords, jobDescription),
      {
        headers: { "Content-Type": "multipart/form-data" },
        responseType: "blob",
      }
    ),

  getApplications: (jobId) => api.get(`/recruitment/applications/${jobId}`),

  updateApplicationStatus: (applicationId, status) =>
    api.patch(`/recruitment/applications/${applicationId}/status`, null, {
      params: { status },
    }),

  deleteApplication: (applicationId) =>
    api.delete(`/recruitment/applications/${applicationId}`),

  getDashboard: () => api.get("/recruitment/dashboard"),
};

export default api;