import { Bell, Globe2, Search } from "lucide-react";
import { usePreferences } from "../../context/PreferencesContext";

function Header() {
  const { language, setLanguage, t } = usePreferences();
  return <header className="top-header"><div className="search-box"><Search size={18}/><input placeholder={t("Search applications...")}/></div><div className="header-actions"><label className="language-select"><Globe2 size={16}/><span className="sr-only">{t("Language")}</span><select aria-label={t("Language")} value={language} onChange={(event) => setLanguage(event.target.value)}><option value="tr">Türkçe</option><option value="en">English</option></select></label><button className="icon-button" aria-label="Bildirimler"><Bell size={19}/></button><div className="avatar">FN</div></div></header>;
}
export default Header;
