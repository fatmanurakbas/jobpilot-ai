import { useEffect, useState } from "react";
import { FileUp, RefreshCw, UserRound } from "lucide-react";
import workspaceService from "../services/workspaceService";
import { usePreferences } from "../context/PreferencesContext";

const PROFILE_KEY = "jobpilot.candidateProfile";
const FILENAME_KEY = "jobpilot.masterCvFilename";

function readSavedProfile() {
  try {
    const saved = localStorage.getItem(PROFILE_KEY);
    return saved && saved !== "undefined" ? JSON.parse(saved) : null;
  } catch {
    return null;
  }
}

function CandidatePage() {
  const [profile, setProfile] = useState(readSavedProfile);
  const [filename, setFilename] = useState(() => localStorage.getItem(FILENAME_KEY) || "");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const { t } = usePreferences();

  useEffect(() => {
    workspaceService.getCandidate().then(({ data }) => {
      if (!data) return;
      setProfile(data.profile);
      setFilename(data.master_cv_filename || "");
      localStorage.setItem("jobpilot.candidateId", String(data.id));
      localStorage.setItem(PROFILE_KEY, JSON.stringify(data.profile));
      localStorage.setItem(FILENAME_KEY, data.master_cv_filename || "");
    }).catch(() => {});
  }, []);

  async function upload(file) {
    if (!file) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const { data } = await workspaceService.uploadCv(file);
      setProfile(data.profile); setFilename(data.master_cv_filename || file.name);
      if (data.id) localStorage.setItem("jobpilot.candidateId", String(data.id));
      localStorage.setItem(PROFILE_KEY, JSON.stringify(data.profile));
      localStorage.setItem(FILENAME_KEY, file.name);
      setMessage("CV yüklendi ve profil bilgileri çıkarıldı.");
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : err.message || "CV yüklenemedi. API bağlantınızı ve PDF/DOCX dosyasını kontrol edin.");
    } finally { setBusy(false); }
  }

  return <div className="workspace-page">
    <div className="page-heading"><div><p className="eyebrow">ADAY</p><h1>{t("Candidate profile")}</h1><p>{t("Master CV’nizi yükleyin ve AI tarafından çıkarılan profili inceleyin.")}</p></div></div>
    {(message || error) && <div className={`api-message${error ? " error" : " success"}`}>{error || message}</div>}
    <div className="workspace-grid">
      <section className="panel workspace-panel">
        <div className="panel-header"><div><h2>{t("Master CV")}</h2><p>{t("PDF veya DOCX, önerilen boyut 10 MB altında")}</p></div><div className="stat-icon"><FileUp size={20}/></div></div>
        <label className="upload-dropzone">
          <input type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={(e) => upload(e.target.files?.[0])} disabled={busy}/>
          <span className="upload-icon"><FileUp size={22}/></span>
          <strong>{busy ? t("CV işleniyor…") : filename || t("CV dosyası seçin veya buraya bırakın")}</strong>
          <small>{t("Dosya yüklendiğinde profil otomatik olarak analiz edilir.")}</small>
          <span className="secondary-button"><RefreshCw size={15}/>{filename ? t("CV değiştir") : t("CV yükle")}</span>
        </label>
      </section>
      <section className="panel workspace-panel">
        <div className="panel-header"><div><h2>{t("Parsed Profile")}</h2><p>{t("Master CV’den çıkarılan bilgiler")}</p></div><div className="stat-icon"><UserRound size={20}/></div></div>
        {profile ? <ProfileView profile={profile} t={t}/> : <div className="empty-state">{t("Profilinizi görmek için önce master CV yükleyin.")}</div>}
      </section>
    </div>
  </div>;
}

function ProfileView({ profile, t }) {
  const fields = [["Name", profile.full_name], ["Email", profile.email], ["Phone", profile.phone], ["LinkedIn", profile.linkedin], ["GitHub", profile.github], ["Portfolio", profile.portfolio], ["CV language", profile.cv_language]];
  return <div className="profile-view">
    <div className="profile-fields">{fields.filter(([, value]) => value).map(([label, value]) => <div className="profile-field" key={label}><small>{t(label)}</small><span>{value}</span></div>)}</div>
    {profile.summary && <div className="profile-section"><h3>{t("Summary")}</h3><p>{profile.summary}</p></div>}
    {profile.skills?.length > 0 && <div className="profile-section"><h3>{t("Skills")}</h3><div className="tag-list">{profile.skills.map((skill) => <span className="skill-tag" key={skill}>{skill}</span>)}</div></div>}
    {profile.experiences?.length > 0 && <div className="profile-section"><h3>{t("Experience")}</h3>{profile.experiences.map((item, i) => <div className="profile-entry" key={`${item.title}-${i}`}><strong>{item.title}</strong>{item.organization && <span>{item.organization}</span>}<ul>{item.description?.map((line, j) => <li key={j}>{line}</li>)}</ul></div>)}</div>}
    {profile.education?.length > 0 && <div className="profile-section"><h3>{t("Education")}</h3>{profile.education.map((item, i) => <div className="profile-entry" key={`${item.institution}-${i}`}><strong>{item.institution}</strong><span>{[item.degree, item.department, item.graduation_year].filter(Boolean).join(" · ")}</span></div>)}</div>}
    {profile.projects?.length > 0 && <div className="profile-section"><h3>{t("Projects")}</h3>{profile.projects.map((item, i) => <div className="profile-entry" key={`${item.name}-${i}`}><strong>{item.name}</strong>{item.technologies?.length > 0 && <span>{item.technologies.join(" · ")}</span>}<ul>{item.description?.map((line, j) => <li key={j}>{line}</li>)}</ul></div>)}</div>}
  </div>;
}

export default CandidatePage;
