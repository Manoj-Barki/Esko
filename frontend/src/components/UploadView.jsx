import React, { useEffect, useRef, useState } from "react";
import { api } from "../api.js";

const ACCEPT = ".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg";
const MAX_MB = 25;

function num(v) { return v === "" || v == null ? undefined : Number(v); }

export default function UploadView({ onDone }) {
  const [file, setFile] = useState(null);
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [batches, setBatches] = useState([]);
  const [batchId, setBatchId] = useState("");
  const [rules, setRules] = useState({
    min_dpi_warning: "", min_dpi_critical: "", min_clearance_mm: "",
    safe_margin_mm: "", image_target_width_mm: "", dieline_colors: "",
  });
  const input = useRef(null);

  useEffect(() => { api.listBatches().then(setBatches).catch(() => {}); }, []);

  function pick(f) {
    setError("");
    if (!f) return;
    if (!/\.(pdf|png|jpe?g)$/i.test(f.name)) return setError("Only PDF, PNG and JPEG files are accepted.");
    if (f.size > MAX_MB * 1024 * 1024) return setError(`File is larger than ${MAX_MB} MB.`);
    setFile(f);
  }

  function buildConfig() {
    const cfg = {};
    for (const k of ["min_dpi_warning", "min_dpi_critical", "min_clearance_mm", "safe_margin_mm", "image_target_width_mm"]) {
      const v = num(rules[k]);
      if (v !== undefined && !Number.isNaN(v)) cfg[k] = v;
    }
    if (rules.dieline_colors.trim()) {
      // "1,0,0.5; 0,0,0" -> [[1,0,0.5],[0,0,0]]
      const cols = rules.dieline_colors.split(";").map((s) => s.split(",").map((n) => Number(n.trim())));
      if (cols.some((c) => c.length !== 3 || c.some((n) => Number.isNaN(n) || n < 0 || n > 1)))
        throw new Error("Dieline colours: use RGB values from 0 to 1, e.g. 1,0,0; 0,0,1");
      cfg.dieline_colors = cols;
    }
    return cfg;
  }

  async function run() {
    setError("");
    let cfg;
    try { cfg = buildConfig(); } catch (e) { return setError(e.message); }
    setBusy(true);
    try {
      onDone(await api.inspect(file, cfg, batchId));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const set = (k) => (e) => setRules({ ...rules, [k]: e.target.value });

  return (
    <div className="upload">
      <h1>Check your dieline before it goes to press</h1>
      <p className="lede">Upload a PDF, PNG or JPEG. PrintGuard looks for low-resolution images, text too close to cut and fold lines, and text outside the safe area, and shows you where each one is.</p>

      <div
        className={`drop ${drag ? "drag" : ""} ${file ? "has" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]); }}
        onClick={() => input.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && input.current?.click()}
        role="button" tabIndex={0}
        aria-label="Choose a file to inspect"
      >
        <input ref={input} type="file" accept={ACCEPT} hidden onChange={(e) => pick(e.target.files[0])} />
        {file ? (
          <>
            <strong>{file.name}</strong>
            <span>{(file.size / 1024 / 1024).toFixed(2)} MB. Click to choose a different file.</span>
          </>
        ) : (
          <>
            <strong>Drop a file here, or click to browse</strong>
            <span>PDF, PNG or JPEG, up to {MAX_MB} MB</span>
          </>
        )}
      </div>

      <details className="rules">
        <summary>Rules for this inspection <em>(optional, leave blank to use defaults)</em></summary>
        <div className="grid">
          <label>Warn below (DPI)<input type="number" min="1" placeholder="150" value={rules.min_dpi_warning} onChange={set("min_dpi_warning")} /></label>
          <label>Critical below (DPI)<input type="number" min="1" placeholder="72" value={rules.min_dpi_critical} onChange={set("min_dpi_critical")} /></label>
          <label>Text clearance from cut/fold (mm)<input type="number" step="0.1" min="0" placeholder="3.0" value={rules.min_clearance_mm} onChange={set("min_clearance_mm")} /></label>
          <label>Safe margin from page edge (mm)<input type="number" step="0.1" min="0" placeholder="3.0" value={rules.safe_margin_mm} onChange={set("safe_margin_mm")} /></label>
          <label>Printed width for PNG/JPEG (mm)<input type="number" step="1" min="1" placeholder="Needed to measure DPI" value={rules.image_target_width_mm} onChange={set("image_target_width_mm")} /></label>
          <label>Dieline stroke colours (RGB 0–1)<input type="text" placeholder="1,0,0; 0,0,1" value={rules.dieline_colors} onChange={set("dieline_colors")} /></label>
        </div>
        <p className="hint">Without a dieline colour, dashed lines are treated as probable folds and those findings are marked "needs review". Raster uploads get a preview only; geometry checks need a PDF with vector paths.</p>
      </details>

      {batches.length > 0 && (
        <label className="batchpick">Link to batch
          <select value={batchId} onChange={(e) => setBatchId(e.target.value)}>
            <option value="">No batch</option>
            {batches.filter((b) => !b.expired).map((b) => (
              <option key={b.id} value={b.id}>{b.batch_number}{b.product_name ? `: ${b.product_name}` : ""} (expires {b.expiry_date})</option>
            ))}
          </select>
          <span className="hint">Inspections linked to a batch are deleted automatically after the batch expires.</span>
        </label>
      )}

      {error && <div className="banner err" role="alert">{error}</div>}
      <button className="primary" disabled={!file || busy} onClick={run}>
        {busy ? "Inspecting…" : "Run inspection"}
      </button>
    </div>
  );
}
