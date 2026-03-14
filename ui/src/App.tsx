import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Overview from "./pages/Overview";
import Usage from "./pages/Usage";
import Requests from "./pages/Requests";
import Settings from "./pages/Settings";
import ApiKeys from "./pages/ApiKeys";
import Projects from "./pages/Projects";
import Pricing from "./pages/Pricing";
import TestKeys from "./pages/TestKeys";
import { useMe } from "./api/hooks";

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const me = useMe();
  if (me.isLoading) {
    return <div className="p-6">Loading...</div>;
  }
  if (me.isError) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Overview />} />
        <Route path="usage" element={<Usage />} />
        <Route path="requests" element={<Requests />} />
        <Route path="projects" element={<Projects />} />
        <Route path="pricing" element={<Pricing />} />
        <Route path="test-keys" element={<TestKeys />} />
        <Route path="settings" element={<Settings />} />
        <Route path="keys" element={<ApiKeys />} />
      </Route>
    </Routes>
  );
}
