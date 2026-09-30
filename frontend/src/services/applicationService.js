import api from "./api";

const base = (applicationId) => `/applications/${applicationId}`;
const fileUrl = (path) => `${api.defaults.baseURL || "http://localhost:8000"}${path}`;

const applicationService = {
  getPackage: (id) => api.get(`${base(id)}/package`),
  getApprovalStatus: (id) => api.get(`${base(id)}/approval-status`),
  getSubmissionApprovalStatus: (id) => api.get(`${base(id)}/submission-approval-status`),
  match: (candidateId, jobId) => api.post(`/applications/match/${candidateId}/${jobId}`),
  tailorCv: (id) => api.post(`${base(id)}/tailor-cv`),
  validateCv: (id) => api.post(`${base(id)}/validate-cv`),
  correctCv: (id) => api.post(`${base(id)}/correct-cv`),
  finalizeCv: (id) => api.post(`${base(id)}/finalize-cv`),
  generateCv: (id) => api.post(`${base(id)}/generate-cv`, null, { responseType: "blob" }),
  generateCoverLetter: (id) => api.post(`${base(id)}/generate-cover-letter`),
  validateCoverLetter: (id) => api.post(`${base(id)}/validate-cover-letter`),
  correctCoverLetter: (id) => api.post(`${base(id)}/correct-cover-letter`),
  finalizeCoverLetter: (id) => api.post(`${base(id)}/finalize-cover-letter`),
  approvePackage: (id) => api.post(`${base(id)}/approve-package`),
  inspectForm: (id, url) => api.post(`${base(id)}/inspect-form`, { url }),
  mapForm: (id, url) => api.post(`${base(id)}/map-form`, { url }),
  saveFormAnswers: (id, answers) => api.post(`${base(id)}/form-answers`, { answers }),
  resolveForm: (id, url) => api.post(`${base(id)}/resolve-form`, { url }),
  fillForm: (id, url) => api.post(`${base(id)}/fill-form`, { url }),
  browserReviewPlan: (id, url) => api.post(`${base(id)}/browser-review-plan`, { url }),
  approveSubmission: (id, url) => api.post(`${base(id)}/approve-submission`, { url }),
  submit: (id) => api.post(`${base(id)}/submit-application`),
  cvDocxUrl: (id) => fileUrl(`${base(id)}/cv/docx`),
  cvPdfUrl: (id) => fileUrl(`${base(id)}/cv/pdf`),
  coverLetterDocxUrl: (id) => fileUrl(`${base(id)}/cover-letter/docx`),
  coverLetterPdfUrl: (id) => fileUrl(`${base(id)}/cover-letter/pdf`),
  formScreenshotUrl: (id) => fileUrl(`${base(id)}/form-screenshot`),
  submissionScreenshotUrl: (id) => fileUrl(`${base(id)}/submission-screenshot`),
};

export default applicationService;
