"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { IconBarChart, IconRocket, IconSpinner, IconHistory, IconLink } from "./icons";
import React from "react";

interface SidebarProps {
  ticker?: string;
  setTicker?: (t: string) => void;
  runAnalysis?: (overrideTicker?: string) => void;
  loading?: boolean;
  history?: string[];
  popularTickers?: string[];
}

export default function Sidebar({
  ticker,
  setTicker,
  runAnalysis,
  loading,
  history,
  popularTickers,
}: SidebarProps) {
  const pathname = usePathname();

  return (
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
        <Link href="/" style={{ textDecoration: "none" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.15rem" }}>
            <IconBarChart size={20} style={{ color: "var(--cta)" } as React.CSSProperties} />
            <span style={{ fontSize: "1.05rem", fontWeight: 800, color: "var(--fg)" }}>Quant Agent</span>
          </div>
        </Link>
        <p style={{ fontSize: "0.73rem", color: "var(--fg-muted)", marginLeft: "1.75rem" }}>
          Financial Intelligence Platform
        </p>
      </div>

      <hr className="divider" style={{ margin: "0" }} />

      {/* Navigation */}
      <nav style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        <Link href="/" style={{
          textDecoration: "none",
          padding: "0.5rem 0.75rem",
          borderRadius: "var(--radius-sm)",
          background: pathname === "/" ? "rgba(118,171,174,0.15)" : "transparent",
          color: pathname === "/" ? "var(--cta)" : "var(--fg)",
          fontWeight: pathname === "/" ? 600 : 400,
          display: "block"
        }}>
          Dashboard
        </Link>
        <Link href="/doc" style={{
          textDecoration: "none",
          padding: "0.5rem 0.75rem",
          borderRadius: "var(--radius-sm)",
          background: pathname === "/doc" ? "rgba(118,171,174,0.15)" : "transparent",
          color: pathname === "/doc" ? "var(--cta)" : "var(--fg)",
          fontWeight: pathname === "/doc" ? 600 : 400,
          display: "block"
        }}>
          Architecture & Docs
        </Link>
      </nav>

      <hr className="divider" style={{ margin: "0" }} />

      {/* Resources */}
      <div>
        <p className="section-label">Resources</p>
        <a 
          href="https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm" 
          target="_blank" 
          rel="noopener noreferrer"
          style={{
            display: "flex", alignItems: "center", gap: "0.5rem",
            textDecoration: "none",
            padding: "0.5rem 0.75rem",
            borderRadius: "var(--radius-sm)",
            color: "var(--fg)",
            fontSize: "0.85rem",
            background: "rgba(255, 255, 255, 0.03)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            transition: "all 0.2s"
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = "var(--accent)";
            e.currentTarget.style.background = "rgba(255, 255, 255, 0.08)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
            e.currentTarget.style.background = "rgba(255, 255, 255, 0.03)";
          }}
        >
          <IconLink size={14} style={{ color: "var(--accent)" } as React.CSSProperties} />
          Sample 10-K (APPLE)
        </a>
      </div>

      {setTicker && runAnalysis && (
        <>
          <hr className="divider" style={{ margin: "0" }} />

          {/* Ticker Input */}
          <div>
            <p className="section-label">Ticker Symbol</p>
            <input
              className="field-input"
              type="text"
              value={ticker || ""}
              onChange={e => setTicker(e.target.value.toUpperCase())}
              onKeyDown={e => e.key === "Enter" && runAnalysis()}
              placeholder="e.g. AAPL, TSLA, RELIANCE.NS"
            />
            {/* Popular chips */}
            {popularTickers && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", marginTop: "0.6rem" }}>
                {popularTickers.map(t => (
                  <button key={t} className="chip" onClick={() => setTicker(t)}>
                    {t}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Run Button */}
          <button className="btn-cta" onClick={() => runAnalysis()} disabled={loading}>
            {loading ? <IconSpinner size={16} /> : <IconRocket size={16} />}
            {loading ? "Running Analysis..." : "Run Analysis"}
          </button>

        
        </>
      )}

      <div style={{ flex: 1 }} />
      <div style={{
        marginTop: "1.5rem",
        paddingTop: "1.5rem",
        borderTop: "1px solid rgba(118,171,174,0.15)",
        textAlign: "center",
      }}>
        <p style={{ fontSize: "0.85rem", color: "var(--fg-muted)", lineHeight: 1.5 }}>
          Developed by <span style={{ color: "var(--accent)", fontWeight: 600, letterSpacing: "0.02em" }}>Mohit Aggarwal</span>
        </p>
      </div>
    </aside>
  );
}
