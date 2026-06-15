import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";

const BOT_URL = "http://localhost:8002/api/chat";

function ChatBotPage() {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Hi! I'm InsureFlow, your AI insurance assistant. How can I help you today? Are you looking to buy a new policy or check an existing one?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", text }]);
    setLoading(true);

    try {
      const res = await fetch(BOT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text }),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);

      const data = await res.json();
      setSessionId(data.session_id);
      setMessages((prev) => [...prev, { role: "bot", text: data.reply }]);
    } catch (err) {
      setError("Could not reach the bot server. Make sure it is running on port 8002.");
      console.error(err);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function resetSession() {
    setSessionId(null);
    setMessages([
      {
        role: "bot",
        text: "Hi! I'm InsureFlow, your AI insurance assistant. How can I help you today? Are you looking to buy a new policy or check an existing one?",
      },
    ]);
    setError(null);
    setInput("");
  }

  return (
    <div className="chat-page">
      {/* Header */}
      <header className="chat-header">
        <div className="chat-header-brand">
          <div className="chat-avatar">IF</div>
          <div>
            <p className="chat-bot-name">InsureFlow AI</p>
            <p className="chat-status">
              <span className="chat-dot" />
              {loading ? "Thinking…" : "Online"}
            </p>
          </div>
        </div>
        <div className="chat-header-actions">
          <button className="chat-icon-btn" onClick={resetSession} title="Start new conversation">
            ↺
          </button>
          <Link to="/" className="chat-icon-btn" title="Go home">
            ✕
          </Link>
        </div>
      </header>

      {/* Message list */}
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble-wrap ${msg.role === "user" ? "chat-bubble-user" : "chat-bubble-bot"}`}>
            {msg.role === "bot" && <div className="chat-avatar chat-avatar-sm">IF</div>}
            <div className={`chat-bubble ${msg.role === "user" ? "chat-bubble-user-inner" : "chat-bubble-bot-inner"}`}>
              {msg.text}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="chat-bubble-wrap chat-bubble-bot">
            <div className="chat-avatar chat-avatar-sm">IF</div>
            <div className="chat-bubble chat-bubble-bot-inner chat-typing">
              <span /><span /><span />
            </div>
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div className="alert-box alert-error" style={{ margin: "0 1rem" }}>
            ⚠ {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <form className="chat-input-bar" onSubmit={sendMessage}>
        <input
          ref={inputRef}
          id="chat-input"
          className="chat-input-field"
          type="text"
          placeholder="Type your message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          autoComplete="off"
          autoFocus
        />
        <button
          id="chat-send-btn"
          className="chat-send-btn"
          type="submit"
          disabled={!input.trim() || loading}
        >
          ↑
        </button>
      </form>
    </div>
  );
}

export default ChatBotPage;
