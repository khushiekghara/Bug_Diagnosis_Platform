import { useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import SubmitBug from "./pages/SubmitBug";
import BugReports from "./pages/BugReports";
import Diagnosis from "./pages/Diagnosis";
import BugDetails from "./pages/BugDetails";

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  const refreshBugs = () => setRefreshKey((value) => value + 1);

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route
          path="/dashboard"
          element={<Dashboard refreshKey={refreshKey} />}
        />
        <Route
          path="/submit"
          element={<SubmitBug onSubmitted={refreshBugs} />}
        />
        <Route
          path="/bugs"
          element={<BugReports refreshKey={refreshKey} />}
        />
        <Route path="/bugs/:bugId" element={<BugDetails />} />
        <Route path="/diagnosis/:bugId" element={<Diagnosis />} />
      </Route>
    </Routes>
  );
}