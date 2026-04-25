import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import SOPLibrary from "./pages/SOPLibrary.jsx";
import SOPDetail from "./pages/SOPDetail.jsx";
import Sessions from "./pages/Sessions.jsx";
import SessionDetail from "./pages/SessionDetail.jsx";
import LiveMonitor from "./pages/LiveMonitor.jsx";
import Alerts from "./pages/Alerts.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/sops" element={<SOPLibrary />} />
        <Route path="/sops/:id" element={<SOPDetail />} />
        <Route path="/sessions" element={<Sessions />} />
        <Route path="/sessions/:id" element={<SessionDetail />} />
        <Route path="/monitor/:id" element={<LiveMonitor />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
