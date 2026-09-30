import api from "./api";

const workspaceService = {
  uploadCv(file) {
    const body = new FormData();
    body.append("file", file);
    return api.post("/documents/cv", body, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  getCandidate: () => api.get("/documents/candidates"),
  getJobs: () => api.get("/jobs/"),
  analyzeAndSaveJob: (jobDescription, jobUrl) =>
    api.post("/jobs/analyze-and-save", { job_description: jobDescription, job_url: jobUrl || null }),
};

export default workspaceService;
