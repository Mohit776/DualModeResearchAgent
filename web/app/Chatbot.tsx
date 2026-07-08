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
          width: "60px", height: "60px", borderRadius: "50%",
          background: "var(--cta)", color: "white",
          border: "none", cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 6px 16px rgba(255, 87, 34, 0.4)",
          transition: "transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), background 0.2s"
        }}
        onMouseEnter={(e) => e.currentTarget.style.transform = "scale(1.1) rotate(5deg)"}
        onMouseLeave={(e) => e.currentTarget.style.transform = "scale(1) rotate(0deg)"}
      >
        {isOpen ? <IconClose size={28} /> : <IconMessageCircle size={28} />}
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div 
          className="chatbot-panel animate-slideInRight"
          style={{
            position: "fixed", bottom: "7rem", right: "2rem", zIndex: 49,
            width: "550px", height: "650px", maxHeight: "80vh", maxWidth: "90vw",
            background: "rgba(30, 38, 46, 0.95)", backdropFilter: "blur(16px)",
            border: "1px solid rgba(118,171,174,0.4)",
            borderRadius: "var(--radius-lg)",
            display: "flex", flexDirection: "column",
            boxShadow: "0 12px 48px rgba(0, 0, 0, 0.5)",
            overflow: "hidden",
            transformOrigin: "bottom right",
            animation: "slideInRight 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)"
          }}
        >
          {/* Header */}
          <div style={{
            background: "linear-gradient(90deg, rgba(118,171,174,0.2) 0%, rgba(118,171,174,0.05) 100%)",
            padding: "1.25rem 1.5rem", borderBottom: "1px solid rgba(118,171,174,0.2)",
            display: "flex", alignItems: "center", justifyContent: "space-between"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <div style={{ background: "rgba(118,171,174,0.2)", padding: "0.5rem", borderRadius: "50%" }}>
                <IconMessageCircle size={20} style={{ color: "var(--accent)" }} />
              </div>
              <span style={{ fontWeight: 700, fontSize: "1.1rem", color: "var(--fg)", letterSpacing: "0.5px" }}>QuantBot</span>
              {ticker && (
                <span style={{ 
                  background: "var(--accent)", color: "white", padding: "0.2rem 0.6rem", 
                  borderRadius: "99px", fontSize: "0.7rem", fontWeight: 700,
                  boxShadow: "0 2px 8px rgba(118,171,174,0.4)"
                }}>
                  {ticker} Context
                </span>
              )}
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              style={{ 
                background: "rgba(255,255,255,0.05)", border: "none", color: "var(--fg-muted)", 
                cursor: "pointer", width: "32px", height: "32px", borderRadius: "50%",
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "all 0.2s"
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.1)"; e.currentTarget.style.color = "white"; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.05)"; e.currentTarget.style.color = "var(--fg-muted)"; }}
            >
              <IconClose size={18} />
            </button>
          </div>

          {/* Messages */}
          <div style={{
            flex: 1, padding: "1.5rem", overflowY: "auto", display: "flex", flexDirection: "column", gap: "1.25rem",
            scrollBehavior: "smooth"
          }}>
            {messages.length === 0 ? (
              <div style={{ 
                margin: "auto", textAlign: "center", color: "var(--fg-muted)", 
                display: "flex", flexDirection: "column", gap: "1rem",
                animation: "fadeIn 0.5s ease-in"
              }}>
                <div style={{ 
                  background: "rgba(118,171,174,0.05)", width: "80px", height: "80px", 
                  borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                  margin: "0 auto", border: "1px solid rgba(118,171,174,0.1)"
                }}>
                  <IconMessageCircle size={40} style={{ color: "var(--accent)", opacity: 0.8 }} />
                </div>
                <div>
                  <h3 style={{ color: "var(--fg)", fontSize: "1.1rem", marginBottom: "0.25rem", fontWeight: 600 }}>Welcome to QuantBot</h3>
                  <p style={{ fontSize: "0.9rem", maxWidth: "80%", margin: "0 auto", lineHeight: 1.5 }}>
                    Ask me anything about {ticker ? ticker : "investments"}.
                  </p>
                </div>
                
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginTop: "1rem" }}>
                  {suggestedQuestions.map((q, i) => (
                    <button 
                      key={i}
                      onClick={() => sendMessage(q)}
                      style={{
                        background: "rgba(118,171,174,0.05)", border: "1px solid rgba(118,171,174,0.3)",
                        color: "var(--accent)", borderRadius: "var(--radius-md)",
                        padding: "0.75rem 1rem", fontSize: "0.85rem", cursor: "pointer",
                        transition: "all 0.2s", textAlign: "left", fontWeight: 500,
                        display: "flex", justifyContent: "space-between", alignItems: "center"
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = "rgba(118,171,174,0.15)";
                        e.currentTarget.style.transform = "translateX(4px)";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = "rgba(118,171,174,0.05)";
                        e.currentTarget.style.transform = "translateX(0)";
                      }}
                    >
                      {q}
                      <span style={{ opacity: 0.5 }}>→</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, i) => {
                const renderMessageContent = (content: string) => {
                  const parts = content.split(/(\*\*.*?\*\*)/g);
                  return parts.map((part, index) => {
                    if (part.startsWith('**') && part.endsWith('**')) {
                      return <strong key={index}>{part.slice(2, -2)}</strong>;
                    }
                    return <span key={index}>{part}</span>;
                  });
                };

                return (
                  <div key={i} style={{ 
                    alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                    maxWidth: "85%",
                    background: msg.role === "user" ? "var(--cta)" : "rgba(118,171,174,0.1)",
                    color: msg.role === "user" ? "white" : "var(--fg)",
                    padding: "1rem 1.25rem",
                    borderRadius: "1rem",
                    borderBottomRightRadius: msg.role === "user" ? "0.25rem" : "1rem",
                    borderBottomLeftRadius: msg.role === "assistant" ? "0.25rem" : "1rem",
                    border: msg.role === "assistant" ? "1px solid rgba(118,171,174,0.2)" : "none",
                    fontSize: "0.95rem",
                    lineHeight: 1.6,
                    whiteSpace: "pre-wrap",
                    boxShadow: msg.role === "user" ? "0 4px 12px rgba(255, 87, 34, 0.2)" : "none",
                    animation: "fadeInUp 0.3s ease-out"
                  }}>
                    {renderMessageContent(msg.content)}
                  </div>
                );
              })
            )}
            {isLoading && (
              <div style={{ 
                alignSelf: "flex-start", display: "flex", alignItems: "center", gap: "0.5rem", 
                padding: "1rem 1.25rem", background: "rgba(118,171,174,0.05)", 
                borderRadius: "1rem", borderBottomLeftRadius: "0.25rem",
                border: "1px solid rgba(118,171,174,0.1)"
              }}>
                <div className="chat-typing-dot" style={{ animationDelay: "0ms" }}></div>
                <div className="chat-typing-dot" style={{ animationDelay: "150ms" }}></div>
                <div className="chat-typing-dot" style={{ animationDelay: "300ms" }}></div>
              </div>
            )}
            <div ref={endOfMessagesRef} />
          </div>

          {/* Input */}
          <div style={{
            padding: "1.25rem", background: "rgba(0,0,0,0.2)", borderTop: "1px solid rgba(118,171,174,0.15)"
          }}>
            <div style={{
              display: "flex", gap: "0.75rem", background: "rgba(255,255,255,0.03)", 
              border: "1px solid rgba(118,171,174,0.3)", borderRadius: "99px", 
              padding: "0.5rem", alignItems: "center",
              transition: "border-color 0.2s, background 0.2s"
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "var(--accent)";
              e.currentTarget.style.background = "rgba(255,255,255,0.06)";
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = "rgba(118,171,174,0.3)";
              e.currentTarget.style.background = "rgba(255,255,255,0.03)";
            }}
            >
              <input 
                type="text" 
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question..."
                style={{
                  flex: 1, background: "transparent", border: "none",
                  padding: "0.5rem 1rem", color: "var(--fg)",
                  fontSize: "0.95rem", outline: "none", width: "100%"
                }}
              />
              <button 
                onClick={() => sendMessage(inputValue)}
                disabled={isLoading || !inputValue.trim()}
                style={{
                  background: inputValue.trim() ? "var(--accent)" : "rgba(118,171,174,0.2)", 
                  border: "none", color: "white", width: "42px", height: "42px",
                  borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                  cursor: inputValue.trim() ? "pointer" : "default",
                  transition: "all 0.2s",
                  boxShadow: inputValue.trim() ? "0 2px 8px rgba(118,171,174,0.4)" : "none"
                }}
                onMouseEnter={(e) => {
                  if (inputValue.trim()) e.currentTarget.style.transform = "scale(1.05)";
                }}
                onMouseLeave={(e) => {
                  if (inputValue.trim()) e.currentTarget.style.transform = "scale(1)";
                }}
              >
                <IconSend size={18} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
