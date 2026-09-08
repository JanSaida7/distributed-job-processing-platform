import { useCallback, useEffect, useState } from "react";
import { ApiError, api } from "./api";

const TOKEN_KEY = "job-platform-token";
const emptyJob = { name: "", payload: "", idempotencyKey: "" };

function messageFor(error) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

function AuthScreen({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", fullName: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "register") {
        await api.register({ email: form.email, password: form.password, full_name: form.fullName || null });
      }
      const token = await api.login({ email: form.email, password: form.password });
      onAuthenticated(token.access_token);
    } catch (requestError) {
      setError(messageFor(requestError));
    } finally {
      setBusy(false);
    }
  }

  return <main className="auth-shell"><section className="auth-card">
    <p className="eyebrow">Distributed job processing</p>
    <h1>{mode === "login" ? "Welcome back" : "Create your account"}</h1>
    <p className="muted">Submit work and follow its progress from one place.</p>
    <form onSubmit={submit}>
      {mode === "register" && <label>Full name<input value={form.fullName} onChange={(e) => setForm({ ...form, fullName: e.target.value })} /></label>}
      <label>Email<input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
      <label>Password<input type="password" required minLength="8" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>
      {error && <p className="error" role="alert">{error}</p>}
      <button disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}</button>
    </form>
    <button className="link-button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>
      {mode === "login" ? "Need an account? Register" : "Already have an account? Sign in"}
    </button>
  </section></main>;
}

function JobForm({ token, onCreated }) {
  const [form, setForm] = useState(emptyJob);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault();
    let payload;
    try { payload = form.payload.trim() ? JSON.parse(form.payload) : null; } catch { setError("Payload must be valid JSON."); return; }
    setBusy(true); setError("");
    try {
      await api.createJob({ name: form.name, payload, idempotency_key: form.idempotencyKey || null }, token);
      setForm(emptyJob); onCreated();
    } catch (requestError) { setError(messageFor(requestError)); } finally { setBusy(false); }
  }
  return <section className="panel"><h2>Submit a job</h2><form className="job-form" onSubmit={submit}>
    <label>Job name<input required maxLength="255" placeholder="e.g. calculate-total" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
    <label>Payload (JSON)<textarea rows="4" placeholder={'{"task":"sum","values":[1,2,3]}'} value={form.payload} onChange={(e) => setForm({ ...form, payload: e.target.value })} /></label>
    <label>Idempotency key <span className="muted">(optional)</span><input maxLength="255" placeholder="one-time-request-id" value={form.idempotencyKey} onChange={(e) => setForm({ ...form, idempotencyKey: e.target.value })} /></label>
    {error && <p className="error" role="alert">{error}</p>}<button disabled={busy}>{busy ? "Submitting…" : "Submit job"}</button>
  </form></section>;
}

function JobDetails({ job, token, onAction }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  if (!job) return <section className="panel detail empty"><p>Select a job to view its details.</p></section>;
  const cancellable = !["completed", "cancelled", "dead_letter"].includes(job.status);
  const retryable = ["failed", "dead_letter"].includes(job.status);
  async function action(fn) { setBusy(true); setError(""); try { await fn(job.id, token); await onAction(); } catch (e) { setError(messageFor(e)); } finally { setBusy(false); } }
  return <section className="panel detail"><div className="detail-heading"><div><p className="eyebrow">Job #{job.id}</p><h2>{job.name}</h2></div><span className={`status ${job.status}`}>{job.status.replace("_", " ")}</span></div>
    <dl><dt>Version</dt><dd>{job.version}</dd><dt>Created</dt><dd>{new Date(job.created_at).toLocaleString()}</dd><dt>Started</dt><dd>{job.started_at ? new Date(job.started_at).toLocaleString() : "—"}</dd><dt>Finished</dt><dd>{job.finished_at ? new Date(job.finished_at).toLocaleString() : "—"}</dd></dl>
    {job.error_message && <p className="error">{job.error_message}</p>}
    <DataBlock label="Payload" value={job.payload} /><DataBlock label="Result" value={job.result} />
    <div className="actions">{cancellable && <button className="secondary" disabled={busy} onClick={() => action(api.cancelJob)}>Cancel</button>}{retryable && <button disabled={busy} onClick={() => action(api.retryJob)}>Retry</button>}</div>{error && <p className="error">{error}</p>}
  </section>;
}

function DataBlock({ label, value }) { return <div className="data-block"><h3>{label}</h3><pre>{value == null ? "—" : typeof value === "string" ? value : JSON.stringify(value, null, 2)}</pre></div>; }

function Dashboard({ token, onLogout }) {
  const [jobs, setJobs] = useState([]); const [selectedId, setSelectedId] = useState(null); const [filter, setFilter] = useState("all"); const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  const loadJobs = useCallback(async () => { try { setError(""); setLoading(true); const data = filter === "failed" ? await api.listFailedJobs(token) : filter === "dead_letter" ? await api.listDeadLetterJobs(token) : await api.listJobs(token); setJobs(data); setSelectedId((current) => data.some((job) => job.id === current) ? current : data[0]?.id ?? null); } catch (e) { if (e instanceof ApiError && e.status === 401) onLogout(); else setError(messageFor(e)); } finally { setLoading(false); } }, [filter, onLogout, token]);
  useEffect(() => { loadJobs(); const poller = window.setInterval(loadJobs, 5000); return () => window.clearInterval(poller); }, [loadJobs]);
  const selectedJob = jobs.find((job) => job.id === selectedId);
  return <main className="dashboard"><header><div><p className="eyebrow">Phase 9 dashboard</p><h1>Jobs</h1></div><div className="header-actions"><span className="muted">Updates every 5 seconds</span><button className="secondary" onClick={onLogout}>Sign out</button></div></header>
    <JobForm token={token} onCreated={loadJobs} />
    <section className="workspace"><section className="panel jobs-panel"><div className="toolbar"><h2>Job queue</h2><select aria-label="Filter jobs" value={filter} onChange={(e) => setFilter(e.target.value)}><option value="all">All jobs</option><option value="failed">Failed</option><option value="dead_letter">Dead letter</option></select></div>{error && <p className="error">{error}</p>}{loading ? <p className="muted">Loading jobs…</p> : jobs.length === 0 ? <p className="muted">No jobs in this view yet.</p> : <ul className="job-list">{jobs.map((job) => <li key={job.id}><button className={job.id === selectedId ? "job-row selected" : "job-row"} onClick={() => setSelectedId(job.id)}><span><strong>{job.name}</strong><small>#{job.id} · v{job.version}</small></span><span className={`status ${job.status}`}>{job.status.replace("_", " ")}</span></button></li>)}</ul>}</section><JobDetails job={selectedJob} token={token} onAction={loadJobs} /></section>
  </main>;
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  function authenticate(value) { localStorage.setItem(TOKEN_KEY, value); setToken(value); }
  function logout() { localStorage.removeItem(TOKEN_KEY); setToken(null); }
  return token ? <Dashboard token={token} onLogout={logout} /> : <AuthScreen onAuthenticated={authenticate} />;
}
