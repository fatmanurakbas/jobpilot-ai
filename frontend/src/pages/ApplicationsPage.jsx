import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ArrowDownToLine, Check, CircleCheck, CircleDashed, FileCheck2, FileText, LoaderCircle, Play, Send, ShieldCheck } from "lucide-react";
import applicationService from "../services/applicationService";
import workspaceService from "../services/workspaceService";
import api from "../services/api";
import { usePreferences } from "../context/PreferencesContext";

const steps = ["Match Analysis", "Tailored CV", "Cover Letter", "Package Review", "Application Form", "Form Preview", "Final Approval", "Submit"];
const statusText = { SUBMITTED: "Submitted", SUBMISSION_UNCONFIRMED: "Submission unconfirmed", SUBMISSION_IN_PROGRESS: "Submission in progress", FORM_PREPARED: "Form prepared", AWAITING_USER_REVIEW: "Awaiting user review", PACKAGE_APPROVED: "Package approved", COVER_LETTER_DRAFTED: "Cover letter drafted", CV_VALIDATION_FAILED: "CV validation failed", MATCHED: "Match completed" };

export default function ApplicationsPage() {
  const { t } = usePreferences();
  const [params] = useSearchParams();
  const applicationId = Number(params.get("id")) || null;
  const [packageData, setPackageData] = useState(null);
  const [approval, setApproval] = useState(null);
  const [submissionApproval, setSubmissionApproval] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [candidateId, setCandidateId] = useState("");
  const [jobId, setJobId] = useState(params.get("jobId") || "");
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [busyAction, setBusyAction] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [result, setResult] = useState(null);
  const [formUrl, setFormUrl] = useState("");
  const [inspection, setInspection] = useState(null);
  const [mapping, setMapping] = useState(null);
  const [resolved, setResolved] = useState(null);
  const [answers, setAnswers] = useState({});
  const [answersSaved, setAnswersSaved] = useState(false);
  const [screenshotVersion, setScreenshotVersion] = useState(Date.now());
  const [screenshotLoaded, setScreenshotLoaded] = useState(false);
  const [screenshotError, setScreenshotError] = useState(false);
  const [reviewWatching, setReviewWatching] = useState(false);

  const refresh = useCallback(async () => {
    if (!applicationId) return;
    const [pkg, pkgApproval, subApproval] = await Promise.all([
      applicationService.getPackage(applicationId),
      applicationService.getApprovalStatus(applicationId).catch(() => ({ data: null })),
      applicationService.getSubmissionApprovalStatus(applicationId).catch(() => ({ data: null })),
    ]);
    setPackageData(pkg.data); setApproval(pkgApproval.data); setSubmissionApproval(subApproval.data);
    return pkg.data;
  }, [applicationId]);

  useEffect(() => {
    refresh().catch((e) => setError(e.response?.data?.detail || "Application yüklenemedi."));
    workspaceService.getJobs().then(({ data }) => setJobs(data)).catch(() => {});
    workspaceService.getCandidate().then(({ data }) => data?.id && setCandidateId(String(data.id))).catch(() => {});
  }, [refresh]);
  useEffect(() => {
    if (!reviewWatching || !applicationId) return undefined;
    let count = 0;
    const timer = window.setInterval(() => { count += 1; refresh().then((data) => { if (data?.status === "AWAITING_USER_REVIEW" || count >= 60) setReviewWatching(false); }).catch(() => {}); }, 2000);
    return () => window.clearInterval(timer);
  }, [reviewWatching, applicationId, packageData?.status, refresh]);
  useEffect(() => {
    if (packageData?.status === "AWAITING_USER_REVIEW") {
      setReviewWatching(false); setScreenshotError(false); setScreenshotLoaded(false); setScreenshotVersion(Date.now());
    }
  }, [packageData?.status]);

  async function run(label, action, opts = {}) {
    setBusy(true); setBusyAction(opts.key || label); setError(""); setMessage(""); setResult(null);
    try {
      const response = await action();
      const data = response?.data ?? response;
      setResult(data);
      const notice = typeof opts.message === "function" ? opts.message(data) : (opts.message || `${label} tamamlandı.`);
      if (opts.failedIf?.(data)) { setError(notice); setMessage(""); }
      else setMessage(notice);
      if (opts.after) await opts.after(data);
      await refresh();
      if (opts.advance) setStep((n) => Math.min(n + 1, 7));
    } catch (e) {
      setError(e.response?.data?.detail || e.message || `${label} başarısız oldu.`);
    } finally { setBusy(false); setBusyAction(""); }
  }

  const pkgApproved = Boolean(approval?.approval_valid);
  const verification = resolved?.verification || packageData?.form_verification;
  const formVerified = Boolean(verification?.verified);
  const isSubmitted = packageData?.status === "SUBMITTED";
  const displayStatus = (status) => status ? t(statusText[status] || status.replaceAll("_", " ")) : t("NOT STARTED");
  const complete = useMemo(() => new Set([
    ...(packageData?.match_percentage != null ? [steps[0]] : []),
    ...(packageData?.cv_validated && packageData?.cv_docx_ready ? [steps[1]] : []),
    ...(packageData?.cover_letter_validated && packageData?.cover_letter_docx_ready ? [steps[2]] : []),
    ...(pkgApproved ? [steps[3]] : []),
    ...(inspection ? [steps[4]] : []),
    ...(formVerified ? [steps[5]] : []),
    ...(submissionApproval?.approval_valid ? [steps[6]] : []),
    ...(isSubmitted ? [steps[7]] : []),
  ]), [packageData, pkgApproved, inspection, formVerified, submissionApproval, isSubmitted]);

  async function match(event) {
    event.preventDefault();
    await run("Match analysis", () => applicationService.match(Number(candidateId), Number(jobId)), { key: "match", after: (data) => { if (data?.application_id) window.location.href = `/applications?id=${data.application_id}`; } });
  }
  async function inspect() { await run("Form inspection", () => applicationService.inspectForm(applicationId, formUrl), { key: "form-inspect", after: setInspection }); }
  async function map() { await run("Form mapping", () => applicationService.mapForm(applicationId, formUrl), { key: "form-map", after: (data) => { setMapping(data); const initial = {}; data.mappings?.forEach((x) => { if (x.status === "NEEDS_USER_INPUT") initial[x.field_name || x.field_label || `field_${x.field_index}`] = x.value || ""; }); setAnswers(initial); } }); }
  async function saveAnswers() {
    const items = Object.entries(answers).filter(([, value]) => value.trim()).map(([field_name, value]) => ({ field_name, value }));
    await run("User answers", () => applicationService.saveFormAnswers(applicationId, items), { after: () => setAnswersSaved(true), message: "Cevaplar kaydedildi." });
  }
  async function resolve() { await run("Form resolution", () => applicationService.resolveForm(applicationId, formUrl), { after: setResolved }); }
  async function fill() { await run("Form preparation", () => applicationService.fillForm(applicationId, formUrl), { key: "form-fill", after: (data) => { setResolved(data); setScreenshotError(false); setScreenshotVersion(Date.now()); } }); }
  async function reviewInBrowser() {
    await run("Browser review", async () => {
      const { data } = await applicationService.browserReviewPlan(applicationId, formUrl);
      const response = await fetch("http://127.0.0.1:8765/review", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ application_id: applicationId, api_base: api.defaults.baseURL || "http://localhost:8000", plan: data.plan, uploads: data.uploads }) });
      if (!response.ok) throw new Error("JobPilot Browser Agent çalışmıyor. desktop_agent yönergelerini izleyin.");
      setReviewWatching(true); return response.json();
    }, { key: "browser-review", message: "Görünür başvuru sayfası açılıyor. JobPilot formu göndermez." });
  }
  async function approveSubmission() { await run("Final approval", () => applicationService.approveSubmission(applicationId, formUrl), { key: "submission-approve", message: "JobPilot gönderimi onaylandı. Henüz gönderim yapılmadı." }); }
  async function submit() { await run("JobPilot submission", () => applicationService.submit(applicationId), { key: "submit", message: "Gönderim sonucu kaydedildi." }); }

  const canOpen = (i) => i === 0 || (i === 1 && !!applicationId) || (i === 2 && packageData?.cv_validated) || (i === 3 && packageData?.ready_for_review) || (i === 4 && pkgApproved) || (i === 5 && pkgApproved && !!formUrl) || (i === 6 && formVerified) || (i === 7 && submissionApproval?.approval_valid);
  return <main className="workspace-page application-workflow">
    <header className="application-detail-header"><div><p className="eyebrow">{applicationId ? `${t("Başvuru akışı")} · #${applicationId}` : t("Yeni başvuru")}</p><h1>{applicationId ? t("Application workflow") : t("Create an application")}</h1><p className="application-company">{applicationId ? `${t("Başvuru")} #${applicationId}` : t("İlan ve aday CV’siyle başvuru akışını başlatın.")}</p></div><div className="application-header-meta">{packageData?.match_percentage != null && <div className="detail-match-score"><strong>{Math.round(packageData.match_percentage)}%</strong><span>{t("MATCH")}</span></div>}<div className={`status-badge${isSubmitted ? " submitted" : ""}`}>{displayStatus(packageData?.status)}</div></div></header>
    {busy ? <div className="api-message operation-running" role="status" aria-live="polite"><LoaderCircle className="spin" size={16}/><span><strong>{t(operationName(busyAction))}</strong> çalışıyor…</span></div> : (error || message) && <div className={`api-message${error ? " error" : " success"}`} role={error ? "alert" : "status"}>{error || message}</div>}
    <nav className="workflow-nav" aria-label={t("Application steps")}>{steps.map((name, i) => <button key={name} disabled={!canOpen(i)} className={`workflow-nav-item${step === i ? " active" : ""}${complete.has(name) ? " complete" : ""}`} onClick={() => setStep(i)}><span className="workflow-nav-check">{complete.has(name) ? <Check size={13}/> : i + 1}</span>{t(name)}</button>)}</nav>
    {step === 0 && <section className="panel workflow-panel"><Heading n={1} title={t("Match Analysis")} status={applicationId ? "Tamamlandı" : "Aday ve ilan seçin"}/>{applicationId ? <p>{t("Eşleşme")}: {packageData?.match_percentage ?? "…"}%</p> : <form className="inline-form" onSubmit={match}><label>{t("Candidate ID")}<input type="number" required value={candidateId} onChange={(e) => setCandidateId(e.target.value)}/></label><label>{t("Analyzed job")}<select required value={jobId} onChange={(e) => setJobId(e.target.value)}><option value="">{t("Select a job")}</option>{jobs.map((j) => <option key={j.id} value={j.id}>#{j.id} · {j.position} — {j.company}</option>)}</select></label><button className="primary-button" disabled={busy}>{busyAction === "match" ? <><LoaderCircle className="spin" size={16}/> Analyzing…</> : t("Analyze match")}</button></form>}</section>}
    {step === 1 && <section className="panel workflow-panel"><Heading n={2} title={t("Tailored CV")} status={packageData?.cv_validation?.is_valid === false ? `${t("Validation failed")} · ${packageData.cv_validation.issues?.length || 0} ${t("issue(s)")}` : packageData?.cv_validated ? t("Validated") : t("CV required")}/><div className="action-toolbar"><Action label={t("Generate tailoring plan")} busy={busyAction === "cv-plan"} done={packageData?.cv_plan_ready} status={packageData?.cv_plan_ready ? "Plan hazır" : "Plan oluşturulmadı"} disabled={busy || packageData?.cv_plan_ready} onClick={() => run("CV plan", () => applicationService.tailorCv(applicationId), { key: "cv-plan" })}/><Action label={t("Validate CV")} busy={busyAction === "cv-validate"} done={packageData?.cv_validated} status={packageData?.cv_validation?.is_valid === false ? `Başarısız · ${packageData.cv_validation.issues?.length || 0} bulgu` : packageData?.cv_validated ? "Doğrulandı" : "Doğrulama bekliyor"} disabled={busy || !packageData?.cv_plan_ready || packageData?.cv_validated} onClick={() => run("CV validation", () => applicationService.validateCv(applicationId), { key: "cv-validate", message: (data) => data.is_valid ? `CV validation passed · ${data.checked_claims} claims checked.` : `CV validation failed · ${data.issues?.length || 0} issue(s). Review the findings below.`, failedIf: (data) => !data.is_valid })}/>{packageData?.cv_validation?.is_valid === false && <Action label={t("Correct CV using these findings")} busy={busyAction === "cv-correct"} status="Düzeltme gerekli" disabled={busy} onClick={() => run("CV correction", () => applicationService.correctCv(applicationId), { key: "cv-correct", message: (data) => `${data.corrections_made?.length || 0} correction(s) applied. Validate the CV again.` })}/>}<Action label={t("Finalize CV")} busy={busyAction === "cv-finalize"} done={packageData?.cv_docx_ready && packageData?.cv_pdf_ready} status={packageData?.cv_docx_ready && packageData?.cv_pdf_ready ? "Belgeler hazır" : packageData?.cv_validated ? "Hazır" : "Önce doğrulama"} disabled={busy || !packageData?.cv_validated || (packageData?.cv_docx_ready && packageData?.cv_pdf_ready)} onClick={() => run("CV finalization", () => applicationService.finalizeCv(applicationId), { key: "cv-finalize" })}/><Action label={t("Generate CV document")} busy={busyAction === "cv-generate"} done={packageData?.cv_docx_ready} status={packageData?.cv_docx_ready ? "DOCX hazır" : packageData?.cv_validated ? "Hazır" : "Önce doğrulama"} disabled={busy || !packageData?.cv_validated || packageData?.cv_docx_ready} onClick={() => run("CV document", () => applicationService.generateCv(applicationId), { key: "cv-generate" })}/></div><ValidationReport validation={packageData?.cv_validation}/><Downloads urls={[["DOCX", applicationService.cvDocxUrl(applicationId), "tailored_cv.docx", packageData?.cv_docx_ready], ["PDF", applicationService.cvPdfUrl(applicationId), "tailored_cv.pdf", packageData?.cv_pdf_ready]]} busy={busy}/></section>}
    {step === 2 && <section className="panel workflow-panel"><Heading n={3} title={t("Cover Letter")} status={packageData?.cover_letter_validation?.is_valid === false ? `${t("Validation failed")} · ${packageData.cover_letter_validation.issues?.length || 0} ${t("issue(s)")}` : packageData?.cover_letter_docx_ready && packageData?.cover_letter_pdf_ready ? t("Documents ready") : packageData?.cover_letter_validated ? t("Validated · finalize documents") : packageData?.cover_letter_ready ? t("Draft generated · validate it") : t("Draft not generated")}/><div className="action-toolbar"><Action label={t("Generate cover letter")} busy={busyAction === "letter-generate"} done={packageData?.cover_letter_ready} status={packageData?.cover_letter_ready ? "Taslak oluşturuldu" : "Henüz oluşturulmadı"} disabled={busy || packageData?.cover_letter_ready} onClick={() => run("Cover letter", () => applicationService.generateCoverLetter(applicationId), { key: "letter-generate" })}/><Action label={t("Validate cover letter")} busy={busyAction === "letter-validate"} done={packageData?.cover_letter_validated} status={packageData?.cover_letter_validation?.is_valid === false ? `Başarısız · ${packageData.cover_letter_validation.issues?.length || 0} bulgu` : packageData?.cover_letter_validated ? "Doğrulandı" : packageData?.cover_letter_ready ? "Tıklayarak doğrulayın" : "Önce taslağı oluşturun"} disabled={busy || !packageData?.cover_letter_ready || packageData?.cover_letter_validated} onClick={() => run("Cover letter validation", () => applicationService.validateCoverLetter(applicationId), { key: "letter-validate", message: (data) => data.is_valid ? `Cover letter validation passed · ${data.checked_claims} claims checked.` : `Cover letter validation failed · ${data.issues?.length || 0} issue(s). See the findings below.`, failedIf: (data) => !data.is_valid })}/>{packageData?.cover_letter_validation?.is_valid === false && <Action label={t("Correct cover letter")} busy={busyAction === "letter-correct"} status="Düzeltme gerekli" disabled={busy} onClick={() => run("Cover letter correction", () => applicationService.correctCoverLetter(applicationId), { key: "letter-correct", message: "Düzeltme uygulandı. Cover letter'ı yeniden doğrulayın." })}/>}<Action label={t("Finalize cover letter")} busy={busyAction === "letter-finalize"} done={packageData?.cover_letter_docx_ready && packageData?.cover_letter_pdf_ready} status={packageData?.cover_letter_docx_ready && packageData?.cover_letter_pdf_ready ? "DOCX ve PDF hazır" : packageData?.cover_letter_validated ? "Belgeleri oluştur" : "Önce doğrulama"} disabled={busy || !packageData?.cover_letter_validated || (packageData?.cover_letter_docx_ready && packageData?.cover_letter_pdf_ready)} onClick={() => run("Cover letter finalization", () => applicationService.finalizeCoverLetter(applicationId), { key: "letter-finalize", message: (data) => data.message || "Cover letter finalization tamamlandı.", failedIf: (data) => data.success === false })}/></div><ValidationReport title={t("Cover letter validation")} helpText="Correct the letter using these findings, then validate it again." validation={packageData?.cover_letter_validation}/><Downloads urls={[["DOCX", applicationService.coverLetterDocxUrl(applicationId), "cover_letter.docx", packageData?.cover_letter_docx_ready], ["PDF", applicationService.coverLetterPdfUrl(applicationId), "cover_letter.pdf", packageData?.cover_letter_pdf_ready]]} busy={busy}/></section>}
    {step === 3 && <section className="panel workflow-panel"><Heading n={4} title={t("Package Review")} status={pkgApproved ? t("Approved") : t("Review package")}/><div className="review-checks"><StateCheck label={t("CV validated and generated")} value={packageData?.cv_validated && packageData?.cv_pdf_ready}/><StateCheck label={t("Cover letter validated and generated")} value={packageData?.cover_letter_validated && packageData?.cover_letter_pdf_ready}/><StateCheck label={t("Package approval")} value={pkgApproved}/></div><button className="primary-button" disabled={busy || !packageData?.ready_for_review || pkgApproved} onClick={() => run("Package approval", () => applicationService.approvePackage(applicationId), { key: "package-approve" })}>{busyAction === "package-approve" ? <LoaderCircle className="spin" size={16}/> : <ShieldCheck size={16}/>}{busyAction === "package-approve" ? "Approving package…" : pkgApproved ? "Package approved ✓" : "Approve package"}</button></section>}
    {step === 4 && <section className="panel workflow-panel"><Heading n={5} title={t("Application Form")} status={inspection ? t("Inspected") : t("URL required")}/><label className="full-label">{t("Application form URL")}<input type="url" value={formUrl} onChange={(e) => setFormUrl(e.target.value)} placeholder="https://company.com/careers/apply"/></label><div className="action-toolbar"><Action label={t("Inspect form")} busy={busyAction === "form-inspect"} done={Boolean(inspection)} status={inspection ? `${inspection.field_count} alan bulundu` : !formUrl ? "URL girin" : !pkgApproved ? "Önce paket onayı" : "Formu inceleyin"} disabled={busy || !formUrl || !pkgApproved} onClick={inspect}/><Action label={t("Generate mapping")} busy={busyAction === "form-map"} done={Boolean(mapping)} status={mapping ? "Eşleme hazır" : inspection ? "Eşleme oluşturun" : "Önce formu inceleyin"} disabled={busy || !inspection || !!mapping} onClick={map}/><Action label={t("Resolve answers")} busy={busyAction === "form-resolve"} done={Boolean(resolved?.ready_to_fill)} status={resolved?.ready_to_fill ? "Doldurmaya hazır" : mapping ? "Cevapları çözümleyin" : "Önce eşleme oluşturun"} disabled={busy || !mapping} onClick={resolve}/></div>{mapping?.mappings?.map((item) => { const key = item.field_name || item.field_label || `field_${item.field_index}`; return <div className="mapping-row" key={item.field_index}><div><strong>{item.field_label || key}</strong><small>{item.status}{item.reason ? ` · ${item.reason}` : ""}</small></div>{item.status === "NEEDS_USER_INPUT" ? <input aria-label={`Answer for ${item.field_label || key}`} value={answers[key] || ""} onChange={(e) => { setAnswers((old) => ({ ...old, [key]: e.target.value })); setAnswersSaved(false); }}/>: <span>{item.value || item.source || "—"}</span>}</div>; })}{mapping?.needs_user_input_count > 0 && <div className="answer-save-row"><button className="secondary-button" onClick={saveAnswers} disabled={busy || !Object.values(answers).some((value) => value.trim())} aria-busy={busyAction === "User answers"}>{busyAction === "User answers" ? <LoaderCircle className="spin" size={15}/> : answersSaved ? <CircleCheck size={15}/> : <Check size={15}/>}{busyAction === "User answers" ? t("Saving answers…") : answersSaved ? t("Answers saved ✓") : t("Save explicit user answers")}</button>{answersSaved && <span role="status">Bu cevaplar başvuru formunu çözümlemek için kaydedildi.</span>}</div>}{resolved && <ResolvedFields data={resolved}/>}<ResultBlock data={result}/></section>}
    {step === 5 && <section className="panel workflow-panel"><Heading n={6} title={t("Form Preview")} status={formVerified ? t("FORM PREPARED") : t("Prepare form")}/><p>{t("Formu hazırlayın; otomatik gönderim yapılmaz.")}</p><div className="action-toolbar"><button className="primary-button" disabled={busy || !formUrl || !pkgApproved || (resolved && !resolved.ready_to_fill)} onClick={fill}>{busyAction === "form-fill" ? <LoaderCircle className="spin" size={16}/> : <FileCheck2 size={16}/>}{t("Fill form & verify")}</button>{formVerified && <><button className="secondary-button" disabled={busy || reviewWatching} onClick={reviewInBrowser}><Play size={15}/>{reviewWatching ? t("Tarayıcıda inceleme sürüyor…") : t("Review in Browser")}</button><button className="primary-button" disabled={busy || !formUrl || !pkgApproved || submissionApproval?.approval_valid} onClick={approveSubmission}><ShieldCheck size={16}/>{submissionApproval?.approval_valid ? t("JobPilot gönderimi onaylandı") : t("Approve JobPilot Submission")}</button></>}</div>{formVerified && <div className="verification-banner success"><CircleCheck size={17}/><strong>{t("Form prepared")} · ✓ {verification.verified_count}/{verification.verified_count + verification.failed_count} {t("alan doğrulandı")}</strong></div>}<div className={`screenshot-frame${screenshotLoaded ? " has-screenshot" : ""}`}><img key={`${applicationId}-${screenshotVersion}`} src={`${applicationService.formScreenshotUrl(applicationId)}?v=${screenshotVersion}`} alt={t("Filled application form screenshot")} onLoad={() => { setScreenshotLoaded(true); setScreenshotError(false); }} onError={() => setScreenshotError(true)}/>{screenshotError && <span>{t("Ekran görüntüsü bulunamadı. Formu yeniden hazırlayın.")}</span>}</div>{verification?.fields?.map((f) => <div className="review-check" key={f.field_index}><StateCheck label={f.field_name || `Field ${f.field_index + 1}`} value={f.verified}/></div>)}</section>}
    {step === 6 && <section className="panel workflow-panel"><Heading n={7} title={t("Final Approval")} status={submissionApproval?.approval_valid ? t("Approved") : t("Approval required")}/><p>JobPilot onayı form ekran görüntüsü, URL, paket ve kullanıcı cevaplarının hash’ine bağlıdır.</p><label className="full-label">{t("Submission URL")}<input type="url" required value={formUrl} onChange={(e) => setFormUrl(e.target.value)}/></label><div className="review-checks"><StateCheck label={t("Package approved")} value={pkgApproved}/><StateCheck label={t("Form fields verified")} value={formVerified}/><StateCheck label={t("Final submission approval valid")} value={submissionApproval?.approval_valid}/></div>{submissionApproval?.message && <p>{submissionApproval.message}</p>}</section>}
    {step === 7 && <section className="panel workflow-panel"><Heading n={8} title={t("Submit")} status={isSubmitted ? t("Submitted") : packageData?.status === "SUBMISSION_UNCONFIRMED" ? t("Submission unconfirmed") : submissionApproval?.approval_valid ? t("Ready") : t("Approval required")}/>{isSubmitted ? <><div className="submit-confirmation"><CircleCheck size={22}/><div><strong>{t("Submission confirmed ✓")}</strong><p>{t("Platform confirmation:")} “{packageData.submission_confirmation}”</p><p>{t("Submitted at:")} {packageData.submitted_at ? new Date(packageData.submitted_at.endsWith("Z") || packageData.submitted_at.includes("+") ? packageData.submitted_at : `${packageData.submitted_at}Z`).toLocaleString() : "—"}</p><p>{t("Final URL:")} <a href={packageData.submission_url} target="_blank" rel="noreferrer">{packageData.submission_url}</a></p></div></div>{packageData.submission_screenshot_available && <a className="secondary-button" href={applicationService.submissionScreenshotUrl(applicationId)} target="_blank" rel="noreferrer">{t("Onay ekran görüntüsünü görüntüle")}</a>}</> : <><div className="submit-confirmation"><Send size={22}/><div><strong>{packageData?.status === "SUBMISSION_UNCONFIRMED" ? t("Submission unconfirmed") : t("JobPilot submit")}</strong><p>{packageData?.status === "SUBMISSION_UNCONFIRMED" ? t("Gönderim kanıtı bulunamadı. Tekrar denemeden önce hedef web sitesini inceleyin.") : packageData?.status === "SUBMISSION_IN_PROGRESS" ? t("Gönderim işleniyor.") : t("Açık onay gerekir. Tıklama tek başına gönderim anlamına gelmez.")}</p>{packageData?.submission_url && <p>{t("Final URL:")} {packageData.submission_url}</p>}{packageData?.submission_screenshot_available && <a href={applicationService.submissionScreenshotUrl(applicationId)} target="_blank" rel="noreferrer">{t("View after-submission screenshot")}</a>}</div></div>{!['SUBMISSION_UNCONFIRMED', 'SUBMISSION_IN_PROGRESS'].includes(packageData?.status) && <button className="primary-button submit-button" disabled={busy || !submissionApproval?.approval_valid || !pkgApproved} onClick={submit}>{busyAction === "submit" ? <LoaderCircle className="spin" size={16}/> : <Send size={16}/>}{t("Submit with JobPilot")}</button>}</>}</section>}
    {result && <ResultBlock data={result}/>}
  </main>;
}

function Heading({ n, title, status }) { return <div className="workflow-step-heading"><span className="step-number">{n}</span><div><h2>{title}</h2></div><span className="step-state">{status}</span></div>; }
function operationName(key) {
  return ({ "letter-generate": "Generate cover letter", "letter-validate": "Validate cover letter", "letter-correct": "Correct cover letter", "letter-finalize": "Finalize cover letter", "cv-plan": "Generate CV plan", "cv-validate": "Validate CV", "cv-correct": "Correct CV", "cv-finalize": "Finalize CV", "cv-generate": "Generate CV document", "form-inspect": "Inspect application form", "form-map": "Map form fields", "form-resolve": "Resolve form answers", "form-fill": "Prepare and verify form", "browser-review": "Open browser review", "submission-approve": "Record final approval", "package-approve": "Approve application package", match: "Analyze candidate and job", "form-answers": "Save user answers", submit: "Submit application" })[key] || key || "Operation";
}
function Action({ label, onClick, disabled, busy, done, status }) {
  const { t } = usePreferences();
  const state = busy ? "Çalışıyor…" : status || (done ? "Tamamlandı" : disabled ? "Ön koşul bekleniyor" : "Hazır");
  return <button type="button" className="secondary-button operation-button" disabled={disabled || busy} onClick={onClick} aria-busy={busy}>
    <span className="operation-icon">{busy ? <LoaderCircle className="spin" size={15}/> : done ? <CircleCheck size={15}/> : <Play size={14}/>}</span>
    <span>{busy ? `${label}…` : label}</span><small className={`operation-status${busy ? " running" : done ? " complete" : disabled ? " waiting" : ""}`}>{t(state)}</small>
  </button>;
}
function StateCheck({ label, value }) { return <div className="review-check"><span className={`review-check-icon${value ? " ok" : ""}`}>{value ? <Check size={13}/> : <CircleDashed size={13}/>}</span><span>{label}</span></div>; }
function ResultBlock({ data }) { const { t } = usePreferences(); return <details className="result-details"><summary><FileText size={15}/>{t("Latest operation result")}</summary><pre>{JSON.stringify(data, null, 2)}</pre></details>; }

function ResolvedFields({ data }) { const { t } = usePreferences(); return <div className="resolved-fields"><div className="resolved-fields-heading"><strong>{t("Form answers")}</strong><span>{data.fill_count || 0} {t("to fill")} · {data.upload_count || 0} {t("files")} · {data.unresolved_count || 0} {t("missing")}</span></div>{data.fields?.map((field) => <div className="mapping-row" key={field.field_index}><div><strong>{field.field_label || field.field_name || `${t("Field")} ${field.field_index + 1}`}</strong><small>{t(field.action)}{field.resolved_from ? ` · ${field.resolved_from}` : ""}{field.reason ? ` · ${field.reason}` : ""}</small></div><span>{field.value || field.file_path || "—"}</span></div>)}</div>; }
function ValidationReport({ validation, title = "CV validation", helpText = "Use “Correct CV using these findings”, then validate the updated CV again. Unsupported experience or skills must not be kept." }) {
  const { t } = usePreferences();
  if (!validation) return null;
  const valid = validation.is_valid;
  const issues = validation.issues || [];
  return <section className={`validation-card${valid ? "" : " validation-card-failed"}`} aria-live="polite">
    <div className="panel-header"><div><h3>{valid ? `${t(title)} ${t("passed")}` : `${t(title)} ${t("failed")}`}</h3><p>{validation.summary || `${validation.checked_claims || 0} ${t("factual claims checked")}`}</p></div><span className={`validation-pill ${valid ? "pass" : "fail"}`}>{valid ? t("PASSED") : `${issues.length} ${t("issue(s)")}`}</span></div>
    {!valid && issues.length > 0 && <div className="validation-issues">{issues.map((issue, index) => <article key={`${issue.field}-${index}`}><strong>{issue.field || `Finding ${index + 1}`} · {issue.severity || "review"}</strong><p>{issue.reason}</p>{issue.generated_text && <blockquote>{issue.generated_text}</blockquote>}</article>)}</div>}
    {!valid && issues.length === 0 && <p>Validator returned failed status without detailed findings. Run validation again; if it repeats, inspect the API result.</p>}
    {!valid && <p className="inline-hint">{helpText}</p>}
  </section>;
}
function Downloads({ urls, busy }) {
  const [downloading, setDownloading] = useState("");
  const [downloaded, setDownloaded] = useState("");
  const [downloadError, setDownloadError] = useState("");
  async function startDownload(url, name) {
    setDownloading(name); setDownloaded(""); setDownloadError("");
    try {
      const { data } = await api.get(url, { responseType: "blob" });
      const href = URL.createObjectURL(data);
      const anchor = document.createElement("a"); anchor.href = href; anchor.download = name; anchor.click();
      window.setTimeout(() => URL.revokeObjectURL(href), 1000);
      setDownloaded(name);
    } catch (e) { setDownloadError(e.response?.data?.detail || `${name} indirilemedi.`); }
    finally { setDownloading(""); }
  }
  const { t } = usePreferences();
  return <div><div className="download-row">{urls.map(([label, url, name, ready]) => <button type="button" key={label} className="secondary-button download-status-button" disabled={!ready || busy || Boolean(downloading)} aria-busy={downloading === name} onClick={() => startDownload(url, name)}><span>{downloading === name ? <LoaderCircle className="spin" size={15}/> : downloaded === name ? <CircleCheck size={15}/> : <ArrowDownToLine size={15}/>} {downloading === name ? `${label} ${t("indiriliyor…")}` : `${label} ${t("download")}`}</span><small className={`operation-status${downloading === name ? " running" : downloaded === name ? " complete" : ready ? "" : " waiting"}`}>{downloading === name ? t("İndiriliyor…") : downloaded === name ? t("İndirildi ✓") : ready ? t("İndirmek için tıklayın") : t("Belge henüz üretilmedi")}</small></button>)}</div>{downloadError && <p className="api-message error" role="alert">{downloadError}</p>}{downloaded && <p className="operation-feedback success" role="status">{downloaded} {t("indirildi ✓")}</p>}</div>;
}
