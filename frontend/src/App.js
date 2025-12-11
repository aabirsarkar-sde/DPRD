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
              <Route path="/" element={<PRDGenerator />} />
              <Route path="/history" element={<History />} />
              <Route path="/prd/:id" element={<PRDGenerator />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <Toaster />
        <Analytics />
      </div>
    </AuthProvider>
  );
}

export default App;
