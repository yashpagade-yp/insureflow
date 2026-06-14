import { Link } from "react-router-dom";

function HomePage() {
  return (
    <div className="home-layout">
      <section className="hero-panel">
        <p className="eyebrow-text">InsureFlow customer experience</p>
        <h1>Health insurance made understandable, trackable, and ready to buy.</h1>
        <p className="hero-copy">
          Customers can start their journey directly, get quotes, complete payment,
          and access issued policies. Admins can monitor and issue policies from the same app.
        </p>

        <div className="hero-actions">
          <Link to="/journey/new" className="primary-button">
            Start customer journey
          </Link>
          <Link to="/customer/login" className="secondary-button">
            Resume with OTP
          </Link>
        </div>
      </section>

      <section className="choice-grid">
        <article className="choice-card">
          <p className="eyebrow-text">Customer</p>
          <h2>Apply, compare, pay</h2>
          <p>
            Fill the insurance form, fetch plans, select add-ons, verify payment OTP, and view policies.
          </p>
          <Link to="/journey/new" className="text-link">
            Enter customer flow
          </Link>
        </article>

        <article className="choice-card choice-card-admin">
          <p className="eyebrow-text">Admin</p>
          <h2>Handle operations</h2>
          <p>
            Login using email, password, and OTP to inspect users, transactions, and policy issuance work.
          </p>
          <Link to="/admin/login" className="text-link">
            Enter admin flow
          </Link>
        </article>
      </section>
    </div>
  );
}

export default HomePage;
