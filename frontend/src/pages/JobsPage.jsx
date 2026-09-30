import { useEffect, useState } from "react";
import { ArrowRight, BriefcaseBusiness, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import workspaceService from "../services/workspaceService";
import { usePreferences } from "../context/PreferencesContext";

function JobsPage() {
  const [description, setDescription] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [jobs, setJobs] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const { t } = usePreferences();

  async function loadJobs() {
    try {
      const { data } = await workspaceService.getJobs();
      if (!Array.isArray(data)) throw new Error("Jobs API returned an unexpected response.");
      setJobs(data);
    }
    catch (err) { setError(err.response?.data?.detail || "İlanlar yüklenemedi."); }
  }
  useEffect(() => { loadJobs(); }, []);

  async function analyze(event) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      const { data } = await workspaceService.analyzeAndSaveJob(description, jobUrl);
      setMessage(`İlan analiz edildi ve kaydedildi. Job #${data.job_id}`);
      setDescription(""); setJobUrl(""); await loadJobs();
    } catch (err) { setError(err.response?.data?.detail || "İlan analiz edilemedi."); }
    finally { setBusy(false); }
  }

  return <div className="workspace-page">
    <div className="page-heading"><div><p className="eyebrow">FIRSATLAR</p><h1>{t("Jobs")}</h1><p>{t("İlan metnini ekleyin; JobPilot gereksinimleri analiz edip kaydetsin.")}</p></div></div>
    {(error || message) && <div className={`api-message${error ? " error" : " success"}`}>{error || message}</div>}
    <section className="panel workspace-panel job-form-panel">
      <div className="panel-header"><div><h2>{t("Add a job")}</h2><p>{t("URL ve tam ilan metni ile başlayın")}</p></div><div className="stat-icon"><Sparkles size={20}/></div></div>
      <form className="job-form" onSubmit={analyze}>
        <label>{t("Job URL")} <span className="optional-label">{t("Optional")}</span><input type="url" value={jobUrl} onChange={(e) => setJobUrl(e.target.value)} placeholder="https://company.com/careers/role"/></label>
        <label>{t("Job description")}<textarea required minLength={50} rows={8} value={description} onChange={(e) => setDescription(e.target.value)} placeholder={t("İlanın tam metnini buraya yapıştırın…")}/></label>
        <div className="form-footer"><small>{t("AI analizi için en az 50 karakter girin.")}</small><button className="primary-button" disabled={busy || description.trim().length < 50}><Sparkles size={16}/>{busy ? t("Analyzing…") : t("Analyze & save")}</button></div>
      </form>
    </section>
    <section className="panel jobs-list-panel">
      <div className="panel-header"><div><h2>{t("Saved jobs")}</h2><p>{jobs.length} {t("ilan")}</p></div></div>
      {jobs.length ? <div className="saved-jobs">{jobs.map((job) => <article className="saved-job" key={job.id}><span className="job-icon"><BriefcaseBusiness size={19}/></span><div className="saved-job-info"><strong>{job.position}</strong><span>{job.company}{job.location ? ` · ${job.location}` : ""}</span><small>Job #{job.id} · {job.status}</small></div>{job.status === "ANALYZED" && <Link className="text-link" to={`/applications?jobId=${job.id}`}>{t("Create application")} <ArrowRight size={15}/></Link>}</article>)}</div> : <div className="empty-state">{t("Henüz ilan yok. İlk ilanı yukarıdan ekleyin.")}</div>}
    </section>
  </div>;
}

export default JobsPage;
