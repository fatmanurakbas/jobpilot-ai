import axios from "axios";


const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
  // AI-backed endpoints (CV tailoring, validation, job analysis) can take
  // longer than a typical API read. Avoid aborting a still-running request.
  timeout: 180000,
});


api.interceptors.response.use(
  (response) => response,

  (error) => {
    console.error(
      "JobPilot API Error:",
      error.response?.data || error.message
    );

    return Promise.reject(error);
  }
);


export default api;
