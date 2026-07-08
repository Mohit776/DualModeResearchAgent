"use client";
import Sidebar from "../Sidebar";
import React, { useState } from "react";
import {
  IconSearch, IconChart, IconShield,
  IconUsers, IconCalc, IconBulb, IconCheck, IconBarChart
} from "../icons";

// ── Tiny sub-components ──────────────────────────────────────────────────────

function Badge({ label, color }: { label: string; color: string }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center",
      background: `${color}18`, color, border: `1px solid ${color}40`,
      borderRadius: "99px", padding: "0.2rem 0.75rem",
      fontSize: "0.75rem", fontWeight: 700, letterSpacing: "0.04em",
      whiteSpace: "nowrap",
    }}>{label}</span>
  );
}

function Highlight({ children }: { children: React.ReactNode }) {
  return (
    <span style={{
      background: "rgba(118,171,174,0.15)",
      color: "var(--accent)",
      borderRadius: "4px",
      padding: "0 4px",
      fontWeight: 600,
    }}>{children}</span>
  );
}

function SectionTitle({ num, title }: { num: string; title: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1.25rem" }}>
      <div style={{
        width: 32, height: 32, borderRadius: "50%",
        background: "var(--cta)", color: "#fff",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: "0.85rem", fontWeight: 800, flexShrink: 0,
      }}>{num}</div>
      <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--fg)", margin: 0 }}>{title}</h2>
    </div>
  );
}

function FeatureCard({ icon: Icon, iconUrl, title, desc, tag, color = "#76ABAE" }: any) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered ? "var(--bg-raised)" : "var(--bg-sunken)",
        border: `1px solid ${hovered ? color + "60" : "rgba(255,255,255,0.06)"}`,
        borderRadius: "var(--radius-md)",
        padding: "1.2rem",
        display: "flex", gap: "1rem", alignItems: "flex-start",
        transition: "all 0.25s ease",
        transform: hovered ? "translateY(-2px)" : "none",
        boxShadow: hovered ? `0 8px 24px rgba(0,0,0,0.2)` : "none",
        cursor: "default",
      }}>
      <div style={{
        width: 44, height: 44, borderRadius: "10px", flexShrink: 0,
        background: `${color}18`, color,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        {iconUrl ? <img src={iconUrl} width={22} height={22} alt={title} style={{ filter: "drop-shadow(0px 2px 4px rgba(0,0,0,0.2))" }} /> : <Icon size={22} />}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.3rem" }}>
          <h3 style={{ fontSize: "0.95rem", fontWeight: 700, color: "var(--fg)", margin: 0 }}>{title}</h3>
          {tag && <Badge label={tag} color={color} />}
        </div>
        <p style={{ fontSize: "0.83rem", color: "var(--fg-muted)", lineHeight: 1.6, margin: 0 }}>{desc}</p>
      </div>
    </div>
  );
}

function PipelineStep({ step, icon: Icon, iconUrl, title, desc, color, tags = [], isLast = false, children }: any) {
  return (
    <div style={{ display: "flex", gap: "1.25rem" }}>
      {/* Left: step indicator + connector */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0 }}>
        <div style={{
          width: 48, height: 48, borderRadius: "50%",
          background: `${color}20`, border: `2px solid ${color}`,
          color, display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "0.85rem", fontWeight: 800, boxShadow: `0 0 12px ${color}30`,
        }}>
          {iconUrl ? <img src={iconUrl} width={24} height={24} alt={title} style={{ filter: "drop-shadow(0px 2px 4px rgba(0,0,0,0.2))" }} /> : <Icon size={20} />}
        </div>
        {!isLast && (
          <div style={{
            width: 2, flex: 1, minHeight: 32,
            background: `linear-gradient(to bottom, ${color}60, transparent)`,
            margin: "4px 0",
          }} />
        )}
      </div>
      {/* Right: content */}
      <div style={{ paddingBottom: isLast ? 0 : "2rem", flex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.4rem", flexWrap: "wrap" }}>
          <span style={{ fontSize: "0.7rem", color, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase" }}>
            STEP {step}
          </span>
          {tags.map((t: string) => <Badge key={t} label={t} color={color} />)}
        </div>
        <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--fg)", margin: "0 0 0.4rem 0" }}>{title}</h3>
        <p style={{ fontSize: "0.85rem", color: "var(--fg-muted)", lineHeight: 1.65, margin: 0 }}>{desc}</p>
        {children}
      </div>
    </div>
  );
}

function CalloutBox({ color, label, children }: { color: string; label: string; children: React.ReactNode }) {
  return (
    <div style={{
      background: `${color}0d`,
      border: `1px solid ${color}30`,
      borderLeft: `3px solid ${color}`,
      borderRadius: "var(--radius-sm)",
      padding: "0.9rem 1.1rem",
      marginTop: "0.75rem",
    }}>
      <p style={{ fontSize: "0.7rem", fontWeight: 800, color, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "0.3rem" }}>
        {label}
      </p>
      <p style={{ fontSize: "0.83rem", color: "var(--fg-muted)", lineHeight: 1.6, margin: 0 }}>{children}</p>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function DocPage() {
  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-sunken)", display: "flex" }}>
      <Sidebar />
      <main style={{ flex: 1, padding: "2rem 2.5rem", overflowX: "hidden" }}>
        <div style={{ maxWidth: "920px", margin: "0 auto" }}>

          {/* ── Hero ── */}
          <div style={{
            background: "var(--bg)",
            border: "1px solid rgba(118,171,174,0.18)",
            borderRadius: "var(--radius-lg)",
            padding: "2.5rem",
            marginBottom: "2rem",
            position: "relative", overflow: "hidden",
          }}>
            <div style={{ position: "absolute", top: 0, right: 0, width: 300, height: 300, borderRadius: "50%", background: "radial-gradient(circle, rgba(255,87,34,0.08) 0%, transparent 70%)", pointerEvents: "none" }} />
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
              <IconBarChart size={28} style={{ color: "var(--cta)" } as React.CSSProperties} />
              <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--cta)", letterSpacing: "0.12em", textTransform: "uppercase" }}>AI Engineer Interview — Project Walkthrough</span>
            </div>
            <h1 style={{ fontSize: "2rem", fontWeight: 800, color: "var(--fg)", margin: "0 0 0.5rem 0", lineHeight: 1.2 }}>
              Dual-Mode Financial Research Agent
            </h1>
            <p style={{ fontSize: "1rem", color: "var(--fg-muted)", margin: "0 0 1.5rem 0", lineHeight: 1.7, maxWidth: 680 }}>
              A production-grade AI system combining a <Highlight>multi-agent LangGraph workflow</Highlight>, a fully-engineered <Highlight>RAG pipeline</Highlight>, and a <Highlight>memory-augmented chatbot</Highlight> — built for high-precision equity research across US and Indian markets.
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
              {[
                ["LangGraph", "#a78bfa"],
                ["Gemini Embeddings", "#4facfe"],
                ["Qdrant Cloud", "#f093fb"],
                ["GPT-OSS 1.12B", "#43e97b"],
                ["Re-ranking", "#f6d365"],
                ["YFinance API", "#fa709a"],
                ["Logfire", "#76ABAE"],
                ["Guardrails", "#FF5722"],
                ["Memory Chatbot", "#e8a838"],
              ].map(([label, color]) => <Badge key={label} label={label} color={color} />)}
            </div>
          </div>


          {/* ── Visual Pipeline ── */}
          <div style={{
            background: "var(--bg)",
            border: "1px solid rgba(118,171,174,0.15)",
            borderRadius: "var(--radius-lg)",
            padding: "2rem 2.5rem",
            marginBottom: "2rem",
          }}>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--fg)", marginBottom: "0.4rem" }}>
              End-to-End Pipeline
            </h2>
            <p style={{ fontSize: "0.85rem", color: "var(--fg-muted)", marginBottom: "2rem" }}>
              How a single ticker request flows through the full system — from raw API call to rendered report.
            </p>
            <div style={{ display: "flex", flexDirection: "column" }}>

              <PipelineStep
                step={1} iconUrl="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" color="#4facfe"
                title="Data Ingestion — YFinance API + SEC EDGAR"
                tags={["YFinance", "SEC 10-K"]}
                desc="User submits a ticker. The backend calls the YFinance API for structured financials and fetches unstructured risk text from SEC EDGAR 10-K filings. For Indian stocks (.NS/.BO), Yahoo Finance is used directly."
              />

              <PipelineStep
                step={2} iconUrl="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/google/google-original.svg" color="#a78bfa"
                title="Gemini Embedding + Semantic Chunking"
                tags={["Gemini Embeddings", "Chunking"]}
                desc="Documents are split by semantic boundaries — not arbitrary token counts — ensuring each chunk is a coherent financial concept. Each chunk is then encoded into a dense vector using Google Gemini embedding models."
              />

              <PipelineStep
                step={3} icon={IconShield} color="#f093fb"
                title="Qdrant Cloud — Hybrid Vector Store"
                tags={["Qdrant Cloud", "Dense + Sparse"]}
                desc="Vectors are persisted in Qdrant Cloud. Retrieval runs a hybrid search: dense similarity scores combined with metadata filters (ticker symbol, fiscal year) to guarantee strict isolation between different stocks and time periods."
              >
                <CalloutBox color="#f093fb" label="Why Hybrid?">
                  Pure dense search risks retrieving contextually similar but temporally wrong chunks (e.g., 2022 risks for a 2024 query). The sparse filter layer acts as a hard guardrail on top of semantic similarity.
                </CalloutBox>
              </PipelineStep>

              <PipelineStep
                step={4} icon={IconCheck} color="#43e97b"
                title="Cross-Encoder Re-ranking"
                tags={["Re-ranking", "Precision"]}
                desc="The top-K retrieved chunks are passed to a cross-encoder model that jointly scores the query and each chunk together — unlike bi-encoders that score independently. This dramatically improves the signal-to-noise ratio of context fed to the LLM."
              >
                <CalloutBox color="#43e97b" label="Why Re-rank?">
                  Bi-encoder retrieval optimizes for recall. Re-ranking optimizes for precision. In financial RAG, hallucinations from low-quality context are far more dangerous than missing a chunk — so we prioritize precision.
                </CalloutBox>
              </PipelineStep>

              <PipelineStep
                step={5} icon={IconUsers} color="#f6d365"
                title="LangGraph Orchestration — GPT-OSS (120B params)"
                tags={["LangGraph", "GPT-OSS 112B", "Multi-Agent"]}
                desc="Re-ranked context is injected into a LangGraph workflow. Specialized nodes run in sequence: (a) Financial KPI analysis & peer comparison, (b) Deterministic DCF + WACC valuation, (c) Investment thesis generation with bull/bear cases."
              >
                <CalloutBox color="#f6d365" label="Why LangGraph?">
                  Declarative graph-based orchestration makes each agent step inspectable and testable independently. State is persisted across nodes, enabling the Reflection Loop to access all upstream outputs.
                </CalloutBox>
              </PipelineStep>

              <PipelineStep
                step={6} icon={IconBulb} color="#a78bfa"
                title="Reflection Loop — Senior Analyst Agent"
                tags={["Self-Critique", "Hallucination Guard"]}
                desc="A second LangGraph agent reviews the complete draft report. It checks for logical contradictions, unsupported valuations, and consistency between DCF outputs and textual conclusions. The report is revised before being returned."
              />

              <PipelineStep
                step={7} iconUrl="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/json/json-original.svg" color="#FF5722"
                title="Output Guardrails & Schema Validation"
                tags={["Guardrails", "JSON Schema"]}
                desc="Before leaving the backend, all agent outputs are validated against a strict Pydantic schema. Guardrails reject malformed financial data, out-of-range valuations, and prevent prompt injection from making it into the stored report."
              />

              <PipelineStep
                step={8} iconUrl="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/nextjs/nextjs-original.svg" color="#76ABAE"
                title="Logfire Observability + Frontend Render"
                tags={["Logfire", "Tracing"]}
                isLast
                desc="Every pipeline step is traced via Pydantic Logfire — LLM latency, retrieval scores, re-ranking deltas, and LangGraph state transitions. The validated report is returned as structured JSON and rendered in the Next.js dashboard with a memory-augmented chatbot for follow-up questions."
              />

            </div>
          </div>


          {/* ── Two columns: sections + pipeline ── */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem", marginBottom: "2rem" }}>

            {/* LEFT: Feature Sections */}
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>

              {/* RAG */}
              <div style={{ background: "var(--bg)", border: "1px solid rgba(118,171,174,0.15)", borderRadius: "var(--radius-lg)", padding: "1.75rem" }}>
                <SectionTitle num="1" title="Production RAG Pipeline" />
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  <FeatureCard
                    iconUrl="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg"
                    title="Ingestion & Semantic Chunking"
                    tag="YFinance + SEC"
                    color="#4facfe"
                    desc="Fetches structured financial data via YFinance API and unstructured SEC 10-K filings. Documents are chunked using semantic boundaries to preserve contextual integrity of risk disclosures."
                  />
                  <FeatureCard
                    iconUrl="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/google/google-original.svg"
                    title="Gemini Embeddings"
                    tag="Dense Vectors"
                    color="#a78bfa"
                    desc="Each chunk is encoded into high-dimensional dense vectors using Google Gemini embedding models, capturing deep financial semantics beyond keyword matching."
                  />
                  <FeatureCard
                    icon={IconShield}
                    title="Qdrant Cloud Vector DB"
                    tag="Hybrid Search"
                    color="#f093fb"
                    desc="Vectors stored in Qdrant Cloud DB. Retrieval combines dense similarity with sparse metadata filters (ticker, fiscal year) — preventing cross-stock contamination."
                  />
                  <FeatureCard
                    icon={IconCheck}
                    title="Cross-Encoder Re-ranking"
                    tag="Precision Boost"
                    color="#43e97b"
                    desc="Retrieved candidates pass through a cross-encoder re-ranker. This second-pass scoring penalizes context mismatches and surfaces the most relevant chunks, drastically cutting hallucinations."
                  />
                </div>
              </div>

              {/* LLM + Guardrails */}
              <div style={{ background: "var(--bg)", border: "1px solid rgba(118,171,174,0.15)", borderRadius: "var(--radius-lg)", padding: "1.75rem" }}>
                <SectionTitle num="2" title="LLM Engine & Guardrails" />
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  <FeatureCard
                    icon={IconCalc}
                    title="GPT-OSS (120B Parameters)"
                    tag="1.12B Params"
                    color="#43e97b"
                    desc="Uses an open-source 1.12B parameter model served via Groq for ultra-low latency inference. Right-sized for structured financial reasoning — DCF math, peer analysis, and thesis generation."
                  />
                  <FeatureCard
                    iconUrl="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/json/json-original.svg"
                    title="Input / Output Guardrails"
                    tag="Safety Layer"
                    color="#FF5722"
                    desc="Implemented guardrails that enforce strict JSON schema output, block prompt injection, and validate financial math consistency before the response is returned to the client."
                  />
                </div>
              </div>

            </div>

            {/* RIGHT: LangGraph + Chatbot + Observability */}
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>

              {/* LangGraph */}
              <div style={{ background: "var(--bg)", border: "1px solid rgba(118,171,174,0.15)", borderRadius: "var(--radius-lg)", padding: "1.75rem" }}>
                <SectionTitle num="3" title="LangGraph Multi-Agent Workflow" />
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  <FeatureCard
                    icon={IconUsers}
                    title="Financials & Peer Analysis Node"
                    tag="Agent Node"
                    color="#f6d365"
                    desc="Dedicated LangGraph node that pulls live KPIs (YoY revenue, operating margin), auto-discovers industry peers, and computes comparative performance differentials."
                  />
                  <FeatureCard
                    icon={IconCalc}
                    title="DCF Valuation Node"
                    tag="Deterministic"
                    color="#fa709a"
                    desc="Runs a fully deterministic DCF + WACC calculation — no LLM math guessing. Generates a sensitivity grid across WACC and terminal growth rate scenarios."
                  />
                  <FeatureCard
                    icon={IconBulb}
                    title="Senior Analyst Reflection Loop"
                    tag="Self-Critique"
                    color="#a78bfa"
                    desc="A second LangGraph agent critiques the draft report before finalization. It checks for internal contradictions, unsupported claims, and logical consistency — functioning as an automated QA gate."
                  />
                </div>
              </div>

              {/* Chatbot + Observability */}
              <div style={{ background: "var(--bg)", border: "1px solid rgba(118,171,174,0.15)", borderRadius: "var(--radius-lg)", padding: "1.75rem" }}>
                <SectionTitle num="4" title="Chatbot & Observability" />
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  <FeatureCard
                    iconUrl="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/javascript/javascript-original.svg"
                    title="Memory-Augmented Chatbot"
                    tag="Stateful"
                    color="#e8a838"
                    desc="Conversational agent with persistent session memory. Users can interrogate the generated report — asking follow-up questions about DCF assumptions, risks, or peer comparisons contextually."
                  />
                  <FeatureCard
                    iconUrl="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/nextjs/nextjs-original.svg"
                    title="Logfire Observability (Pydantic)"
                    tag="Full Tracing"
                    color="#76ABAE"
                    desc="Every LLM call, vector retrieval, re-ranking score, and LangGraph state transition is traced via Pydantic Logfire. Provides deep visibility into latency, token usage, and agent decision paths."
                  />
                </div>
              </div>

            </div>
          </div>


        </div>
      </main>
    </div>
  );
}
