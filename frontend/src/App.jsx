import React, { useState, useEffect } from "react";
import FaceAnalyzer from "./components/FaceAnalyzer";
import ResultsDisplay from "./components/ResultsDisplay";
import RoutineDisplay from "./components/RoutineDisplay";
import { Sparkles, History, Heart, ShieldAlert, Award } from "lucide-react";

const API_BASE = "http://localhost:8002";

export default function App() {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [history, setHistory] = useState([]);
  const [activeTab, setActiveTab] = useState("analyzer"); // "analyzer" | "history"

  const fetchHistory = async () => {
    const sessionId = localStorage.getItem("skincv_session_id");
    if (!sessionId) return;
    try {
      const response = await fetch(`${API_BASE}/api/history?session_id=${sessionId}`);
      if (response.ok) {
        const data = await response.ok ? await response.json() : [];
        setHistory(data);
      }
    } catch (err) {
      console.error("Failed to fetch history:", err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [analysisResult]);

  const handleAnalysisComplete = (result) => {
    setAnalysisResult(result);
    setActiveTab("analyzer");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500/30">
      {/* Premium Header */}
      <header className="sticky top-0 z-50 w-full border-b border-slate-900 bg-slate-950/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center text-slate-950 font-bold text-lg shadow-md shadow-emerald-500/10">
              S
            </div>
            <span className="font-bold tracking-tight text-lg text-slate-100 flex items-center gap-1.5">
              SkinCV
              <span className="text-[10px] uppercase tracking-widest bg-slate-900 border border-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">
                v1.0.0
              </span>
            </span>
          </div>
          <nav className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab("analyzer")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition ${
                activeTab === "analyzer"
                  ? "bg-slate-900 text-emerald-400 border border-emerald-500/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Analyze
            </button>
            <button
              onClick={() => {
                setActiveTab("history");
                fetchHistory();
              }}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
                activeTab === "history"
                  ? "bg-slate-900 text-emerald-400 border border-emerald-500/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <History className="w-3.5 h-3.5" />
              History ({history.length})
            </button>
          </nav>
        </div>
      </header>

      {/* Hero Header */}
      <main className="max-w-6xl mx-auto px-4 py-10 flex flex-col items-center">
        <div className="text-center max-w-2xl mb-12 flex flex-col items-center">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 font-medium mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            HackZen 2026 CV Track Entry
          </div>
          <h1 className="text-4xl font-extrabold text-slate-50 tracking-tight sm:text-5xl mb-4">
            Physiology-First Skin Analysis
          </h1>
          <p className="text-base text-slate-400 leading-relaxed">
            An open-challenge facial analyzer explicitly designed for gender-neutral routine building, focusing purely on skin tone-inclusive classical CV heuristics.
          </p>
        </div>

        {activeTab === "analyzer" ? (
          <div className="grid lg:grid-cols-12 gap-8 w-full items-start">
            {/* Left side: scanner */}
            <div className="lg:col-span-6 flex justify-center">
              <FaceAnalyzer
                apiBase={API_BASE}
                isAnalyzing={isAnalyzing}
                setIsAnalyzing={setIsAnalyzing}
                onAnalysisComplete={handleAnalysisComplete}
              />
            </div>

            {/* Right side: results & routine */}
            <div className="lg:col-span-6 flex flex-col gap-8 items-center w-full">
              {analysisResult ? (
                <>
                  <ResultsDisplay scores={analysisResult.scores} quality={analysisResult.quality} warnings={analysisResult.warnings} />
                  <RoutineDisplay routine={analysisResult.routine} />
                </>
              ) : (
                <div className="flex flex-col items-center justify-center p-12 text-center border border-slate-900 bg-slate-900/20 rounded-2xl aspect-[4/3] w-full max-w-xl">
                  <Heart className="w-12 h-12 text-slate-800 mb-4" />
                  <h3 className="text-base font-semibold text-slate-300 mb-1">Waiting for analysis</h3>
                  <p className="text-xs text-slate-500 max-w-xs">
                    Once you upload or capture a photo, your zoned skin concern scores and recommended steps will appear here.
                  </p>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* History View */
          <div className="w-full max-w-3xl flex flex-col gap-6">
            <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
              <History className="w-6 h-6 text-emerald-500" />
              Scan History
            </h2>
            {history.length === 0 ? (
              <div className="text-center p-16 border border-slate-900 bg-slate-900/20 rounded-2xl">
                <p className="text-sm text-slate-500">No previous scans found in this session.</p>
              </div>
            ) : (
              <div className="grid gap-6">
                {history.map((record) => (
                  <div
                    key={record.id}
                    className="p-6 bg-slate-900/60 border border-slate-850 rounded-2xl flex flex-col md:flex-row gap-6 items-start hover:border-emerald-500/20 transition duration-300"
                  >
                    <img
                      src={`${API_BASE}${record.image_url}`}
                      alt="Past Scan"
                      className="w-24 h-24 md:w-32 md:h-32 object-cover rounded-xl border border-slate-800"
                    />
                    <div className="flex-1 flex flex-col gap-4">
                      <div className="flex justify-between items-start flex-wrap gap-2">
                        <div>
                          <span className="text-xs text-slate-500">Scan ID: {record.id}</span>
                          <h4 className="text-sm font-semibold text-slate-300">
                            {new Date(record.timestamp).toLocaleString()}
                          </h4>
                        </div>
                        <button
                          onClick={() => {
                            setAnalysisResult(record);
                            setActiveTab("analyzer");
                          }}
                          className="px-3.5 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 text-xs font-semibold rounded-lg transition"
                        >
                          View Report
                        </button>
                      </div>
                      
                      {/* Short score badges summary */}
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(record.scores).map(([concern, val]) => {
                          const score = typeof val === "object" && val !== null ? val.score : val;
                          const label = concern === "under_eye_contrast" ? "under-eye" : concern;
                          return (
                            <div key={concern} className="bg-slate-950/60 border border-slate-850 px-2.5 py-1 rounded-lg text-xs">
                              <span className="text-slate-400 capitalize">{label.replace(/_/g, " ")}: </span>
                              <span className="font-bold text-slate-200">{score}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Modern Footer */}
      <footer className="w-full border-t border-slate-900 mt-20 bg-slate-950 py-8">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© 2026 SkinCV Project. Built for HackZen 2026 Open Challenge.</p>
          <div className="flex gap-4">
            <span className="flex items-center gap-1"><Award className="w-3.5 h-3.5 text-emerald-500" /> Inclusive Design</span>
            <span className="flex items-center gap-1"><ShieldAlert className="w-3.5 h-3.5 text-emerald-500" /> Data Privacy First</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
