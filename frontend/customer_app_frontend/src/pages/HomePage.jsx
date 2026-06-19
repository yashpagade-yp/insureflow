import { Link } from "react-router-dom";

const trustPoints = [
  "Simple plan comparison with clear coverage and premium details",
  "Guided customer journey from application to issued policy",
  "Easy return access through mobile OTP login",
];

const journeySteps = [
  {
    title: "Start your application",
    description:
      "Share your contact details, city, and coverage preference through a simple guided form.",
  },
  {
    title: "Compare matched plans",
    description:
      "Review suitable plans, compare benefits and premiums, and choose what fits you best.",
  },
  {
    title: "Complete payment",
    description:
      "Verify the payment step and move forward without a confusing or crowded checkout flow.",
  },
  {
    title: "Access your policy later",
    description:
      "Log in again with mobile OTP to track your journey, view policies, and raise support tickets.",
  },
];

const botFeatures = [
  {
    eyebrow: "AI chat bot",
    title: "Ask questions in a simple text conversation",
    description:
      "Use the chatbot to understand plans, journey steps, policy flow, and common insurance questions.",
    actionLabel: "Open AI chat",
    actionTo: "/chat",
  },
  {
    eyebrow: "Voice bot",
    title: "Talk to an assistant in a voice-first experience",
    description:
      "Use the voice bot for spoken guidance and a clearer, more natural support experience.",
    actionLabel: "Open voice assistant",
    actionTo: "/voice",
  },
  {
    eyebrow: "Calling bot",
    title: "Get support through guided insurance calling assistance",
    description:
      "The calling bot helps with customer follow-up, guided insurance conversations, and assisted policy progress.",
    actionLabel: "Admin login for calling bot",
    actionTo: "/admin/login",
  },
];

const insuranceHighlights = [
  "Health insurance plans matched to your requested coverage",
  "Optional add-ons for stronger protection",
  "Policy access and support after purchase",
];

function HomePage() {
  return (
    <div className="home-layout landing-layout">
      <section className="landing-topbar">
        <div className="landing-topbar-brand">
          <span className="brand-monogram">IF</span>
          <div>
            <p className="eyebrow-text">InsureFlow</p>
            <h2>Customer Insurance Platform</h2>
          </div>
        </div>

        <div className="landing-topbar-actions">
          <Link to="/customer/login" className="ghost-button">
            Customer login
          </Link>
          <Link to="/admin/login" className="secondary-button">
            Admin login
          </Link>
          <Link to="/journey/new" className="primary-button">
            Start application
          </Link>
        </div>
      </section>

      <section className="hero-panel landing-hero landing-slide">
        <div className="landing-hero-copy">
          <p className="eyebrow-text">Slide 1 · Customer welcome</p>
          <h1>Buy insurance with a journey that feels calm, clear, and easy to follow.</h1>
          <p className="hero-copy">
            Explore health insurance, compare suitable plans, complete payment,
            and return later to manage your policy from one simple web experience.
          </p>

          <div className="hero-actions">
            <Link to="/journey/new" className="primary-button">
              Start new application
            </Link>
            <Link to="/customer/login" className="secondary-button">
              Resume with OTP
            </Link>
          </div>

          <div className="hero-trust-strip">
            {trustPoints.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </div>

        <div className="landing-hero-panel">
          <article className="landing-quote-card">
            <p className="eyebrow-text">Insurance made friendly</p>
            <h2>Protection decisions should feel understandable, not stressful.</h2>
            <p className="muted-copy">
              This platform is designed for customers first, with a clean path
              from insurance details to policy access.
            </p>
          </article>

          <div className="landing-mini-grid">
            <div className="hero-mini-card">
              <p className="eyebrow-text">Customer flow</p>
              <h3>Apply, compare, pay, and manage</h3>
              <p>Everything important stays easy to reach.</p>
            </div>
            <div className="hero-mini-card">
              <p className="eyebrow-text">Admin access</p>
              <h3>Operations are available in the same webapp</h3>
              <p>Admins can log in separately when needed.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="section-card landing-slide">
        <div className="section-head">
          <div>
            <p className="eyebrow-text">Slide 2 · Why choose InsureFlow</p>
            <h3>What the customer gets from this insurance experience</h3>
            <p>
              We keep the experience practical and easy to understand so the
              customer can focus on choosing the right protection.
            </p>
          </div>
        </div>

        <div className="customer-steps-grid">
          {insuranceHighlights.map((item, index) => (
            <article key={item} className="step-card">
              <span className="step-card-index">0{index + 1}</span>
              <h4>{item}</h4>
              <p>
                Clear information, simpler choices, and a structured path through the
                full insurance journey.
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-card landing-slide landing-process-card">
        <div className="section-head">
          <div>
            <p className="eyebrow-text">Slide 3 · How it works</p>
            <h3>The customer insurance journey in four simple steps</h3>
            <p>
              The process is intentionally guided so the customer always knows
              what comes next.
            </p>
          </div>
        </div>

        <div className="customer-steps-grid customer-steps-grid-wide">
          {journeySteps.map((step, index) => (
            <article key={step.title} className="step-card">
              <span className="step-card-index">0{index + 1}</span>
              <h4>{step.title}</h4>
              <p>{step.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-card landing-slide">
        <div className="section-head">
          <div>
            <p className="eyebrow-text">Slide 4 · Smart assistance</p>
            <h3>Get help through chat, voice, and calling support</h3>
            <p>
              Each support feature is available for a different kind of customer
              interaction, while still feeling part of the same product.
            </p>
          </div>
        </div>

        <div className="bot-feature-grid">
          {botFeatures.map((feature) => (
            <article key={feature.title} className="bot-feature-card">
              <p className="eyebrow-text">{feature.eyebrow}</p>
              <h4>{feature.title}</h4>
              <p>{feature.description}</p>
              <Link to={feature.actionTo} className="secondary-button">
                {feature.actionLabel}
              </Link>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-entry-grid landing-slide">
        <article className="choice-card landing-role-card">
          <p className="eyebrow-text">Slide 5 · Customer entry</p>
          <h2>Start or continue your insurance journey</h2>
          <p>
            Use the customer side to apply for health insurance, compare plans,
            complete payment, and access your policies later.
          </p>

          <div className="landing-list">
            <div className="landing-list-item">Start a new health insurance application</div>
            <div className="landing-list-item">Resume your journey through mobile OTP login</div>
            <div className="landing-list-item">Access issued policies and support tickets</div>
          </div>

          <div className="landing-action-stack">
            <Link to="/journey/new" className="primary-button">
              Start application
            </Link>
            <Link to="/customer/login" className="secondary-button">
              Customer login
            </Link>
          </div>
        </article>

        <article className="choice-card landing-role-card landing-role-card-admin">
          <p className="eyebrow-text">Admin entry</p>
          <h2>Customer-app admin access</h2>
          <p>
            Admins use the same webapp with a separate login to monitor customer
            journeys and assisted calling workflows.
          </p>

          <div className="landing-list">
            <div className="landing-list-item">Monitor customer journeys and policy progress</div>
            <div className="landing-list-item">Track outbound call activity and follow-up status</div>
            <div className="landing-list-item">Access calling-bot and customer assistance tools</div>
          </div>

          <div className="landing-action-stack">
            <Link to="/admin/login" className="primary-button">
              Admin login
            </Link>
          </div>
        </article>
      </section>
    </div>
  );
}

export default HomePage;
