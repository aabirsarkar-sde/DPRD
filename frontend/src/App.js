import { useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import PRDGenerator from "@/components/PRDGenerator";
import { Analytics } from "@vercel/analytics/react";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<PRDGenerator />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-center" />
      <Analytics />
    </div>
  );
}

export default App;
