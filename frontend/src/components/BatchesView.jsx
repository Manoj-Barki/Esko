import React, { useEffect, useState } from "react";
import { api } from "../api.js";

const today = () => new Date().toISOString().slice(0, 10);

export default function BatchesView({ onOpen }) {
  const [batches, setBatches] = useState(null);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");
  const [mode, setMode] = useState("shelf");
  const [form, setForm] = useState({ batch_number: "", product_name: "", mfg_date: today(), expiry_date: "", shelf_life_days: "" });

  const load = () => api.listBatches().then(setBatches).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function create(e) {
    e.preventDefault();
    setError(""); setNote("");
    const body = { batch_number: form.batch_number.trim(), mfg_date: form.mfg_date };
    if (form.product_name.trim()) body.product_name = form.product_name.trim();
    if (mode === "shelf") body.shelf_life_days = Number(form.shelf_life_days);
    else body.expiry_date = form.expiry_date;
    try {
      await api.createBatch(body);
      setForm({ ...form, batch_number: "", product_name: "", expiry_date: "", shelf_life_days: "" });
      load();
    } catch (err) { setError(err.message); }
  }

  async function remove(b) {
    const n = b.inspection_ids.length;
    if (!confirm(`Delete batch ${b.batch_number}${n ? ` and its ${n} linked inspection${n > 1 ? "s" : ""}` : ""}? This is permanent.`)) return;
    try { await api.deleteBatch(b.id); load(); } catch (err) { setError(err.message); }
  }

  async function purge() {
    setError(""); setNote("");
    try {
      const { purged_batches } = await api.purgeExpired();
      setNote(purged_batches ? `Deleted ${purged_batches} expired batch${purged_batches > 1 ? "es" : ""}.` : "No expired batches to delete.");
      load();
    } catch (err) { setError(err.message); }
  }

  const expiredCount = (batches || []).filter((b) => b.expired).length;

  return (
    <div className="batches">
      <h1>Batches</h1>
      <p className="lede">Track products by batch. When a batch's expiry date has passed, the batch and every inspection linked to it (uploaded file, previews, results) is deleted automatically the next day.</p>

      <form className="card" onSubmit={create}>
        <div className="grid">
          <label>Batch number<input required maxLength={64} value={form.batch_number} onChange={set("batch_number")} placeholder="B-101" /></label>
          <label>Product name <em>(optional)</em><input maxLength={200} value={form.product_name} onChange={set("product_name")} /></label>
          <label>Manufactured<input required type="date" value={form.mfg_date} onChange={set("mfg_date")} /></label>
          {mode === "shelf"
            ? <label>Shelf life (days)<input required type="number" min="1" max="36500" value={form.shelf_life_days} onChange={set("shelf_life_days")} /></label>
            : <label>Expiry date<input required type="date" min={form.mfg_date} value={form.expiry_date} onChange={set("expiry_date")} /></label>}
        </div>
        <div className="row">
          <button type="submit" className="primary">Create batch</button>
          <button type="button" className="link" onClick={() => setMode(mode === "shelf" ? "date" : "shelf")}>
            {mode === "shelf" ? "Enter an expiry date instead" : "Use shelf life instead"}
          </button>
        </div>
      </form>

      {error && <div className="banner err" role="alert">{error}</div>}
      {note && <div className="banner ok" role="status">{note}</div>}

      <div className="row between">
        <h2>All batches</h2>
        <button onClick={purge} disabled={!expiredCount} title="Permanently deletes expired batches and their inspections">
          Delete expired now{expiredCount ? ` (${expiredCount})` : ""}
        </button>
      </div>

      {batches === null ? <p>Loading…</p> : batches.length === 0 ? (
        <div className="empty"><strong>No batches yet.</strong><span>Create one above, then link inspections to it when you upload a file.</span></div>
      ) : (
        <div className="tablewrap">
          <table>
            <thead><tr><th>Batch</th><th>Product</th><th>Manufactured</th><th>Expires</th><th>Inspections</th><th></th></tr></thead>
            <tbody>
              {batches.map((b) => (
                <tr key={b.id} className={b.expired ? "expired" : ""}>
                  <td><strong>{b.batch_number}</strong></td>
                  <td>{b.product_name || "–"}</td>
                  <td>{b.mfg_date}</td>
                  <td>{b.expiry_date}{b.expired && <span className="pill critical">Expired</span>}</td>
                  <td>
                    {b.inspection_ids.length === 0 ? "–" : b.inspection_ids.map((id) => (
                      <button key={id} className="link" onClick={() => onOpen(id).catch?.(() => {})}>{id.slice(0, 6)}</button>
                    ))}
                  </td>
                  <td><button className="danger" onClick={() => remove(b)}>Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
