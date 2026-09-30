import { useEffect, useState } from "react";
import { ArrowRight, BriefcaseBusiness, CircleCheck, FileCheck2, Send, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import api from "../services/api";
import { usePreferences } from "../context/PreferencesContext";

function DashboardPage() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { t } = usePreferences();

  useEffect(() => {
    api.get("/applications/")
      .then(({ data }) => setApplications(Array.isArray(data) ? data : []))
      .catch((err) => setError(err.response?.data?.detail || "Başvurular alınamadı. Backend’in çalıştığını kontrol edin."))
      .finally(() => setLoading(false));
  }, []);

  const readyCount = applications.filter((app) => ["PACKAGE_APPROVED", "FORM_FILLED", "SUBMITTED"].includes(app.status)).length;
  const submittedCount = applications.filter((app) => app.status === "SUBMITTED").length;
  const averageMatch = applications.length
    ? Math.round(applications.reduce((sum, app) => sum + (app.match_percentage || 0), 0) / applications.length)
    : 0;

  return <div>
    <div className="page-heading dashboard-hero">
      <div><p className="eyebrow">JOBPILOT AI · KİŞİSEL ÇALIŞMA ALANINIZ</p><h1>{t("Dashboard")}</h1><p>{t("CV’niz ve iş ilanlarınızla başvuru sürecinizi yönetin.")}</p></div>
      <Link className="primary-button" to="/candidate"><Sparkles size={18}/>{t("Yeni başvuru başlat")}</Link>
    </div>

    {error && <div className="api-message error">{error}</div>}
    {loading && <div className="api-message">Başvurular yükleniyor…</div>}

    <div className="stats-grid">
      <StatCard icon={<BriefcaseBusiness/>} title={t("Applications")} value={applications.length} detail={t("Toplam başvuru")}/>
      <StatCard icon={<Sparkles/>} title={t("Average Match")} value={`${averageMatch}%`} detail={t("Ortalama eşleşme")}/>
      <StatCard icon={<FileCheck2/>} title={t("Ready")} value={readyCount} detail={t("İncelemeye hazır")}/>
      <StatCard icon={<Send/>} title={t("Submitted")} value={submittedCount} detail={t("Gönderilmiş başvurular")}/>
    </div>

    <div className="dashboard-grid">
      <section className="panel dashboard-applications">
        <div className="panel-header"><div><h2>{t("Applications")}</h2><p>{t("İş ilanlarına göre başvuru akışlarınız")}</p></div><Link to="/jobs" className="text-link">{t("İlan ekle")} <ArrowRight size={16}/></Link></div>
        {applications.map((application) => <div className="application-row" key={application.id}>
          <div className="company-logo">{(application.company || "JP").slice(0, 2).toUpperCase()}</div>
          <div className="application-info"><strong>{application.position || `Application #${application.id}`}</strong><span>{application.company || "Company"} · Application #{application.id}</span></div>
          <div className="match-score"><strong>{application.match_percentage ?? "—"}{application.match_percentage != null ? "%" : ""}</strong><span>{t("Match")}</span></div>
          <StatusBadge status={application.status}/>
          <Link className="application-open-link" to={`/applications?id=${application.id}`} aria-label={`Application #${application.id} ayrıntılarını aç`}><ArrowRight size={17}/></Link>
        </div>)}
        {!loading && applications.length === 0 && <div className="empty-state dashboard-empty"><strong>{t("Henüz başvuru yok")}</strong><span>{t("Önce master CV’nizi ekleyin, sonra bir ilan analiz edip eşleştirin.")}</span><div><Link className="secondary-button" to="/candidate">{t("CV ekle")}</Link><Link className="secondary-button" to="/jobs">{t("İlan ekle")}</Link></div></div>}
      </section>

      <section className="panel dashboard-next"><div className="panel-header"><div><h2>{t("Next steps")}</h2><p>{t("Yeni bir başvuru oluşturmak için")}</p></div></div>
        <NextStep number="1" title={t("Master CV yükle")} detail={t("Aday profili CV’nizden çıkarılır.")} to="/candidate"/>
        <NextStep number="2" title={t("İlan ekle ve analiz et")} detail={t("İş gereksinimleri kaydedilir.")} to="/jobs"/>
        <NextStep number="3" title={t("Match analizi başlat")} detail={t("İlan sayfasında oluşturduğunuz başvuruyu açın.")} to="/applications"/>
      </section>
    </div>
  </div>;
}

function StatCard({ icon, title, value, detail }) { return <div className="stat-card"><div className="stat-icon">{icon}</div><div className="stat-content"><span>{title}</span><strong>{value}</strong><small>{detail}</small></div></div>; }
function StatusBadge({ status }) { const submitted = status === "SUBMITTED"; return <div className={`status-badge${submitted ? " submitted" : ""}`}>{submitted && <CircleCheck size={15}/>} {status || "UNKNOWN"}</div>; }
function NextStep({ number, title, detail, to }) { return <Link className="next-step-row" to={to}><span className="next-step-number">{number}</span><span className="next-step-copy"><strong>{title}</strong><small>{detail}</small></span><span className="next-step-arrow"><ArrowRight size={16}/></span></Link>; }

export default DashboardPage;
