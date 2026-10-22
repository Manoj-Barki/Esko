import React, { useMemo, useState } from "react";
import { api } from "../api.js";

const SEV_LABEL = { critical: "Critical", warning: "Warning", info: "Info" };
const STATUS_LABEL = { confirmed: "Confirmed", needs_review: "Needs review", false_positive: "False positive", resolved: "Resolved" };
const CHECK_LABEL = { passed: "Passed", failed: "Failed", skipped: "Skipped", unavailable: "Unavailable" };

export default function ResultView({ result, onChange, onNew }) {
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState(null);
  const [sev, setSev] = useState("all");
  const [hideDismissed, setHideDismissed] = useState(true);
  const [error, setError] = useState("");

  const pageInfo = result.pages.find((p) => p.number === page) || result.pages[0];
  const inactive = (f) => f.status === "false_positive" || f.status === "resolved";

  const visible = useMemo(
    () => result.findings.filter((f) => (sev === "all" || f.severity === sev) && !(hideDismissed && inactive(f))),
    [result, sev, hideDismissed]
  );
  const onPage = visible.filter((f) => f.page === page);
  const by = result.summary?.by_severity || {};
  const checks = result.summary?.checks || {};
  const active = result.findings.filter((f) => !inactive(f));

  async function setStatus(f, status) {
    setError("");
    try { onChange(await api.setFindingStatus(result.id, f.id, status)); }
    catch (e) { setError(e.message); }
  }

  function pick(f) {
    setSelected(f.id);
    setPage(f.page);
    document.getElementById(`finding-${f.id}`)?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  return (
    <div className="result">
      <div className="result-head">
        <div>
          <h1 className="fname">{result.file.filename}</h1>
          <p className="meta">
            {result.file.kind.toUpperCase()}, {result.file.page_count} page{result.file.page_count > 1 ? "s" : ""},{" "}
            {(result.file.size_bytes / 1024 / 1024).toFixed(2)} MB, inspected in {result.duration_ms} ms
          </p>
        </div>
        <div className="actions">
          <a className="btn" href={api.reportUrl(result.id)} download>Download report</a>
          <button onClick={onNew}>Inspect another file</button>
        </div>
      </div>

      <section className="stats" aria-label="Summary">
        <div className={`stat crit ${by.critical ? "hot" : ""}`}><b>{by.critical || 0}</b><span>Critical</span></div>
        <div className={`stat warn ${by.warning ? "hot" : ""}`}><b>{by.warning || 0}</b><span>Warnings</span></div>
        <div className="stat info"><b>{by.info || 0}</b><span>Info</span></div>
        <div className="stat checks">
          <span>
            {checks.passed || 0} passed, {checks.failed || 0} failed
            {(checks.unavailable || 0) + (checks.skipped || 0) > 0 && <>, <strong>{(checks.unavailable || 0) + (checks.skipped || 0)} could not run</strong></>}
          </span>
        </div>
      </section>

      {!result.file.physical_size_known && (
        <div className="banner warn">This file has no physical size, so resolution (DPI) could not be measured. Set a printed width under "Rules for this inspection" to enable that check.</div>
      )}
      {error && <div className="banner err" role="alert">{error}</div>}

      <div className="split">
        <section className="viewer" aria-label="Page preview">
          {result.pages.length > 1 && (
            <div className="pager">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)} aria-label="Previous page">‹</button>
              <span>Page {page} of {result.pages.length}</span>
              <button disabled={page >= result.pages.length} onClick={() => setPage(page + 1)} aria-label="Next page">›</button>
            </div>
          )}
          <div className="sheet">
            {pageInfo?.preview_url && <img src={api.url(pageInfo.preview_url)} alt={`Preview of page ${page}`} draggable="false" />}
            {onPage.map((f) => {
              const [x, y, w, h] = f.bbox;
              return (
                <button
                  key={f.id}
                  className={`box ${f.severity} ${selected === f.id ? "sel" : ""} ${inactive(f) ? "dim" : ""}`}
                  style={{ left: `${x * 100}%`, top: `${y * 100}%`, width: `${w * 100}%`, height: `${h * 100}%` }}
                  onClick={() => pick(f)}
                  aria-label={`${f.id}: ${f.title}`}
                  title={`${f.id}: ${f.title}`}
                />
              );
            })}
          </div>
          <p className="hint">Boxes mark where each finding is. Select one to see its details.</p>
        </section>

        <section className="findings" aria-label="Findings">
          <div className="filters">
            <div role="group" aria-label="Filter by severity">
              {["all", "critical", "warning", "info"].map((s) => (
                <button key={s} className={sev === s ? "on" : ""} onClick={() => setSev(s)}>{s === "all" ? "All" : SEV_LABEL[s]}</button>
              ))}
            </div>
            <label className="check"><input type="checkbox" checked={hideDismissed} onChange={(e) => setHideDismissed(e.target.checked)} /> Hide dismissed</label>
          </div>

          {active.length === 0 && (
            <div className="empty">
              <strong>No open findings.</strong>
              <span>{(checks.unavailable || 0) + (checks.skipped || 0) > 0
                ? "Some checks could not run (see below), so this is not a full pass."
                : "The checks that ran found nothing to flag. Confirm against your printer's spec before approving."}</span>
            </div>
          )}

          <ul>
            {visible.map((f) => (
              <li key={f.id} id={`finding-${f.id}`} className={`finding ${f.severity} ${selected === f.id ? "sel" : ""} ${inactive(f) ? "dim" : ""}`}>
                <button className="fhead" onClick={() => pick(f)} aria-expanded={selected === f.id}>
                  <span className={`pill ${f.severity}`}>{SEV_LABEL[f.severity]}</span>
                  <span className="ftitle">{f.title}</span>
                  <span className="fid">{f.id}, p.{f.page}</span>
                </button>
                {selected === f.id && (
                  <div className="fbody">
                    <dl>
                      <dt>Observed</dt><dd>{f.observed}</dd>
                      <dt>Expected</dt><dd>{f.expected}</dd>
                    </dl>
                    <p>{f.explanation}</p>
                    <p className="rec"><strong>What to do:</strong> {f.recommendation}</p>
                    <p className="ev">
                      Rule {f.rule_id}. {STATUS_LABEL[f.status]}, {Math.round(f.confidence * 100)}% confidence. Source: {f.evidence.source}
                      {Object.keys(f.evidence.measurements || {}).length > 0 && (
                        <> ({Object.entries(f.evidence.measurements).filter(([, v]) => v != null).map(([k, v]) => `${k.replace(/_/g, " ")}: ${v}`).join(", ")})</>
                      )}
                    </p>
                    <div className="row">
                      {f.status === "false_positive" || f.status === "resolved"
                        ? <button onClick={() => setStatus(f, "confirmed")}>Reopen</button>
                        : <>
                            <button onClick={() => setStatus(f, "resolved")}>Mark resolved</button>
                            <button onClick={() => setStatus(f, "false_positive")}>Mark false positive</button>
                          </>}
                    </div>
                  </div>
                )}
              </li>
            ))}
          </ul>

          <h2>Checks</h2>
          <ul className="checks-list">
            {result.checks.map((c) => (
              <li key={c.rule_id}>
                <span className={`cs ${c.status}`}>{CHECK_LABEL[c.status]}</span>
                <span><strong>{c.rule_id}</strong> {c.name}{c.detail && <em>{c.detail}</em>}</span>
              </li>
            ))}
          </ul>
          <p className="hint">{result.disclaimer}</p>
        </section>
      </div>
    </div>
  );
}
