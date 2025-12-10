import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider, useAuth } from "./context/AuthContext";
import PRDGenerator from "./components/PRDGenerator";
import History from "./components/History";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import { Loader2 } from "lucide-react";
import { Analytics } from "@vercel/analytics/react";

const ProtectedRoute = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-[#0a0a0b]">
        <Loader2 className="w-8 h-8 text-[#fafafa] animate-spin" />
      </div>
    );
  }

  return user ? <Outlet /> : <Navigate to="/login" />;
};

function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-[#0a0a0b] text-[#fafafa]">
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />

            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<Home />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <Toaster />
        <Analytics />
      </div>
    </AuthProvider>
  );
}

function Home() {
  const [view, setView] = useState("generator");
  // const [selectedPrd, setSelectedPrd] = useState(null); // Unused for now

  return (
    <>
      {view === "generator" ? (
        <PRDGenerator onViewHistory={() => setView("history")} />
      ) : (
        <History
          onBack={() => setView("generator")}
          onSelectPrd={(prd) => {
            // Future: Load PRD into generator or show detail view
            setView("generator");
          }}
        />
      )}
    </>
  );
}

export default App;
