"use client";

import React, { useState, useRef, useEffect } from "react";
import { IconMessageCircle, IconClose, IconSend, IconSpinner } from "./icons";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatbotProps {
  ticker?: string;
  reportContext?: any;
}

export default function Chatbot({ ticker, reportContext }: ChatbotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && endOfMessagesRef.current) {
      endOfMessagesRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen, isLoading]);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;
    
    const userMsg: Message = { role: "user", content: text };
    setMessages(prev => [...prev, userMsg]);
    setInputValue("");
    setIsLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          ticker: ticker,
          report_context: reportContext,
          history: messages,
        }),
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed to fetch response");
      
      setMessages(prev => [...prev, { role: "assistant", content: data.reply }]);
    } catch (err: any) {
      setMessages(prev => [...prev, { role: "assistant", content: `Error: ${err.message}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      sendMessage(inputValue);
    }
  };

  const suggestedQuestions = [
    "What are the key risks?",
    "Is this stock a buy?",
    "Summarize the peer comparison.",
    "Explain the DCF valuation."
  ];

  return (
    <>
      {/* Floating Action Button */}
      <button 
        className="chatbot-bubble" 
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: "fixed", bottom: "2rem", right: "2rem", zIndex: 50,
          width: "56px", height: "56px", borderRadius: "50%",
          background: "var(--cta)", color: "white",
          border: "none", cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 4px 12px rgba(255, 87, 34, 0.4)",
          transition: "transform 0.2s, background 0.2s"
        }}
        onMouseEnter={(e) => e.currentTarget.style.transform = "scale(1.05)"}
        onMouseLeave={(e) => e.currentTarget.style.transform = "scale(1)"}
      >
        {isOpen ? <IconClose size={24} /> : <IconMessageCircle size={24} />}
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div 
          className="chatbot-panel animate-slideInRight"
          style={{
            position: "fixed", bottom: "6.5rem", right: "2rem", zIndex: 49,
            width: "360px", height: "500px",
            background: "rgba(38, 46, 54, 0.85)", backdropFilter: "blur(12px)",
            border: "1px solid rgba(118,171,174,0.3)",
            borderRadius: "var(--radius-lg)",
            display: "flex", flexDirection: "column",
            boxShadow: "0 8px 32px rgba(0, 0, 0, 0.4)",
            overflow: "hidden"
          }}
        >
          {/* Header */}
          <div style={{
            background: "rgba(118,171,174,0.15)",
            padding: "1rem", borderBottom: "1px solid rgba(118,171,174,0.2)",
            display: "flex", alignItems: "center", justifyContent: "space-between"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <IconMessageCircle size={18} style={{ color: "var(--accent)" }} />
              <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--fg)" }}>QuantBot</span>
              {ticker && (
                <span style={{ 
                  background: "var(--accent)", color: "white", padding: "0.1rem 0.4rem", 
                  borderRadius: "99px", fontSize: "0.65rem", fontWeight: 700 
                }}>
                  {ticker} Context
                </span>
              )}
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              style={{ background: "none", border: "none", color: "var(--fg-muted)", cursor: "pointer" }}
            >
              <IconClose size={18} />
            </button>
          </div>

          {/* Messages */}
          <div style={{
            flex: 1, padding: "1rem", overflowY: "auto", display: "flex", flexDirection: "column", gap: "1rem"
          }}>
            {messages.length === 0 ? (
              <div style={{ 
                margin: "auto", textAlign: "center", color: "var(--fg-muted)", 
                display: "flex", flexDirection: "column", gap: "0.5rem" 
              }}>
                <IconMessageCircle size={32} style={{ margin: "0 auto", opacity: 0.3 }} />
                <p style={{ fontSize: "0.85rem", marginTop: "0.5rem" }}>Ask me anything about {ticker ? ticker : "investments"}.</p>
                
                <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", marginTop: "1rem" }}>
                  {suggestedQuestions.map((q, i) => (
                    <button 
                      key={i}
                      onClick={() => sendMessage(q)}
                      style={{
                        background: "rgba(118,171,174,0.1)", border: "1px solid rgba(118,171,174,0.2)",
                        color: "var(--accent)", borderRadius: "var(--radius-sm)",
                        padding: "0.5rem", fontSize: "0.75rem", cursor: "pointer",
                        transition: "background 0.2s"
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = "rgba(118,171,174,0.2)"}
                      onMouseLeave={(e) => e.currentTarget.style.background = "rgba(118,171,174,0.1)"}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, i) => (
                <div key={i} style={{ 
                  alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                  maxWidth: "85%",
                  background: msg.role === "user" ? "var(--cta)" : "rgba(118,171,174,0.15)",
                  color: msg.role === "user" ? "white" : "var(--fg)",
                  padding: "0.6rem 0.8rem",
                  borderRadius: "var(--radius-md)",
                  borderBottomRightRadius: msg.role === "user" ? 0 : "var(--radius-md)",
                  borderBottomLeftRadius: msg.role === "assistant" ? 0 : "var(--radius-md)",
                  fontSize: "0.85rem",
                  lineHeight: 1.5,
                  whiteSpace: "pre-wrap"
                }}>
                  {msg.content}
                </div>
              ))
            )}
            {isLoading && (
              <div style={{ alignSelf: "flex-start", display: "flex", alignItems: "center", gap: "0.4rem", padding: "0.5rem" }}>
                <div className="chat-typing-dot" style={{ animationDelay: "0ms" }}></div>
                <div className="chat-typing-dot" style={{ animationDelay: "150ms" }}></div>
                <div className="chat-typing-dot" style={{ animationDelay: "300ms" }}></div>
              </div>
            )}
            <div ref={endOfMessagesRef} />
          </div>

          {/* Input */}
          <div style={{
            padding: "0.75rem", background: "rgba(0,0,0,0.1)", borderTop: "1px solid rgba(118,171,174,0.15)",
            display: "flex", gap: "0.5rem"
          }}>
            <input 
              type="text" 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question..."
              style={{
                flex: 1, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(118,171,174,0.2)",
                borderRadius: "99px", padding: "0.5rem 1rem", color: "var(--fg)",
                fontSize: "0.85rem", outline: "none"
              }}
            />
            <button 
              onClick={() => sendMessage(inputValue)}
              disabled={isLoading || !inputValue.trim()}
              style={{
                background: inputValue.trim() ? "var(--accent)" : "rgba(118,171,174,0.2)", 
                border: "none", color: "white", width: "36px", height: "36px",
                borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                cursor: inputValue.trim() ? "pointer" : "default",
                transition: "background 0.2s"
              }}
            >
              <IconSend size={16} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
