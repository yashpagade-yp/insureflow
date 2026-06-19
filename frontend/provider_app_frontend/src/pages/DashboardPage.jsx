import { useEffect, useMemo, useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import StatCard from "../components/StatCard";
import {
  listBuyerCompanies,
  listPayments,
  listPlans,
  listProviderCompanies,
  listQuotes,
} from "../lib/api";

function DashboardPage() {
  const [companies, setCompanies] = useState([]);
  const [plans, setPlans] = useState([]);
  const [quotes, setQuotes] = useState([]);
  const [payments, setPayments] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const [
          buyerResponse,
          providerResponse,
          planResponse,
          quoteResponse,
          paymentResponse,
        ] = await Promise.all([
          listBuyerCompanies(),
          listProviderCompanies(),
          listPlans(),
          listQuotes(),
          listPayments(),
        ]);

        setCompanies([
          ...(buyerResponse.items ?? []),
          ...(providerResponse.items ?? []),
        ]);
        setPlans(planResponse.items ?? []);
        setQuotes(quoteResponse.items ?? []);
        setPayments(paymentResponse.items ?? []);
      } catch (error) {
        setErrorMessage(error.message);
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  const providerCompanies = companies.filter(
    (item) => item.company_type === "provider"
  );
  const buyerCompanies = companies.filter((item) => item.company_type === "buyer");
  const activeCompanies = companies.filter((item) => item.is_active);
  const selectedQuotes = quotes.filter((item) => item.selected_plan_id);
  const successfulPayments = payments.filter(
    (item) => String(item.payment_status || "").toLowerCase() === "verified"
  );

  const dashboardStats = useMemo(
    () => [
      {
        label: "Network companies",
        value: companies.length,
        helper: `${activeCompanies.length} active companies currently connected`,
      },
      {
        label: "Provider carriers",
        value: providerCompanies.length,
        helper: "Insurance carriers available for publishing plans",
      },
      {
        label: "Buyer partners",
        value: buyerCompanies.length,
        helper: "Mediator or buyer systems integrated with provider APIs",
      },
      {
        label: "Published plans",
        value: plans.length,
        helper: "Plan inventory available to quote generation",
      },
      {
        label: "Live journeys",
        value: quotes.length + payments.length,
        helper: `${selectedQuotes.length} selected quotes and ${successfulPayments.length} verified payments`,
      },
    ],
    [
      activeCompanies.length,
      buyerCompanies.length,
      companies.length,
      payments.length,
      plans.length,
      providerCompanies.length,
      quotes.length,
      selectedQuotes.length,
      successfulPayments.length,
    ]
  );

  return (
    <div className="page-stack">
      <section className="command-hero">
        <div className="command-hero-copy">
          <p className="eyebrow-text">Provider command center</p>
          <h2>Operate the insurer side with confidence, speed, and clean control.</h2>
          <p>
            This workspace is for internal provider teams. It keeps company onboarding,
            plan publishing, quote activity, and payment-side visibility in one sharper,
            data-first console that stays visually separate from the customer experience.
          </p>
          <div className="hero-chip-row">
            <span className="hero-chip">Carrier network</span>
            <span className="hero-chip">Plan publishing</span>
            <span className="hero-chip">Quote intelligence</span>
            <span className="hero-chip">Payment visibility</span>
          </div>
        </div>

        <div className="command-hero-side">
          <div className="metric-strip">
            <div className="metric-cell">
              <span>Active network</span>
              <strong>{activeCompanies.length}</strong>
            </div>
            <div className="metric-cell">
              <span>Plans live</span>
              <strong>{plans.length}</strong>
            </div>
            <div className="metric-cell">
              <span>Quotes tracked</span>
              <strong>{quotes.length}</strong>
            </div>
            <div className="metric-cell">
              <span>Payments tracked</span>
              <strong>{payments.length}</strong>
            </div>
          </div>

          <div className="activity-card section-card">
            <div className="section-card-header">
              <div>
                <h3>Operational focus</h3>
                <p>Keep the provider backend healthy and ready for high-trust customer journeys.</p>
              </div>
            </div>
            <div className="company-board">
              <div className="company-board-cell">
                <span>Onboarding</span>
                <strong>Buyer + provider setup</strong>
              </div>
              <div className="company-board-cell">
                <span>Products</span>
                <strong>Coverage, benefits, riders</strong>
              </div>
              <div className="company-board-cell">
                <span>Operations</span>
                <strong>Quotes and payments</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="stats-grid">
        {dashboardStats.map((item) => (
          <StatCard
            key={item.label}
            label={item.label}
            value={item.value}
            helper={item.helper}
          />
        ))}
      </section>

      {errorMessage ? <div className="alert-box alert-error">{errorMessage}</div> : null}

      <SectionCard
        title="Why this provider workspace exists"
        subtitle="A provider-facing console should feel operational, reliable, and clearly distinct from the customer app."
      >
        <div className="spotlight-grid">
          <article className="spotlight-card">
            <h4>Internal-first by design</h4>
            <p>Dense operational information belongs here, not in the customer-facing journey.</p>
          </article>
          <article className="spotlight-card">
            <h4>Fast decisions</h4>
            <p>Provider admins need pricing, plan, and activity signals close together to act quickly.</p>
          </article>
          <article className="spotlight-card">
            <h4>Cleaner coordination</h4>
            <p>When network, product, and operations views are aligned, downstream quote and payment flows become easier to trust.</p>
          </article>
        </div>
      </SectionCard>

      <div className="content-grid">
        <SectionCard
          title="Recent network activity"
          subtitle="Latest buyer and provider companies visible from the provider backend."
        >
          {isLoading ? (
            <p className="muted-copy">Loading company network...</p>
          ) : companies.length === 0 ? (
            <EmptyState
              title="No companies yet"
              description="Register buyer companies and provider carriers from the company network page."
            />
          ) : (
            <div className="list-stack">
              {companies.slice(0, 6).map((company) => (
                <article key={`${company.company_name}-${company.company_type}`} className="list-card">
                  <div>
                    <h4>{company.company_name}</h4>
                    <p>{company.contact_email || "No contact email"} · {company.contact_phone || "No phone"}</p>
                  </div>
                  <div className="chip-list">
                    <span className={company.company_type === "provider" ? "role-pill role-provider" : "role-pill role-mediator"}>
                      {company.company_type}
                    </span>
                    <span className={company.is_active ? "status-pill status-active" : "status-pill"}>
                      {company.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </SectionCard>

        <SectionCard
          title="Published plan inventory"
          subtitle="Recently available provider plans and their pricing state."
        >
          {isLoading ? (
            <p className="muted-copy">Loading plan inventory...</p>
          ) : plans.length === 0 ? (
            <EmptyState
              title="No plans yet"
              description="Publish your first provider plan from the plan studio."
            />
          ) : (
            <div className="list-stack">
              {plans.slice(0, 6).map((plan) => (
                <article key={plan.plan_code} className="list-card">
                  <div>
                    <h4>{plan.plan_name}</h4>
                    <p>{plan.company_name} · {plan.plan_code}</p>
                  </div>
                  <strong className="currency-value">
                    Rs. {Number(plan.base_premium || 0).toLocaleString()}
                  </strong>
                </article>
              ))}
            </div>
          )}
        </SectionCard>
      </div>

      <div className="operations-stack">
        <SectionCard
          title="Quote-side visibility"
          subtitle="Provider-side quote documents flowing in from completed buyer journeys."
        >
          {isLoading ? (
            <p className="muted-copy">Loading quote activity...</p>
          ) : quotes.length === 0 ? (
            <EmptyState
              title="No quotes yet"
              description="Quotes will appear here after customer journeys request provider plan matches."
            />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Transaction</th>
                    <th>Items</th>
                    <th>Selected plan</th>
                  </tr>
                </thead>
                <tbody>
                  {quotes.slice(0, 8).map((quote) => (
                    <tr key={quote.transaction_id}>
                      <td>{quote.transaction_id}</td>
                      <td>{quote.items.length}</td>
                      <td>{quote.selected_plan_id || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>

        <SectionCard
          title="Payment-side visibility"
          subtitle="Provider-side payment records generated as customers move toward verification."
        >
          {isLoading ? (
            <p className="muted-copy">Loading payment activity...</p>
          ) : payments.length === 0 ? (
            <EmptyState
              title="No payments yet"
              description="Payment records will appear here after the customer journey reaches payment processing."
            />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Reference</th>
                    <th>Transaction</th>
                    <th>Status</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.slice(0, 8).map((payment) => (
                    <tr key={payment.payment_reference}>
                      <td>{payment.payment_reference}</td>
                      <td>{payment.transaction_id}</td>
                      <td>{payment.payment_status}</td>
                      <td>Rs. {Number(payment.amount || 0).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}

export default DashboardPage;
