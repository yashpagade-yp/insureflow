import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

const BOT_BASE_URL = import.meta.env.VITE_BOT_BASE_URL ?? "http://localhost:8002";
const BOT_URL = `${BOT_BASE_URL}/api/chat`;

const quickPrompts = [
  "Show me health insurance plans for a family.",
  "How do I resume my policy journey?",
  "What happens after payment OTP verification?",
];

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

  const messageCount = useMemo(
    () => messages.filter((item) => item.role !== "system").length,
    [messages]
  );

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(event, overrideText = "") {
    if (event) {
      event.preventDefault();
    }

    const text = (overrideText || input).trim();
    if (!text || loading) {
      return;
    }

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

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

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
      <section className="chat-workspace">
        <header className="chat-header">
          <div className="chat-header-brand">
            <div className="chat-avatar">IF</div>
            <div>
              <p className="chat-bot-name">InsureFlow AI Assistant</p>
              <p className="chat-status">
                <span className="chat-dot" />
                {loading ? "Preparing your answer..." : "Online and ready to help"}
              </p>
            </div>
          </div>
          <div className="chat-header-actions">
            <button className="chat-icon-btn" onClick={resetSession} title="Start new conversation">
              Reset
            </button>
            <Link to="/" className="chat-icon-btn" title="Go home">
              Home
            </Link>
          </div>
        </header>

        <div className="chat-layout-grid">
          <aside className="chat-side-panel">
            <div className="mini-card">
              <p className="eyebrow-text">Chat help</p>
              <h4>Ask about plans, policies, or journey steps</h4>
              <p>
                The chatbot is best for quick guidance, understanding the customer flow,
                and answering policy-related questions in plain language.
              </p>
            </div>

            <div className="mini-card">
              <p className="eyebrow-text">Session snapshot</p>
              <p>
                <strong>Messages:</strong> {messageCount}
              </p>
              <p>
                <strong>Session:</strong> {sessionId ? "Active" : "New"}
              </p>
            </div>

            <div className="mini-card">
              <p className="eyebrow-text">Suggested prompts</p>
              <div className="stacked-fields">
                {quickPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    className="ghost-button quick-prompt-button"
                    onClick={() => void sendMessage(null, prompt)}
                    disabled={loading}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </aside>

          <section className="chat-main-panel">
            <div className="chat-messages">
              {messages.map((msg, index) => (
                <div
                  key={`${msg.role}-${index}`}
                  className={`chat-bubble-wrap ${
                    msg.role === "user" ? "chat-bubble-user" : "chat-bubble-bot"
                  }`}
                >
                  {msg.role === "bot" ? <div className="chat-avatar chat-avatar-sm">IF</div> : null}
                  <div
                    className={`chat-bubble ${
                      msg.role === "user"
                        ? "chat-bubble-user-inner"
                        : "chat-bubble-bot-inner"
                    }`}
                  >
                    {msg.text}
                  </div>
                </div>
              ))}

              {loading ? (
                <div className="chat-bubble-wrap chat-bubble-bot">
                  <div className="chat-avatar chat-avatar-sm">IF</div>
                  <div className="chat-bubble chat-bubble-bot-inner chat-typing">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              ) : null}

              {error ? (
                <div className="alert-box alert-error chat-inline-alert">{error}</div>
              ) : null}

              <div ref={bottomRef} />
            </div>

            <form className="chat-input-bar" onSubmit={sendMessage}>
              <input
                ref={inputRef}
                id="chat-input"
                className="chat-input-field"
                type="text"
                placeholder="Ask anything about policies, plans, payments, or the customer journey"
                value={input}
                onChange={(event) => setInput(event.target.value)}
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
                Send
              </button>
            </form>
          </section>
        </div>
      </section>
    </div>
  );
}

export default ChatBotPage;
