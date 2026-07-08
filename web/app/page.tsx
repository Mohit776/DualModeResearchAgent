"use client";

import { useState, useRef, useEffect, useCallback, Fragment } from "react";
import {
  IconChart, IconShield, IconUsers, IconCalc, IconBulb, IconSearch,
  IconRocket, IconDownload, IconTrendingUp, IconTrendingDown,
  IconCheck, IconWarning, IconSpinner, IconHistory,
  IconBarChart, IconChevronDown, IconChevronUp, IconLink,
} from "./icons";
import Chatbot from "./Chatbot";

// ── Types ─────────────────────────────────────────────────────────────────────

interface FinancialData {
  revenue_latest?: number;
  revenue_prev?: number;
  yoy_growth?: number;
  op_income_latest?: number;
  op_margin_latest?: number;
  op_margin_prev?: number;
  latest_period?: string;
  prev_period?: string;
}

interface ReportData {
  ticker?: string;

  financial_overview?: { revenue_growth?: string; operating_margin_trend?: string };
  risk_assessment?: { industry_risks?: string[]; operational_risks?: string[]; regulatory_risks?: string[] };
  peer_comparison?: {
    peers?: string[];
    peer_margins?: Record<string, number>;
    avg_peer_operating_margin?: number;
    company_operating_margin?: number;
  };
  dcf_valuation?: { enterprise_value?: number; equity_value?: number; implied_share_price?: number; error?: string };
  wacc_analysis?: {
    wacc_pct?: string;
    wacc?: number;
    breakdown?: { cost_of_equity?: number; cost_of_debt?: number; equity_weight?: number; debt_weight?: number };
  };
  sensitivity_analysis?: {
    implied_prices?: Record<string, Record<string, number>>;
    base_case?: { wacc?: string; terminal_growth?: string };
  };
  thesis?: { bull_case?: string; bear_case?: string };
  senior_analyst_review?: { approved?: boolean; feedback?: string; revision_cycles?: number };
  investment_conclusion?: {
    overall_confidence?: string;
    confidence_score?: number;
    recommended_action?: string;
    conclusion?: string;
  };
  citations?: Array<{ source?: string; chunk_index?: number; relevance_score?: number; excerpt?: string }>;
}

interface ApiResponse {
  success?: boolean;
  ticker?: string;

  filing_year?: number;
  financials?: FinancialData;
  report?: ReportData;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const POPULAR_TICKERS = ["AAPL", "NVDA", "TSLA", "MSFT", "RELIANCE.NS"];
const HISTORY_KEY = "qa_history";
const MAX_HISTORY = 5;


const STEPS_DEEP = [
  "Fetching financial data from Polygon",
  "Analyzing KPIs with deep model",
  "Retrieving 10-K excerpts (hybrid search)",
  "Summarizing risk factors",
  "Discovering & comparing industry peers",
  "Running DCF / WACC valuation",
  "Generating investment thesis",
  "Senior Analyst reviewing report",
  "Computing confidence-weighted conclusion",
  "Assembling final investment memo",
];

const TABS = [
  { id: "financials", label: "Financials",  Icon: IconChart   },
  { id: "risks",      label: "Risks",       Icon: IconShield  },
  { id: "peers",      label: "Peers",       Icon: IconUsers   },
  { id: "valuation",  label: "Valuation",   Icon: IconCalc    },
  { id: "thesis",     label: "Thesis",      Icon: IconBulb    },
  { id: "review",     label: "Review",      Icon: IconSearch  },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtB(v: number): string {
  if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(2)}M`;
  return `$${v.toLocaleString()}`;
}

function clamp(v: number, min: number, max: number) {
  return Math.min(max, Math.max(min, v));
}

function sensColor(v: number, min: number, max: number): string {
  const t = max === min ? 0.5 : clamp((v - min) / (max - min), 0, 1);
  // danger (#e05c5c) → warn (#e8a838) → success (#4caf7d)
  if (t < 0.5) {
    const r = Math.round(224 + (232 - 224) * (t * 2));
    const g = Math.round(92  + (168 - 92)  * (t * 2));
    const b = Math.round(92  + (56  - 92)  * (t * 2));
    return `rgb(${r},${g},${b})`;
  } else {
    const r = Math.round(232 + (76  - 232) * ((t - 0.5) * 2));
    const g = Math.round(168 + (175 - 168) * ((t - 0.5) * 2));
    const b = Math.round(56  + (125 - 56)  * ((t - 0.5) * 2));
    return `rgb(${r},${g},${b})`;
  }
}

function confidenceColor(level: string) {
  if (level === "HIGH")   return "var(--success)";
  if (level === "MEDIUM") return "var(--warn)";
  return "var(--danger)";
}

function actionLabel(action: string): { text: string; color: string; bg: string } {
  const map: Record<string, { text: string; color: string; bg: string }> = {
    BUY:              { text: "BUY",              color: "var(--success)", bg: "rgba(76,175,125,0.15)" },
    SELL:             { text: "SELL",             color: "var(--danger)",  bg: "rgba(224,92,92,0.15)"  },
    HOLD:             { text: "HOLD",             color: "var(--warn)",    bg: "rgba(232,168,56,0.15)" },
    FURTHER_RESEARCH: { text: "FURTHER RESEARCH", color: "var(--accent)",  bg: "rgba(118,171,174,0.12)"},
  };
  return map[action] ?? map["HOLD"];
}

// ── Sub-components ────────────────────────────────────────────────────────────

function MetricCard({
  label, value, delta, deltaLabel, positive,
}: { label: string; value: string; delta?: string; deltaLabel?: string; positive?: boolean }) {
  return (
    <div className="metric-card">
      <p className="section-label" style={{ marginBottom: "0.35rem" }}>{label}</p>
      <p style={{ fontSize: "1.55rem", fontWeight: 700, color: "var(--fg)", lineHeight: 1.2 }}>{value}</p>
      {delta !== undefined && (
        <div style={{ display: "flex", alignItems: "center", gap: "0.3rem", marginTop: "0.4rem" }}>
          {positive
            ? <IconTrendingUp size={14} style={{ color: "var(--success)" } as React.CSSProperties} />
            : <IconTrendingDown size={14} style={{ color: "var(--danger)" } as React.CSSProperties} />}
          <span style={{ fontSize: "0.8rem", fontWeight: 600, color: positive ? "var(--success)" : "var(--danger)" }}>
            {delta}
          </span>
          {deltaLabel && <span style={{ fontSize: "0.78rem", color: "var(--fg-muted)" }}>{deltaLabel}</span>}
        </div>
      )}
    </div>
  );
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <h2 style={{
      fontSize: "0.8rem", fontWeight: 700, letterSpacing: "0.08em",
      textTransform: "uppercase", color: "var(--accent)",
      borderBottom: "1px solid rgba(118,171,174,0.18)",
      paddingBottom: "0.5rem", marginBottom: "1rem",
    }}>
      {children}
    </h2>
  );
}

function EmptyState({ label }: { label: string }) {
  return <p style={{ color: "var(--fg-muted)", fontSize: "0.85rem", fontStyle: "italic" }}>{label}</p>;
}

// ── Revenue Bar Chart (pure CSS) ──────────────────────────────────────────────

function RevenueBarChart({ prev, latest, prevLabel, latestLabel }: {
  prev: number; latest: number; prevLabel: string; latestLabel: string;
}) {
  const max = Math.max(prev, latest, 1);
  const bars = [
    { label: prevLabel,   value: prev,   pct: (prev   / max) * 100, color: "var(--accent)" },
    { label: latestLabel, value: latest, pct: (latest / max) * 100, color: "var(--cta)"    },
  ];
  return (
    <div style={{ background: "var(--bg-sunken)", borderRadius: "var(--radius-md)", padding: "1.2rem", marginTop: "1rem" }}>
      <p className="section-label" style={{ marginBottom: "1rem" }}>Revenue Trend</p>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
        {bars.map(b => (
          <div key={b.label}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
              <span style={{ fontSize: "0.8rem", color: "var(--fg-muted)" }}>{b.label}</span>
              <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--fg)" }}>{fmtB(b.value)}</span>
            </div>
            <div style={{ background: "rgba(255,255,255,0.06)", borderRadius: "99px", height: "8px", overflow: "hidden" }}>
              <div style={{
                width: `${b.pct}%`, height: "100%", background: b.color,
                borderRadius: "99px", transition: "width 0.8s ease",
              }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Confidence Score Arc (pure CSS conic-gradient) ────────────────────────────

function ScoreGauge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const deg = Math.round(score * 360);
  return (
    <div style={{ position: "relative", width: 80, height: 80, flexShrink: 0 }}>
      <div style={{
        width: 80, height: 80, borderRadius: "50%",
        background: `conic-gradient(var(--cta) 0deg ${deg}deg, rgba(255,87,34,0.15) ${deg}deg 360deg)`,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        <div style={{
          width: 58, height: 58, borderRadius: "50%",
          background: "var(--bg-sunken)",
          display: "flex", alignItems: "center", justifyContent: "center",
          flexDirection: "column",
        }}>
          <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "var(--fg)", lineHeight: 1 }}>{pct}</span>
          <span style={{ fontSize: "0.6rem", color: "var(--fg-muted)", lineHeight: 1 }}>/ 100</span>
        </div>
      </div>
    </div>
  );
}

// ── Sensitivity Grid ──────────────────────────────────────────────────────────

function SensitivityGrid({ data, baseCase }: {
  data: Record<string, Record<string, number>>;
  baseCase?: { wacc?: string; terminal_growth?: string };
}) {
  const waccKeys = Object.keys(data);
  if (!waccKeys.length) return <EmptyState label="No sensitivity data available." />;
  const tgKeys = Object.keys(data[waccKeys[0]] || {});
  const allValues = waccKeys.flatMap(w => tgKeys.map(t => data[w]?.[t] ?? 0));
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);

  return (
    <div style={{ overflowX: "auto" }}>
      <div style={{
        display: "grid",
        gridTemplateColumns: `80px repeat(${tgKeys.length}, 1fr)`,
        gap: "2px", fontSize: "0.75rem",
      }}>
        {/* Header row */}
        <div className="sens-cell" style={{ color: "var(--fg-muted)", textAlign: "right" }}>WACC \ TGR</div>
        {tgKeys.map(t => (
          <div key={t} className="sens-cell" style={{ color: "var(--accent)", fontWeight: 700 }}>{t}</div>
        ))}
        {/* Data rows */}
        {waccKeys.map(w => (
          <Fragment key={w}>
            <div key={`lbl-${w}`} className="sens-cell"
              style={{ color: "var(--accent)", fontWeight: 700, textAlign: "right" }}>{w}</div>
            {tgKeys.map(t => {
              const v = data[w]?.[t] ?? 0;
              const isBase = w === baseCase?.wacc && t === baseCase?.terminal_growth;
              return (
                <div key={`${w}-${t}`} className="sens-cell" style={{
                  background: sensColor(v, min, max),
                  borderRadius: "4px",
                  outline: isBase ? "2px solid var(--cta)" : "none",
                  color: "#fff",
                  textShadow: "0 1px 2px rgba(0,0,0,0.4)",
                }}>
                  ${v.toFixed(0)}
                </div>
              );
            })}
          </Fragment>
        ))}
      </div>
      <p style={{ fontSize: "0.72rem", color: "var(--fg-muted)", marginTop: "0.6rem" }}>
        Implied share price · Orange border = base case
      </p>
    </div>
  );
}

// ── WACC Breakdown ────────────────────────────────────────────────────────────

function WaccBreakdown({ breakdown, waccPct }: {
  breakdown?: { cost_of_equity?: number; cost_of_debt?: number; equity_weight?: number; debt_weight?: number };
  waccPct?: string;
}) {
  const [open, setOpen] = useState(false);
  if (!breakdown) return null;
  const items = [
    { label: "Cost of Equity",  value: `${((breakdown.cost_of_equity  ?? 0) * 100).toFixed(1)}%` },
    { label: "Cost of Debt",    value: `${((breakdown.cost_of_debt    ?? 0) * 100).toFixed(1)}%` },
    { label: "Equity Weight",   value: `${((breakdown.equity_weight   ?? 0) * 100).toFixed(0)}%` },
    { label: "Debt Weight",     value: `${((breakdown.debt_weight     ?? 0) * 100).toFixed(0)}%` },
  ];
  return (
    <div style={{ marginTop: "1rem" }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: "flex", alignItems: "center", gap: "0.4rem",
          background: "none", border: "none", cursor: "pointer",
          color: "var(--accent)", fontSize: "0.82rem", fontWeight: 600, fontFamily: "Inter, sans-serif",
          padding: 0,
        }}
      >
        {open ? <IconChevronUp size={14} /> : <IconChevronDown size={14} />}
        WACC Breakdown {waccPct ? `(${waccPct})` : ""}
      </button>
      {open && (
        <div style={{
          display: "grid", gridTemplateColumns: "1fr 1fr",
          gap: "0.75rem", marginTop: "0.75rem",
        }}>
          {items.map(i => (
            <div key={i.label} style={{
              background: "var(--bg-sunken)", borderRadius: "var(--radius-sm)",
              padding: "0.7rem 1rem",
            }}>
              <p className="section-label" style={{ marginBottom: "0.2rem" }}>{i.label}</p>
              <p style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--fg)" }}>{i.value}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Step Progress ─────────────────────────────────────────────────────────────

function StepProgress({ steps, currentStep }: { steps: string[]; currentStep: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {steps.map((s, i) => {
        const done   = i < currentStep;
        const active = i === currentStep;
        return (
          <div key={i} className={`step-row ${done ? "done" : active ? "active" : ""}`}>
            {done   ? <IconCheck   size={15} /> :
             active ? <IconSpinner size={15} /> :
             <span style={{ width: 15, height: 15, borderRadius: "50%",
               border: "1.5px solid var(--fg-muted)", display: "inline-block", flexShrink: 0 }} />}
            <span>{s}</span>
          </div>
        );
      })}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function Home() {
  const [ticker,      setTicker      ] = useState("NVDA");
  const [loading,     setLoading     ] = useState(false);
  const [currentStep, setCurrentStep ] = useState(0);
  const [reportData,  setReportData  ] = useState<ApiResponse | null>(null);
  const [error,       setError       ] = useState("");
  const [activeTab,   setActiveTab   ] = useState("financials");
  const [history,     setHistory     ] = useState<string[]>([]);
  const [waccOpen,    setWaccOpen    ] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  // Load history from localStorage
  useEffect(() => {
    try {
      const h = JSON.parse(localStorage.getItem(HISTORY_KEY) ?? "[]");
      setHistory(Array.isArray(h) ? h : []);
    } catch { setHistory([]); }
  }, []);

  const pushHistory = useCallback((t: string) => {
    setHistory(prev => {
      const next = [t, ...prev.filter(x => x !== t)].slice(0, MAX_HISTORY);
      localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  // Simulate step progression while loading (ticks every ~3s)
  useEffect(() => {
    if (!loading) { setCurrentStep(0); return; }
    const steps = STEPS_DEEP;
    const interval = setInterval(() => {
      setCurrentStep(s => (s < steps.length - 1 ? s + 1 : s));
    }, 3500);
    return () => clearInterval(interval);
  }, [loading]);

  const runAnalysis = async (overrideTicker?: string) => {
    const t = (overrideTicker ?? ticker).toUpperCase().trim();
    if (!t) return;
    setLoading(true);
    setError("");
    setReportData(null);
    setCurrentStep(0);
    setActiveTab("financials");

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

      const res = await fetch(`${apiUrl}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: t }),
      });
      const data: ApiResponse = await res.json();
      if (!res.ok) throw new Error((data as any).detail ?? "Analysis failed");
      setReportData(data);
      pushHistory(t);
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    } catch (err: any) {
      setError(err.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const exportJSON = () => {
    if (!reportData) return;
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${reportData.ticker ?? "report"}_quant_agent.json`;
    a.click(); URL.revokeObjectURL(url);
  };

  const fin   = reportData?.financials ?? {};
  const report = reportData?.report ?? {};
  const yoy    = (fin.yoy_growth ?? 0) * 100;
  const opm    = (fin.op_margin_latest ?? 0) * 100;
  const opmPrev= (fin.op_margin_prev  ?? 0) * 100;
  const opmDelta = opm - opmPrev;
  const lyLabel  = String(fin.latest_period ?? "Latest").slice(0, 4);
  const pyLabel  = String(fin.prev_period   ?? "Prev"  ).slice(0, 4);
  const steps    = STEPS_DEEP;
  const conf     = report.investment_conclusion;
  const confLevel= conf?.overall_confidence ?? "MEDIUM";
  const confScore= conf?.confidence_score ?? 0.5;
  const action   = actionLabel(conf?.recommended_action ?? "HOLD");

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-sunken)", display: "flex" }}>

      {/* ── Sidebar ── */}
      <aside style={{
        width: 280, flexShrink: 0,
        background: "var(--bg)",
        borderRight: "1px solid rgba(118,171,174,0.15)",
        padding: "1.5rem 1.25rem",
        display: "flex", flexDirection: "column", gap: "1.2rem",
        position: "sticky", top: 0, height: "100vh", overflowY: "auto",
      }}>
        {/* Logo */}
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.15rem" }}>
            <IconBarChart size={20} style={{ color: "var(--cta)" } as React.CSSProperties} />
            <span style={{ fontSize: "1.05rem", fontWeight: 800, color: "var(--fg)" }}>Quant Agent</span>
          </div>
          <p style={{ fontSize: "0.73rem", color: "var(--fg-muted)", marginLeft: "1.75rem" }}>
            Financial Intelligence Platform
          </p>
        </div>

        <hr className="divider" style={{ margin: "0" }} />

        {/* Ticker Input */}
        <div>
          <p className="section-label">Ticker Symbol</p>
          <input
            className="field-input"
            type="text"
            value={ticker}
            onChange={e => setTicker(e.target.value.toUpperCase())}
            onKeyDown={e => e.key === "Enter" && runAnalysis()}
            placeholder="e.g. AAPL, TSLA, RELIANCE.NS"
          />
          {/* Popular chips */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", marginTop: "0.6rem" }}>
            {POPULAR_TICKERS.map(t => (
              <button key={t} className="chip" onClick={() => { setTicker(t); }}>
                {t}
              </button>
            ))}
          </div>
        </div>





        {/* Run Button */}
        <button className="btn-cta" onClick={() => runAnalysis()} disabled={loading}>
          {loading ? <IconSpinner size={16} /> : <IconRocket size={16} />}
          {loading ? "Running Analysis..." : "Run Analysis"}
        </button>

        {/* History */}
        {history.length > 0 && (
          <div>
            <p className="section-label" style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
              <IconHistory size={12} /> Recent
            </p>
            {history.map(h => (
              <div key={h} className="history-item" onClick={() => { setTicker(h); runAnalysis(h); }}>
                <IconLink size={12} style={{ color: "var(--accent)", flexShrink: 0 } as React.CSSProperties} />
                {h}
              </div>
            ))}
          </div>
        )}

        <div style={{ flex: 1 }} />
        <p style={{ fontSize: "0.68rem", color: "var(--fg-muted)", lineHeight: 1.5 }}>
          Powered by Groq · Qdrant · LangGraph
        </p>
      </aside>

      {/* ── Main Content ── */}
      <main style={{ flex: 1, padding: "1.75rem 2rem", overflowX: "hidden" }}>

        {/* Hero */}
        <div style={{
          background: "var(--bg)",
          border: "1px solid rgba(118,171,174,0.18)",
          borderRadius: "var(--radius-lg)",
          padding: "2rem 2.5rem",
          marginBottom: "1.75rem",
          position: "relative", overflow: "hidden",
        }}>
          {/* Shimmer sweep */}
          <div style={{
            position: "absolute", inset: 0, overflow: "hidden", borderRadius: "inherit", pointerEvents: "none",
          }}>
            <div style={{
              position: "absolute", top: 0, left: "-100%", width: "60%", height: "100%",
              background: "linear-gradient(90deg, transparent, rgba(118,171,174,0.06), transparent)",
              animation: "shimmer 4s ease-in-out infinite",
            }} />
          </div>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 800, color: "var(--fg)", margin: 0 }}>
            Financial Intelligence
          </h1>
          <p style={{ color: "var(--fg-muted)", marginTop: "0.3rem", fontSize: "0.9rem" }}>
            AI-powered equity research — KPI analysis · RAG risk assessment · DCF valuation · Investment thesis
          </p>
          {reportData && (
            <div style={{
              marginTop: "1rem", display: "flex", alignItems: "center", gap: "0.6rem",
              flexWrap: "wrap",
            }}>
              <span style={{
                background: "var(--cta)", color: "#fff",
                padding: "0.25rem 0.85rem", borderRadius: "99px",
                fontSize: "0.82rem", fontWeight: 700,
              }}>
                {reportData.ticker}
              </span>

              <span style={{ display: "flex", alignItems: "center", gap: "0.3rem", color: "var(--success)", fontSize: "0.82rem" }}>
                <IconCheck size={14} /> Analysis complete
              </span>
              <div style={{ marginLeft: "auto" }}>
                <button className="btn-secondary" onClick={exportJSON}>
                  <IconDownload size={14} /> Export JSON
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Error Banner */}
        {error && (
          <div style={{
            background: "rgba(224,92,92,0.1)",
            border: "1px solid rgba(224,92,92,0.35)",
            borderRadius: "var(--radius-md)",
            padding: "1rem 1.25rem",
            marginBottom: "1.5rem",
            display: "flex", alignItems: "center", gap: "0.6rem",
            color: "#f09090", fontSize: "0.9rem",
          }}>
            <IconWarning size={18} />
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div style={{
            background: "var(--bg)",
            border: "1px solid rgba(118,171,174,0.18)",
            borderRadius: "var(--radius-lg)",
            padding: "2rem 2.5rem",
            animation: "fadeIn 0.3s ease",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "1.5rem" }}>
              <IconSpinner size={20} style={{ color: "var(--accent)" } as React.CSSProperties} />
              <span style={{ fontWeight: 600, color: "var(--fg)" }}>
                Orchestrating AI Agents for {ticker}
              </span>
            </div>
            <StepProgress steps={steps} currentStep={currentStep} />
            <p style={{ marginTop: "1.2rem", fontSize: "0.8rem", color: "var(--fg-muted)" }}>
              Deep mode takes 30–60 seconds.
            </p>
          </div>
        )}

        {/* Landing placeholder */}
        {!loading && !reportData && !error && (
          <div style={{ animation: "fadeIn 0.4s ease" }}>
            <div style={{ textAlign: "center", padding: "3rem 0", color: "var(--fg-muted)", marginBottom: "2rem" }}>
              <IconBarChart size={56} style={{ margin: "0 auto 1rem", color: "var(--accent)", opacity: 0.4 } as React.CSSProperties} />
              <h3 style={{ color: "var(--fg)", fontWeight: 700, marginBottom: "0.5rem" }}>
                Enter a ticker and click Run Analysis
              </h3>
              <p style={{ maxWidth: 480, margin: "0 auto", fontSize: "0.875rem", lineHeight: 1.7 }}>
                The AI agent fetches live financials, retrieves 10-K risk sections from the vector store,
                runs a deterministic DCF valuation, and generates a structured equity research report.
                Supports US (NYSE/NASDAQ) and Indian stocks (.NS / .BO).
              </p>
            </div>
            {/* Feature grid */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
              {[
                { Icon: IconChart,  title: "AI-Powered",      desc: "Groq for fast execution and high reasoning." },
                { Icon: IconSearch, title: "Hybrid RAG",         desc: "Dense + sparse vectors in Qdrant with metadata grounding. Zero cross-contamination." },
                { Icon: IconCalc,   title: "DCF Valuation",      desc: "Deterministic DCF, WACC, and sensitivity analysis. No LLM math guessing." },
                { Icon: IconShield, title: "Reflection Loop",    desc: "Senior Analyst AI reviews for contradictions and hallucinations before finalizing." },
                { Icon: IconBulb,   title: "Investment Thesis",  desc: "Bull and bear cases with confidence-weighted conclusions and traceable citations." },
                { Icon: IconUsers,  title: "Peer Comparison",    desc: "Auto-discovers industry peers and compares operating margins side by side." },
              ].map(({ Icon, title, desc }) => (
                <div key={title} className="metric-card" style={{ textAlign: "center", padding: "1.5rem" }}>
                  <Icon size={28} style={{ margin: "0 auto 0.75rem", color: "var(--accent)" } as React.CSSProperties} />
                  <p style={{ fontWeight: 700, color: "var(--fg)", marginBottom: "0.4rem" }}>{title}</p>
                  <p style={{ fontSize: "0.8rem", color: "var(--fg-muted)", lineHeight: 1.6 }}>{desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Results ── */}
        {reportData && !loading && (
          <div ref={resultsRef} style={{ animation: "slideUp 0.45s ease" }}>

            {/* Confidence Banner (deep mode) */}
            {conf && (
              <div style={{
                background: `linear-gradient(135deg, ${action.bg}, rgba(48,56,65,0.5))`,
                border: `1px solid ${action.color}30`,
                borderRadius: "var(--radius-lg)",
                padding: "1.5rem 2rem",
                marginBottom: "1.5rem",
                display: "flex", alignItems: "center", gap: "1.5rem", flexWrap: "wrap",
              }}>
                <ScoreGauge score={confScore} />
                <div style={{ flex: 1 }}>
                  <p className="section-label" style={{ color: "var(--fg-muted)" }}>Recommended Action</p>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginTop: "0.3rem", flexWrap: "wrap" }}>
                    <span style={{
                      background: action.bg, color: action.color,
                      border: `1px solid ${action.color}50`,
                      padding: "0.3rem 1rem", borderRadius: "99px",
                      fontWeight: 800, fontSize: "1rem", letterSpacing: "0.04em",
                    }}>
                      {action.text}
                    </span>
                    <span style={{
                      background: `${confidenceColor(confLevel)}15`,
                      color: confidenceColor(confLevel),
                      border: `1px solid ${confidenceColor(confLevel)}40`,
                      padding: "0.25rem 0.7rem", borderRadius: "99px",
                      fontSize: "0.78rem", fontWeight: 700, textTransform: "uppercase",
                    }}>
                      {confLevel} CONFIDENCE
                    </span>
                  </div>
                  {conf.conclusion && (
                    <p style={{ fontSize: "0.85rem", color: "var(--fg-muted)", marginTop: "0.6rem", lineHeight: 1.6 }}>
                      {conf.conclusion}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Tabs */}
            <div className="tab-bar" style={{ marginBottom: "1.5rem" }}>
              {TABS.map(({ id, label, Icon }) => (
                <button
                  key={id}
                  className={`tab-item ${activeTab === id ? "active" : ""}`}
                  onClick={() => setActiveTab(id)}
                >
                  <Icon size={14} /> {label}
                </button>
              ))}
            </div>

            {/* ── Financials Tab ── */}
            {activeTab === "financials" && (
              <div style={{ animation: "fadeIn 0.3s ease" }}>
                <SectionHeader>Financial KPIs</SectionHeader>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.85rem", marginBottom: "1.5rem" }}>
                  <MetricCard
                    label={`Revenue (${lyLabel})`}
                    value={fmtB(fin.revenue_latest ?? 0)}
                    delta={`${Math.abs(yoy).toFixed(1)}% YoY`}
                    deltaLabel={`${pyLabel} → ${lyLabel}`}
                    positive={yoy >= 0}
                  />
                  <MetricCard
                    label={`Revenue (${pyLabel})`}
                    value={fmtB(fin.revenue_prev ?? 0)}
                    delta="Prior year"
                    positive={true}
                  />
                  <MetricCard
                    label={`Operating Income (${lyLabel})`}
                    value={fmtB(fin.op_income_latest ?? 0)}
                  />
                  <MetricCard
                    label={`Operating Margin (${lyLabel})`}
                    value={`${opm.toFixed(1)}%`}
                    delta={`${Math.abs(opmDelta).toFixed(1)}pp vs ${pyLabel}`}
                    positive={opmDelta >= 0}
                  />
                </div>

                {/* Revenue bar chart */}
                <RevenueBarChart
                  prev={fin.revenue_prev ?? 0}
                  latest={fin.revenue_latest ?? 0}
                  prevLabel={pyLabel}
                  latestLabel={lyLabel}
                />

                {/* AI analysis */}
                {report.financial_overview && (
                  <div style={{ marginTop: "1.5rem" }}>
                    <SectionHeader>AI Financial Analysis</SectionHeader>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                      {[
                        { label: "Revenue Growth",          key: "revenue_growth"          },
                        { label: "Operating Margin Trend",  key: "operating_margin_trend"  },
                      ].map(({ label, key }) => (
                        <div key={key} style={{
                          background: "var(--bg-raised)", borderRadius: "var(--radius-md)",
                          padding: "1.1rem 1.3rem",
                          border: "1px solid rgba(118,171,174,0.15)",
                        }}>
                          <p className="section-label" style={{ marginBottom: "0.5rem" }}>{label}</p>
                          <p style={{ fontSize: "0.875rem", color: "var(--fg-muted)", lineHeight: 1.7 }}>
                            {(report.financial_overview as any)[key] ?? "—"}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ── Risks Tab ── */}
            {activeTab === "risks" && (
              <div style={{ animation: "fadeIn 0.3s ease" }}>
                <SectionHeader>Risk Assessment</SectionHeader>
                {report.risk_assessment ? (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1.25rem" }}>
                    {[
                      { label: "Industry Risks",    items: report.risk_assessment.industry_risks    },
                      { label: "Operational Risks", items: report.risk_assessment.operational_risks },
                      { label: "Regulatory Risks",  items: report.risk_assessment.regulatory_risks  },
                    ].map(({ label, items }) => (
                      <div key={label} style={{
                        background: "var(--bg-raised)", borderRadius: "var(--radius-md)",
                        padding: "1.2rem", border: "1px solid rgba(118,171,174,0.12)",
                      }}>
                        <p className="section-label" style={{ marginBottom: "0.75rem" }}>{label}</p>
                        {items?.length ? (
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                            {items.map((r, i) => (
                              <span key={i} className="risk-pill">{r}</span>
                            ))}
                          </div>
                        ) : <EmptyState label="No data available." />}
                      </div>
                    ))}
                  </div>
                ) : <EmptyState label="No risk data in this report." />}
              </div>
            )}

            {/* ── Peers Tab ── */}
            {activeTab === "peers" && (
              <div style={{ animation: "fadeIn 0.3s ease" }}>
                {report.peer_comparison ? (() => {
                  const pc = report.peer_comparison!;
                  const diff = ((pc.company_operating_margin ?? 0) - (pc.avg_peer_operating_margin ?? 0)) * 100;
                  return (
                    <>
                      <SectionHeader>
                        Peer Comparison — vs {pc.peers?.join(" · ") || "Peers"}
                      </SectionHeader>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px,1fr))", gap: "0.85rem" }}>
                        {/* Company card */}
                        <div style={{
                          background: "rgba(118,171,174,0.1)",
                          border: "1px solid rgba(118,171,174,0.35)",
                          borderRadius: "var(--radius-md)", padding: "1.1rem",
                          textAlign: "center",
                        }}>
                          <p className="section-label">{reportData.ticker} Op. Margin</p>
                          <p style={{ fontSize: "1.6rem", fontWeight: 800, color: "var(--fg)", marginTop: "0.3rem" }}>
                            {((pc.company_operating_margin ?? 0) * 100).toFixed(1)}%
                          </p>
                        </div>
                        {/* vs Peer Avg */}
                        <div style={{
                          background: diff >= 0 ? "rgba(76,175,125,0.1)" : "rgba(224,92,92,0.1)",
                          border: `1px solid ${diff >= 0 ? "rgba(76,175,125,0.35)" : "rgba(224,92,92,0.35)"}`,
                          borderRadius: "var(--radius-md)", padding: "1.1rem",
                          textAlign: "center",
                        }}>
                          <p className="section-label">vs Peer Avg</p>
                          <p style={{
                            fontSize: "1.6rem", fontWeight: 800,
                            color: diff >= 0 ? "var(--success)" : "var(--danger)",
                            marginTop: "0.3rem",
                          }}>
                            {diff >= 0 ? "+" : ""}{diff.toFixed(1)}pp
                          </p>
                        </div>
                        {/* Each peer */}
                        {pc.peers?.map(p => (
                          <div key={p} style={{
                            background: "var(--bg-raised)",
                            border: "1px solid rgba(118,171,174,0.18)",
                            borderRadius: "var(--radius-md)", padding: "1.1rem",
                            textAlign: "center",
                          }}>
                            <p className="section-label">{p} Op. Margin</p>
                            <p style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--fg)", marginTop: "0.3rem" }}>
                              {((pc.peer_margins?.[p] ?? 0) * 100).toFixed(1)}%
                            </p>
                          </div>
                        ))}
                      </div>
                    </>
                  );
                })() : (
                  <div style={{ textAlign: "center", padding: "3rem", color: "var(--fg-muted)" }}>
                    <IconUsers size={40} style={{ margin: "0 auto 1rem", opacity: 0.3 } as React.CSSProperties} />
                    <p>Peer comparison data is not available.</p>
                  </div>
                )}
              </div>
            )}

            {/* ── Valuation Tab ── */}
            {activeTab === "valuation" && (
              <div style={{ animation: "fadeIn 0.3s ease" }}>
                {report.dcf_valuation && !report.dcf_valuation.error ? (
                  <>
                    <SectionHeader>DCF Valuation</SectionHeader>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.85rem", marginBottom: "1.5rem" }}>
                      {[
                        { label: "Enterprise Value",    value: fmtB(report.dcf_valuation.enterprise_value ?? 0) },
                        { label: "Equity Value",        value: fmtB(report.dcf_valuation.equity_value ?? 0)     },
                        { label: "Implied Share Price", value: `$${(report.dcf_valuation.implied_share_price ?? 0).toFixed(2)}` },
                        { label: "WACC",                value: report.wacc_analysis?.wacc_pct ?? "N/A"          },
                      ].map(({ label, value }) => (
                        <div key={label} style={{
                          background: "rgba(118,171,174,0.07)",
                          border: "1px solid rgba(118,171,174,0.2)",
                          borderRadius: "var(--radius-md)", padding: "1.2rem 1.4rem",
                        }}>
                          <p className="section-label" style={{ marginBottom: "0.35rem" }}>{label}</p>
                          <p style={{ fontSize: "1.45rem", fontWeight: 700, color: "var(--fg)" }}>{value}</p>
                        </div>
                      ))}
                    </div>

                    {/* WACC Breakdown */}
                    <WaccBreakdown
                      breakdown={report.wacc_analysis?.breakdown}
                      waccPct={report.wacc_analysis?.wacc_pct}
                    />

                    {/* Sensitivity */}
                    {report.sensitivity_analysis?.implied_prices && (
                      <div style={{ marginTop: "1.75rem" }}>
                        <SectionHeader>Sensitivity Analysis</SectionHeader>
                        <p style={{ fontSize: "0.8rem", color: "var(--fg-muted)", marginBottom: "0.75rem" }}>
                          Implied share price across WACC (rows) vs Terminal Growth Rate (columns)
                        </p>
                        <div style={{
                          background: "var(--bg-raised)", borderRadius: "var(--radius-md)",
                          padding: "1.25rem", border: "1px solid rgba(118,171,174,0.12)",
                        }}>
                          <SensitivityGrid
                            data={report.sensitivity_analysis.implied_prices}
                            baseCase={report.sensitivity_analysis.base_case}
                          />
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div style={{ textAlign: "center", padding: "3rem", color: "var(--fg-muted)" }}>
                    <IconCalc size={40} style={{ margin: "0 auto 1rem", opacity: 0.3 } as React.CSSProperties} />
                    <p>Valuation data is not available.</p>
                    {report.dcf_valuation?.error && (
                      <p style={{ color: "var(--danger)", marginTop: "0.5rem", fontSize: "0.85rem" }}>
                        Error: {report.dcf_valuation.error}
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ── Thesis Tab ── */}
            {activeTab === "thesis" && (
              <div style={{ animation: "fadeIn 0.3s ease" }}>
                {report.thesis ? (
                  <>
                    <SectionHeader>Investment Thesis</SectionHeader>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                      <div style={{
                        background: "rgba(76,175,125,0.08)",
                        border: "1px solid rgba(76,175,125,0.25)",
                        borderRadius: "var(--radius-md)", padding: "1.4rem",
                      }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
                          <IconTrendingUp size={18} style={{ color: "var(--success)" } as React.CSSProperties} />
                          <span style={{ fontWeight: 700, color: "var(--success)" }}>Bull Case</span>
                        </div>
                        <p style={{ fontSize: "0.875rem", color: "var(--fg-muted)", lineHeight: 1.75 }}>
                          {report.thesis.bull_case ?? "—"}
                        </p>
                      </div>
                      <div style={{
                        background: "rgba(224,92,92,0.08)",
                        border: "1px solid rgba(224,92,92,0.25)",
                        borderRadius: "var(--radius-md)", padding: "1.4rem",
                      }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
                          <IconTrendingDown size={18} style={{ color: "var(--danger)" } as React.CSSProperties} />
                          <span style={{ fontWeight: 700, color: "var(--danger)" }}>Bear Case</span>
                        </div>
                        <p style={{ fontSize: "0.875rem", color: "var(--fg-muted)", lineHeight: 1.75 }}>
                          {report.thesis.bear_case ?? "—"}
                        </p>
                      </div>
                    </div>
                  </>
                ) : (
                  <div style={{ textAlign: "center", padding: "3rem", color: "var(--fg-muted)" }}>
                    <IconBulb size={40} style={{ margin: "0 auto 1rem", opacity: 0.3 } as React.CSSProperties} />
                    <p>Investment thesis is not available.</p>
                  </div>
                )}
              </div>
            )}

            {/* ── Review Tab ── */}
            {activeTab === "review" && (
              <div style={{ animation: "fadeIn 0.3s ease" }}>
                {/* Senior Analyst Review */}
                {report.senior_analyst_review ? (() => {
                  const rev = report.senior_analyst_review!;
                  const approved = rev.approved !== false;
                  return (
                    <>
                      <SectionHeader>Senior Analyst Review</SectionHeader>
                      <div style={{
                        background: approved ? "rgba(76,175,125,0.08)" : "rgba(232,168,56,0.08)",
                        border: `1px solid ${approved ? "rgba(76,175,125,0.3)" : "rgba(232,168,56,0.3)"}`,
                        borderRadius: "var(--radius-md)", padding: "1.4rem",
                        marginBottom: "1.5rem",
                      }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.65rem", marginBottom: "0.75rem" }}>
                          {approved
                            ? <IconCheck   size={20} style={{ color: "var(--success)" } as React.CSSProperties} />
                            : <IconWarning size={20} style={{ color: "var(--warn)"    } as React.CSSProperties} />}
                          <span style={{ fontWeight: 700, fontSize: "1rem", color: approved ? "var(--success)" : "var(--warn)" }}>
                            {approved ? "Approved" : "Flagged for Review"}
                          </span>
                          <span style={{
                            marginLeft: "auto",
                            background: "rgba(255,87,34,0.15)", color: "var(--cta)",
                            border: "1px solid rgba(255,87,34,0.3)",
                            padding: "0.15rem 0.6rem", borderRadius: "99px",
                            fontSize: "0.75rem", fontWeight: 700,
                          }}>
                            {rev.revision_cycles ?? 0} revision{(rev.revision_cycles ?? 0) !== 1 ? "s" : ""}
                          </span>
                        </div>
                        <p style={{ fontSize: "0.875rem", color: "var(--fg-muted)", lineHeight: 1.7 }}>
                          {rev.feedback ?? "No feedback provided."}
                        </p>
                      </div>
                    </>
                  );
                })() : (
                  <div style={{ textAlign: "center", padding: "2rem", color: "var(--fg-muted)", marginBottom: "1.5rem" }}>
                    <p>Senior Analyst Review is not available.</p>
                  </div>
                )}

                {/* Citations */}
                {report.citations && report.citations.length > 0 && (
                  <>
                    <SectionHeader>
                      Source Citations ({report.citations.length})
                    </SectionHeader>
                    {report.citations.map((c, i) => (
                      <div key={i} className="citation-item">
                        <p className="cite-label">
                          [{i + 1}] {c.source} — Chunk #{c.chunk_index} — Relevance: {c.relevance_score?.toFixed(3)}
                        </p>
                        <p style={{ marginTop: "0.2rem" }}>{c.excerpt}</p>
                      </div>
                    ))}
                  </>
                )}
              </div>
            )}

          </div>
        )}
      </main>
      <Chatbot ticker={reportData?.ticker} reportContext={reportData?.report} />
    </div>
  );
}
