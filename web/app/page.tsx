"use client";

import { useState } from "react";
import Head from "next/head";

export default function Home() {
  const [ticker, setTicker] = useState("NVDA");
  const [mode, setMode] = useState("deep");
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState<any>(null);
  const [error, setError] = useState("");

  const runAnalysis = async () => {
    if (!ticker) return;
    setLoading(true);
    setError("");
    setReportData(null);
    try {
      const res = await fetch("http://localhost:8000/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker, mode, filing_year: 2023 }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Analysis failed");
      setReportData(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatB = (v: number) => {
    if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
    if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(2)}M`;
    return `$${v.toLocaleString()}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0f1117] via-[#1a1d2e] to-[#0f1117] text-white p-6 font-sans">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-[300px_1fr] gap-8">
        
        {/* Sidebar */}
        <aside className="bg-gradient-to-b from-[#12151f] to-[#1a1d2e] border-r border-indigo-500/20 p-6 rounded-2xl h-fit">
          <h2 className="text-xl font-bold mb-1">🌳 Quant Agent</h2>
          <p className="text-slate-500 text-sm mb-6">Financial Intelligence Platform</p>
          <hr className="border-indigo-500/20 mb-6" />

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Ticker Symbol</label>
              <input 
                type="text" 
                value={ticker} 
                onChange={e => setTicker(e.target.value.toUpperCase())}
                className="w-full bg-[#0f1117] border border-indigo-500/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500"
                placeholder="AAPL, NVDA..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Analysis Mode</label>
              <div className="space-y-2">
                <label className="flex items-center space-x-2">
                  <input type="radio" checked={mode==="quick"} onChange={() => setMode("quick")} className="text-indigo-500" />
                  <span className="text-sm">⚡ Quick (Groq)</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input type="radio" checked={mode==="deep"} onChange={() => setMode("deep")} className="text-indigo-500" />
                  <span className="text-sm">🔬 Deep (GLM-4.7 + DCF)</span>
                </label>
              </div>
            </div>

            <button 
              onClick={runAnalysis}
              disabled={loading}
              className="w-full mt-6 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white font-semibold py-3 px-4 rounded-xl transition-all disabled:opacity-50"
            >
              {loading ? "Running..." : "🚀 Run Analysis"}
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main>
          {/* Hero */}
          <div className="bg-gradient-to-br from-indigo-500 via-purple-500 to-cyan-500 p-8 rounded-2xl mb-8 relative overflow-hidden">
            <h1 className="text-3xl font-bold text-white relative z-10">🌳 Quant Agent · Financial Intelligence</h1>
            <p className="text-white/80 mt-2 relative z-10">AI-powered equity research · KPI analysis · RAG risk assessment · DCF valuation</p>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-4 rounded-xl mb-8">
              ❌ {error}
            </div>
          )}

          {!reportData && !loading && (
            <div className="text-center py-20 text-slate-400">
              <div className="text-6xl mb-4">📈</div>
              <h3 className="text-xl font-semibold text-slate-300">Enter a ticker and click Run Analysis</h3>
              <p className="mt-2 max-w-md mx-auto text-sm">
                The AI agent will fetch live financials, retrieve risk sections from the vector store, run DCF valuation, and generate a structured equity research report.
              </p>
            </div>
          )}

          {loading && (
             <div className="text-center py-20 text-indigo-400 animate-pulse">
               <div className="loader inline-block w-8 h-8 rounded-full border-4 border-indigo-400 border-t-transparent animate-spin mb-4"></div>
               <p>Orchestrating AI Agents. This takes 30-40 seconds...</p>
             </div>
          )}

          {reportData && !loading && (
            <div className="animate-in fade-in duration-500 space-y-8">
              
              {/* Financial KPIs */}
              <div>
                <h2 className="text-xl font-semibold text-purple-300 border-b border-indigo-500/20 pb-2 mb-4">📊 Financial KPIs</h2>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-indigo-500/5 border border-indigo-500/20 rounded-xl p-5 hover:-translate-y-1 transition-transform">
                     <p className="text-slate-400 uppercase text-xs font-semibold tracking-wider">Revenue (Latest)</p>
                     <p className="text-2xl font-bold mt-1 text-slate-100">{formatB(reportData.financials?.revenue_latest || 0)}</p>
                     <p className={`text-sm mt-1 ${(reportData.financials?.yoy_growth||0)>=0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {(reportData.financials?.yoy_growth||0)>=0 ? '▲' : '▼'} {Math.abs((reportData.financials?.yoy_growth||0)*100).toFixed(1)}% YoY
                     </p>
                  </div>
                  <div className="bg-indigo-500/5 border border-indigo-500/20 rounded-xl p-5 hover:-translate-y-1 transition-transform">
                     <p className="text-slate-400 uppercase text-xs font-semibold tracking-wider">Revenue (Prev)</p>
                     <p className="text-2xl font-bold mt-1 text-slate-100">{formatB(reportData.financials?.revenue_prev || 0)}</p>
                     <p className="text-sm mt-1 text-slate-500">Prior Year</p>
                  </div>
                  <div className="bg-indigo-500/5 border border-indigo-500/20 rounded-xl p-5 hover:-translate-y-1 transition-transform">
                     <p className="text-slate-400 uppercase text-xs font-semibold tracking-wider">Op Income</p>
                     <p className="text-2xl font-bold mt-1 text-slate-100">{formatB(reportData.financials?.op_income_latest || 0)}</p>
                     <p className="text-sm mt-1 text-slate-500">Latest Year</p>
                  </div>
                  <div className="bg-indigo-500/5 border border-indigo-500/20 rounded-xl p-5 hover:-translate-y-1 transition-transform">
                     <p className="text-slate-400 uppercase text-xs font-semibold tracking-wider">Op Margin</p>
                     <p className="text-2xl font-bold mt-1 text-slate-100">{((reportData.financials?.op_margin_latest || 0) * 100).toFixed(1)}%</p>
                  </div>
                </div>
              </div>

              {/* Peer Comparison (if deep mode) */}
              {mode === "deep" && reportData.report?.peer_comparison && (
                <div>
                  <h2 className="text-xl font-semibold text-cyan-300 border-b border-indigo-500/20 pb-2 mb-4">
                    🔬 Peer Comparison 
                    <span className="text-sm font-normal text-cyan-500/80 ml-2">
                      vs {reportData.report.peer_comparison.peers?.join(" · ") || "Peers"}
                    </span>
                  </h2>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-xl p-5 text-center flex flex-col justify-center">
                      <p className="text-cyan-400 uppercase text-[10px] sm:text-xs font-semibold tracking-wider">{ticker} Op. Margin</p>
                      <p className="text-xl sm:text-2xl font-bold mt-1 text-slate-100">{((reportData.report.peer_comparison.company_operating_margin || 0) * 100).toFixed(1)}%</p>
                    </div>
                    <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-xl p-5 text-center flex flex-col justify-center">
                      <p className="text-cyan-400 uppercase text-[10px] sm:text-xs font-semibold tracking-wider">vs Peer Avg</p>
                      <p className={`text-xl sm:text-2xl font-bold mt-1 ${(reportData.report.peer_comparison.company_operating_margin || 0) - (reportData.report.peer_comparison.avg_peer_operating_margin || 0) >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {((reportData.report.peer_comparison.company_operating_margin || 0) - (reportData.report.peer_comparison.avg_peer_operating_margin || 0) >= 0 ? "+" : "")}
                        {(((reportData.report.peer_comparison.company_operating_margin || 0) - (reportData.report.peer_comparison.avg_peer_operating_margin || 0)) * 100).toFixed(1)}pp
                      </p>
                    </div>
                    {reportData.report.peer_comparison.peers?.map((peerTicker: string) => (
                      <div key={peerTicker} className="bg-cyan-500/5 border border-cyan-500/20 rounded-xl p-5 text-center flex flex-col justify-center">
                        <p className="text-slate-400 uppercase text-[10px] sm:text-xs font-semibold tracking-wider">{peerTicker} Op. Margin</p>
                        <p className="text-xl sm:text-2xl font-bold mt-1 text-slate-100">{((reportData.report.peer_comparison.peer_margins?.[peerTicker] || 0) * 100).toFixed(1)}%</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Thesis (if deep mode) */}
              {mode === "deep" && reportData.report?.thesis && (
                <div>
                  <h2 className="text-xl font-semibold text-purple-300 border-b border-indigo-500/20 pb-2 mb-4">💡 Investment Thesis</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                     <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-6">
                        <h4 className="text-emerald-400 font-bold mb-2">🟢 Bull Case</h4>
                        <p className="text-sm text-slate-300 leading-relaxed">{reportData.report.thesis.bull_case}</p>
                     </div>
                     <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6">
                        <h4 className="text-red-400 font-bold mb-2">🔴 Bear Case</h4>
                        <p className="text-sm text-slate-300 leading-relaxed">{reportData.report.thesis.bear_case}</p>
                     </div>
                  </div>
                </div>
              )}

              {/* Risks */}
              {reportData.report?.risk_assessment && (
                <div>
                  <h2 className="text-xl font-semibold text-purple-300 border-b border-indigo-500/20 pb-2 mb-4">⚠️ Risk Assessment</h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                     <div>
                       <h4 className="font-semibold mb-3">🏭 Industry Risks</h4>
                       <div className="flex flex-wrap gap-2">
                         {reportData.report.risk_assessment.industry_risks?.map((r: string, i: number) => (
                           <span key={i} className="bg-red-500/10 border border-red-500/20 text-red-300 text-xs px-3 py-1 rounded-full">{r}</span>
                         ))}
                       </div>
                     </div>
                     <div>
                       <h4 className="font-semibold mb-3">⚙️ Operational Risks</h4>
                       <div className="flex flex-wrap gap-2">
                         {reportData.report.risk_assessment.operational_risks?.map((r: string, i: number) => (
                           <span key={i} className="bg-red-500/10 border border-red-500/20 text-red-300 text-xs px-3 py-1 rounded-full">{r}</span>
                         ))}
                       </div>
                     </div>
                     <div>
                       <h4 className="font-semibold mb-3">📋 Regulatory Risks</h4>
                       <div className="flex flex-wrap gap-2">
                         {reportData.report.risk_assessment.regulatory_risks?.map((r: string, i: number) => (
                           <span key={i} className="bg-red-500/10 border border-red-500/20 text-red-300 text-xs px-3 py-1 rounded-full">{r}</span>
                         ))}
                       </div>
                     </div>
                  </div>
                </div>
              )}

              {/* Citations */}
              {reportData.report?.citations?.length > 0 && (
                <div>
                  <h2 className="text-xl font-semibold text-purple-300 border-b border-indigo-500/20 pb-2 mb-4">📌 Source Citations</h2>
                  <div className="space-y-3">
                     {reportData.report.citations.map((cite: any, i: number) => (
                        <div key={i} className="bg-indigo-500/5 border-l-2 border-indigo-400 pl-4 py-2 text-sm text-slate-300">
                           <span className="text-indigo-400 font-semibold mb-1 block">[{i+1}] {cite.source} — Relevance: {cite.relevance_score?.toFixed(3)}</span>
                           {cite.excerpt}
                        </div>
                     ))}
                  </div>
                </div>
              )}

            </div>
          )}
        </main>
      </div>
    </div>
  );
}
