import React, { useEffect, useState } from "react";
import { api } from "./api.js";
import UploadView from "./components/UploadView.jsx";
import ResultView from "./components/ResultView.jsx";
import BatchesView from "./components/BatchesView.jsx";

export default function App() {
  const [tab, setTab] = useState("inspect");
  const [result, setResult] = useState(null);
  const [online, setOnline] = useState(null);

  useEffect(() => {
    api.health().then(() => setOnline(true)).catch(() => setOnline(false));
  }, []);

  function show(r) { setResult(r); setTab("inspect"); }

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true">
            <rect x="5" y="5" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeDasharray="3 2" />
            <path d="M13 0v7M13 19v7M0 13h7M19 13h7" stroke="currentColor" strokeWidth="1.6" />
            <circle cx="13" cy="13" r="3" fill="var(--magenta)" />
          </svg>
          <span>PrintGuard</span>
        </div>
        <nav aria-label="Main">
          <button className={tab === "inspect" ? "on" : ""} onClick={() => setTab("inspect")}>Inspect</button>
          <button className={tab === "batches" ? "on" : ""} onClick={() => setTab("batches")}>Batches</button>
        </nav>
        <span className={`conn ${online === false ? "down" : online ? "up" : ""}`} role="status">
          {online === null ? "Connecting…" : online ? "Backend connected" : "Backend not reachable"}
        </span>
      </header>

      <main>
        {online === false && (
          <div className="banner err">
            Can't reach the API. Start it with <code>uvicorn main:app --reload --port 8000</code> in the backend folder, then reload.
          </div>
        )}
        {tab === "inspect" && (
          result
            ? <ResultView result={result} onChange={setResult} onNew={() => setResult(null)} />
            : <UploadView onDone={show} />
        )}
        {tab === "batches" && <BatchesView onOpen={(id) => api.getInspection(id).then(show)} />}
      </main>

      <footer>Automated screening aid, not a certification that artwork is print-ready. Confirm against your printer's specification.</footer>
    </div>
  );
}
