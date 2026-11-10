import React, { useEffect, useRef, useState } from "react";
import { api } from "../api.js";

const ACCEPT = ".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg";
const MAX_MB = 25;

function num(v) { return v === "" || v == null ? undefined : Number(v); }

export default function UploadView({ onDone }) {
  const [files, setFiles] = useState([]);
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [batches, setBatches] = useState([]);
  const [batchId, setBatchId] = useState("");
  const [uploadProgress, setUploadProgress] = useState({});
  const [rules, setRules] = useState({
    min_dpi_warning: "", min_dpi_critical: "", min_clearance_mm: "",
    safe_margin_mm: "", image_target_width_mm: "", dieline_colors: "",
  });
  const input = useRef(null);

  useEffect(() => { api.listBatches().then(setBatches).catch(() => {}); }, []);

  function validateFile(f) {
    if (!/\.(pdf|png|jpe?g)$/i.test(f.name)) {
      return `${f.name}: Only PDF, PNG and JPEG files are accepted.`;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      return `${f.name}: File is larger than ${MAX_MB} MB.`;
    }
    return null;
  }

  function pick(fileList) {
    setError("");
    if (!fileList || fileList.length === 0) return;

    const newFiles = Array.from(fileList);
    const errors = [];
    const validFiles = [];

    newFiles.forEach(f => {
      const err = validateFile(f);
      if (err) {
        errors.push(err);
      } else {
        validFiles.push(f);
      }
    });

    if (errors.length > 0) {
      setError(errors.join(" "));
    }

    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles]);
    }
  }

  function removeFile(index) {
    setFiles(files.filter((_, i) => i !== index));
    setError("");
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
    setUploadProgress({});

    try {
      const results = [];
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        setUploadProgress(prev => ({ ...prev, [i]: { name: file.name, status: 'uploading', progress: 0 } }));

        try {
          const result = await api.inspect(file, cfg, batchId);
          results.push(result);
          setUploadProgress(prev => ({ ...prev, [i]: { name: file.name, status: 'completed', progress: 100, result } }));
        } catch (e) {
          setUploadProgress(prev => ({ ...prev, [i]: { name: file.name, status: 'error', progress: 0, error: e.message } }));
        }
      }

      if (results.length === 1) {
        onDone(results[0]);
      } else if (results.length > 1) {
        // For now, show the first result. Can be enhanced for batch view
        onDone(results[0]);
      }
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
      <p className="lede">Upload PDF, PNG or JPEG files. PrintGuard looks for low-resolution images, text too close to cut and fold lines, and text outside the safe area, and shows you where each one is.</p>

      <div
        className={`drop ${drag ? "drag" : ""} ${files.length > 0 ? "has" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files); }}
        onClick={() => input.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && input.current?.click()}
        role="button" tabIndex={0}
        aria-label="Choose files to inspect"
      >
        <input ref={input} type="file" accept={ACCEPT} multiple hidden onChange={(e) => pick(e.target.files)} />
        {files.length > 0 ? (
          <>
            <strong>{files.length} file{files.length > 1 ? 's' : ''} selected</strong>
            <span>Click to add more files</span>
          </>
        ) : (
          <>
            <strong>Drop files here, or click to browse</strong>
            <span>PDF, PNG or JPEG, up to {MAX_MB} MB each. Multiple files supported.</span>
          </>
        )}
      </div>

      {files.length > 0 && (
        <div className="file-list">
          <h2>Selected Files</h2>
          <ul>
            {files.map((file, i) => (
              <li key={i} className="file-item">
                <div className="file-info">
                  <strong>{file.name}</strong>
                  <span className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                </div>
                <button type="button" onClick={() => removeFile(i)} disabled={busy} aria-label={`Remove ${file.name}`}>
                  ✕
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {Object.keys(uploadProgress).length > 0 && (
        <div className="upload-progress">
          <h2>Upload Progress</h2>
          {Object.entries(uploadProgress).map(([index, prog]) => (
            <div key={index} className={`progress-item ${prog.status}`}>
              <div className="progress-header">
                <strong>{prog.name}</strong>
                <span className={`status-badge ${prog.status}`}>
                  {prog.status === 'uploading' ? '⏳ Uploading...' :
                   prog.status === 'completed' ? '✓ Completed' :
                   prog.status === 'error' ? '✗ Error' : ''}
                </span>
              </div>
              {prog.status === 'error' && <div className="error-msg">{prog.error}</div>}
              {prog.status === 'completed' && prog.result && (
                <button
                  className="link"
                  onClick={() => onDone(prog.result)}
                >
                  View results
                </button>
              )}
            </div>
          ))}
        </div>
      )}

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
      <button className="primary" disabled={files.length === 0 || busy} onClick={run}>
        {busy ? `Inspecting ${files.length} file${files.length > 1 ? 's' : ''}...` : `Run inspection${files.length > 1 ? 's' : ''}`}
      </button>
    </div>
  );
}
