// Thin wrapper over the PrintGuard backend. Paths are relative; Vite proxies /api in dev.
// For a deployed build set VITE_API_BASE (e.g. "http://127.0.0.1:8000").
const BASE = import.meta.env.VITE_API_BASE || "";

async function request(path, options) {
  const res = await fetch(BASE + path, options);
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d) => d.msg).join("; ");
    } catch { /* keep default */ }
    throw new Error(detail);
  }
  return res;
}

const json = (body) => ({
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  url: (path) => BASE + path,
  async inspect(file, config, batchId) {
    const form = new FormData();
    form.append("file", file);
    if (config && Object.keys(config).length) form.append("config", JSON.stringify(config));
    if (batchId) form.append("batch_id", String(batchId));
    return (await request("/api/inspect", { method: "POST", body: form })).json();
  },
  async getInspection(id) {
    return (await request(`/api/inspections/${id}`)).json();
  },
  async setFindingStatus(id, findingId, status) {
    return (await request(`/api/inspections/${id}/findings/${findingId}`, { method: "PATCH", ...json({ status }) })).json();
  },
  reportUrl: (id) => BASE + `/api/inspections/${id}/report`,
  async listBatches() {
    return (await request("/api/batches")).json();
  },
  async createBatch(body) {
    return (await request("/api/batches", { method: "POST", ...json(body) })).json();
  },
  async deleteBatch(id) {
    return (await request(`/api/batches/${id}`, { method: "DELETE" })).json();
  },
  async purgeExpired() {
    return (await request("/api/batches/purge-expired", { method: "POST" })).json();
  },
  async health() {
    return (await request("/api/health")).json();
  },
};
