import axios from "axios";
import { getDemoRole } from "./demoRole.js";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL,
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  config.headers["X-Demo-Role"] = getDemoRole();
  return config;
});

// --------------------------------------------------------------- endpoints
export const sopApi = {
  list: (params) => api.get("/api/sops", { params }).then((r) => r.data),
  get: (id) => api.get(`/api/sops/${id}`).then((r) => r.data),
  create: (body) => api.post("/api/sops", body).then((r) => r.data),
  publish: (id) => api.post(`/api/sops/${id}/publish`).then((r) => r.data),
  generate: (body) => api.post("/api/sops/generate", body).then((r) => r.data),
  uploadVideo: (file) => {
    const form = new FormData();
    form.append("file", file);
    return api
      .post("/api/sops/upload-video", form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
};

export const sessionApi = {
  list: (params) => api.get("/api/sessions", { params }).then((r) => r.data),
  get: (id) => api.get(`/api/sessions/${id}`).then((r) => r.data),
  create: (body) => api.post("/api/sessions", body).then((r) => r.data),
  summary: (id) => api.get(`/api/sessions/${id}/summary`).then((r) => r.data),
};

export const alertApi = {
  list: (params) => api.get("/api/alerts", { params }).then((r) => r.data),
  ack: (id) => api.post(`/api/alerts/${id}/ack`).then((r) => r.data),
};

export const analyticsApi = {
  muda: (sessionId) =>
    api.get(`/api/analytics/sessions/${sessionId}/muda`).then((r) => r.data),
  ergonomics: (sessionId) =>
    api.get(`/api/analytics/sessions/${sessionId}/ergonomics`).then((r) => r.data),
  heatmapUrl: (sessionId) => `${baseURL}/api/analytics/sessions/${sessionId}/heatmap`,
};
