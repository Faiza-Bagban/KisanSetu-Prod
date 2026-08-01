import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";


import Header from "./components/Header";
import Footer from "./components/Footer";

// Pages
import ChatbotWidget from "./components/ChatbotWidget";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import FarmerPortal from "./pages/FarmerPortal";
import OfficerDashboard from "./pages/OfficerDashboard";
import GrievanceDashboard from "./pages/GrievanceDashboard";
import AdminMap from "./pages/AdminMap";
import IntelligenceReport from "./pages/IntelligenceReport";


/* ---------------- Layout Wrapper ---------------- */
const LayoutWrapper = ({ children }) => {
  const location = useLocation();

  const isAuthPage =
    location.pathname.startsWith("/login") ||
    location.pathname.startsWith("/signup");

  return (
    <>
      <Toaster position="top-right" />
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          background: "#020617",
        }}
      >
        {!isAuthPage && <Header />}
        <main style={{ flex: 1 }}>{children}</main>
        {!isAuthPage && <Footer />}
        <ChatbotWidget />
      </div>
    </>
  );
};


/* ---------------- Public Route ---------------- */
const PublicRoute = ({ children }) => {
  const { user } = useAuth();

  if (!user) return children;

  const routeMap = {
    "Farmer":           "/",
    "Field Officer":    "/officer",
    "District Officer": "/grievance",
    "Admin":            "/map"
  };

  return <Navigate to={routeMap[user.role] || "/"} replace />;
};


/* ---------------- App ---------------- */
export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <LayoutWrapper>
          <Routes>

            {/* ---------- PUBLIC ---------- */}
            <Route
              path="/login"
              element={
                <PublicRoute><Login /></PublicRoute>
              }
            />
            <Route
              path="/signup"
              element={
                <PublicRoute><Signup /></PublicRoute>
              }
            />

<Route
  path="/"
  element={
    <ProtectedRoute allowedRoles={["Farmer", "Field Officer", "District Officer", "Admin"]}>
      <FarmerPortal />
    </ProtectedRoute>
  }
/>

            {/* ---------- FIELD OFFICER ---------- */}
            <Route
              path="/officer"
              element={
                <ProtectedRoute allowedRoles={["Field Officer", "District Officer", "Admin"]}>
                  <OfficerDashboard />
                </ProtectedRoute>
              }
            />

            {/* ---------- DISTRICT OFFICER ---------- */}
            <Route
              path="/grievance"
              element={
                <ProtectedRoute allowedRoles={["District Officer", "Admin"]}>
                  <GrievanceDashboard />
                </ProtectedRoute>
              }
            />

            {/* ---------- MAP ---------- */}
            <Route
              path="/map"
              element={
                <ProtectedRoute allowedRoles={["District Officer", "Admin"]}>
                  <AdminMap />
                </ProtectedRoute>
              }
            />

            {/* ---------- INTELLIGENCE ---------- */}
            <Route
              path="/intelligence"
              element={
                <ProtectedRoute allowedRoles={["District Officer", "Admin"]}>
                  <IntelligenceReport />
                </ProtectedRoute>
              }
            />

            {/* ---------- FALLBACK ---------- */}
            <Route path="*" element={<Navigate to="/login" replace />} />

          </Routes>
        </LayoutWrapper>
      </BrowserRouter>
    </AuthProvider>
  );
}