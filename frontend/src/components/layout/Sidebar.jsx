import { Activity, BriefcaseBusiness, LayoutDashboard, Rocket, Settings, UserRound } from "lucide-react";
import { NavLink } from "react-router-dom";
import { usePreferences } from "../../context/PreferencesContext";

function Sidebar() {
  const { t } = usePreferences();
  const items = [["/", LayoutDashboard, "Dashboard"], ["/jobs", BriefcaseBusiness, "Jobs"], ["/candidate", UserRound, "Candidate"], ["/applications", BriefcaseBusiness, "Applications"], ["/activity", Activity, "Agent Activity"]];
  return <aside className="sidebar"><div className="brand"><div className="brand-icon"><Rocket size={21}/></div><div><h2>JobPilot</h2><span>AI Agent</span></div></div><div className="sidebar-label">ÇALIŞMA ALANI</div><nav className="nav">{items.map(([to, Icon, label]) => <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}><Icon size={19}/>{t(label)}</NavLink>)}</nav><div className="sidebar-bottom"><NavLink to="/settings" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}><Settings size={19}/>{t("Settings")}</NavLink><div className="system-status"><span className="status-dot"/><div><strong>{t("System Operational")}</strong><small>{t("All agents online")}</small></div></div><small className="sidebar-version">JOBPILOT · WORKSPACE</small></div></aside>;
}
export default Sidebar;
