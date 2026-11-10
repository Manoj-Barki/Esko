import React, { useState, useEffect, useRef } from "react";
import { api } from "../api.js";

export default function AssistantView() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Load RAG stats on mount
    api.ragStats()
      .then(setStats)
      .catch(err => console.error("Failed to load RAG stats:", err));
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage() {
    if (!input.trim() || loading) return;

    const userMessage = { role: "user", content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await api.ragChat(input);

      const assistantMessage = {
        role: "assistant",
        content: response.answer || "I couldn't generate a response.",
        sources: response.sources || [],
        error: response.error
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = {
        role: "assistant",
        content: `Error: ${err.message}`,
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="assistant">
      <h1>AI Assistant for Packaging Standards</h1>
      <p className="lede">
        Ask questions about packaging preflight rules, image resolution standards, dieline geometry,
        and common defects. The assistant uses a knowledge base of industry standards to provide accurate answers.
      </p>

      {stats && (
        <div className="banner info">
          <strong>Knowledge Base Status:</strong> {stats.status}
          {stats.total_documents > 0 && ` • ${stats.total_documents} documents indexed`}
          {stats.openai_configured !== undefined && (
            <span> • AI Q&A: {stats.openai_configured ? "✓ Enabled" : "⚠ Disabled (set OPENAI_API_KEY)"}</span>
          )}
        </div>
      )}

      <div className="chat-container">
        <div className="messages">
          {messages.length === 0 && (
            <div className="empty">
              <strong>Start a conversation</strong>
              <span>Try asking:</span>
              <ul className="suggestions">
                <li>"What is the minimum DPI for packaging artwork?"</li>
                <li>"How much clearance should text have from cut lines?"</li>
                <li>"What causes low resolution image warnings?"</li>
                <li>"Explain the safe area margin requirements"</li>
              </ul>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              <div className="message-role">
                {msg.role === "user" ? "You" : "AI Assistant"}
              </div>
              <div className="message-content">
                {msg.content}
                {msg.error && msg.error !== "missing_api_key" && (
                  <div className="message-error">⚠ {msg.error}</div>
                )}
              </div>
              {msg.sources && msg.sources.length > 0 && (
                <details className="message-sources">
                  <summary>Sources ({msg.sources.length})</summary>
                  <ul>
                    {msg.sources.map((src, si) => (
                      <li key={si}>
                        <strong>{src.metadata?.source || "Unknown"}</strong>
                        {src.metadata?.category && <em> • {src.metadata.category}</em>}
                        <p>{src.content}</p>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          ))}

          {loading && (
            <div className="message assistant loading">
              <div className="message-role">AI Assistant</div>
              <div className="message-content">
                <span className="typing-indicator">●●●</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-container">
          <textarea
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about packaging standards..."
            rows={2}
            disabled={loading}
          />
          <button
            className="primary"
            onClick={sendMessage}
            disabled={!input.trim() || loading}
          >
            {loading ? "Thinking..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}
