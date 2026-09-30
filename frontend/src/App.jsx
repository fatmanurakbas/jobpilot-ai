import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import Sidebar from "./components/layout/Sidebar";
import Header from "./components/layout/Header";
import DashboardPage from "./pages/DashboardPage";
import ApplicationsPage from "./pages/ApplicationsPage";
import CandidatePage from "./pages/CandidatePage";
import JobsPage from "./pages/JobsPage";
import SettingsPage from "./pages/SettingsPage";
import ActivityPage from "./pages/ActivityPage";
import { PreferencesProvider } from "./context/PreferencesContext";


function App() {
  return (
    <PreferencesProvider><BrowserRouter>
      <div className="app-shell">

        <Sidebar />

        <main className="main-content">

          <Header />

          <div className="page-content">
            <Routes>

              <Route
                path="/"
                element={<DashboardPage />}
              />

              <Route
                path="/applications"
                element={<ApplicationsPage />}
              />

              <Route path="/candidate" element={<CandidatePage />} />
              <Route path="/jobs" element={<JobsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/activity" element={<ActivityPage />} />

            </Routes>
          </div>

        </main>

      </div>
    </BrowserRouter></PreferencesProvider>
  );
}

export default App;
