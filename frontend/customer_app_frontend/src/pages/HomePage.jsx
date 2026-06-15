import { Link } from "react-router-dom";

function HomePage() {
  return (
    <div className="home-layout">
      <section className="hero-panel">
        <p className="eyebrow-text">InsureFlow customer experience</p>
        <h1>Health insurance made understandable, trackable, and ready to buy.</h1>
        <p className="hero-copy">
          Customers can start their journey directly, get quotes, complete payment,
          and access issued policies. Or talk to our AI assistant instantly.
        </p>

        <div className="hero-actions">
          <Link to="/chat" className="primary-button">
            Chat with AI
          </Link>
          <Link to="/voice" className="secondary-button">
            Voice assistant
          </Link>
          <Link to="/journey/new" className="secondary-button">
            Start manually
          </Link>
        </div>
      </section>

      <section className="choice-grid">
        <article className="choice-card">
          <p className="eyebrow-text">AI Chatbot</p>
          <h2>Ask anything, get it done</h2>
          <p>
            Chat with InsureFlow AI — it will guide you through buying insurance,
            compare plans, and complete your policy purchase end to end.
          </p>
          <Link to="/chat" className="text-link">
            Open chatbot →
          </Link>
        </article>

        <article className="choice-card choice-card-voice">
          <p className="eyebrow-text" style={{ color: "var(--success)" }}>AI Voice Bot</p>
          <h2>Speak naturally</h2>
          <p>
            Use your microphone to talk with InsureFlow AI. Ask about plans,
            pricing, and complete your purchase hands-free.
          </p>
          <Link to="/voice" className="text-link">
            Open voice bot →
          </Link>
        </article>

        <article className="choice-card">
          <p className="eyebrow-text">Manual form</p>
          <h2>Apply, compare, pay</h2>
          <p>
            Fill the insurance form yourself, fetch plans, select add-ons,
            verify payment OTP, and view policies.
          </p>
          <Link to="/journey/new" className="text-link">
            Start form →
          </Link>
        </article>
      </section>
    </div>
  );
}

export default HomePage;
