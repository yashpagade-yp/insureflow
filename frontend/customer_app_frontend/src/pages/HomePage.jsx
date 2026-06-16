import { Link } from "react-router-dom";

const customerHighlights = [
  "Start your health insurance form without creating an account first.",
  "Compare plans, add riders, and complete payment only after you choose a policy.",
  "Use mock OTP later to resume, track, and download your issued policy.",
];

const adminHighlights = [
  "Login with email, password, and OTP for customer-side operations.",
  "Monitor customers, incomplete journeys, issued policies, and support tickets.",
  "Investigate failed outcomes and close customer issues from the admin workspace.",
];

function HomePage() {
  return (
    <div className="home-layout landing-layout">
      <section className="hero-panel landing-hero">
        <div className="landing-hero-copy">
          <p className="eyebrow-text">InsureFlow customer platform</p>
          <h1>Choose how you want to enter the customer insurance platform.</h1>
          <p className="hero-copy">
            This space supports both sides of the customer app: customers who want
            to buy and manage policies, and admins who monitor journeys, policies,
            and support operations.
          </p>

          <div className="hero-actions">
            <Link to="/journey/new" className="primary-button">
              Start customer journey
            </Link>
            <Link to="/admin/login" className="secondary-button">
              Open admin login
            </Link>
          </div>
        </div>

        <div className="landing-hero-panel">
          <div className="landing-quote-card">
            <p className="eyebrow-text">Health cover note</p>
            <h2>Good health deserves calm, clear financial protection.</h2>
            <p className="muted-copy">
              Start simple, compare the right cover, and keep every important
              policy touchpoint easy to reach.
            </p>
          </div>
          <div className="landing-mini-grid">
            <div className="hero-mini-card">
              <p className="eyebrow-text">Customer entry</p>
              <h3>Buy, resume, and track policies</h3>
            </div>
            <div className="hero-mini-card">
              <p className="eyebrow-text">Admin entry</p>
              <h3>Review journeys, policies, and support tickets</h3>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-role-grid">
        <article className="choice-card landing-role-card">
          <p className="eyebrow-text">Customer side</p>
          <h2>For customers buying health insurance</h2>
          <p>
            This path is for applicants who want to fill the form, get quotes,
            choose a plan, complete payment, and later access their policy.
          </p>

          <div className="landing-list">
            {customerHighlights.map((item) => (
              <div key={item} className="landing-list-item">
                {item}
              </div>
            ))}
          </div>

          <div className="landing-action-stack">
            <Link to="/journey/new" className="primary-button">
              Start new application
            </Link>
            <Link to="/customer/login" className="secondary-button">
              Customer login
            </Link>
            <div className="landing-inline-links">
              <Link to="/chat" className="text-link">
                AI chat
              </Link>
              <Link to="/voice" className="text-link">
                Voice assistant
              </Link>
            </div>
          </div>
        </article>

        <article className="choice-card landing-role-card landing-role-card-admin">
          <p className="eyebrow-text">Customer-app admin side</p>
          <h2>For admin operations inside the customer platform</h2>
          <p>
            This path is for admins who oversee customer records, incomplete
            journeys, issued policies, and post-purchase support issues.
          </p>

          <div className="landing-list">
            {adminHighlights.map((item) => (
              <div key={item} className="landing-list-item">
                {item}
              </div>
            ))}
          </div>

          <div className="landing-action-stack">
            <Link to="/admin/login" className="primary-button">
              Admin login
            </Link>
            <Link to="/admin/app/dashboard" className="secondary-button">
              Open admin dashboard
            </Link>
          </div>
        </article>
      </section>
    </div>
  );
}

export default HomePage;
