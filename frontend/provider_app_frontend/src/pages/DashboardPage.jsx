import { useEffect, useMemo, useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import StatCard from "../components/StatCard";
import { listCompanies, listPayments, listPlans, listQuotes } from "../lib/api";

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
        const [companyResponse, planResponse, quoteResponse, paymentResponse] =
          await Promise.all([
            listCompanies(),
            listPlans(),
            listQuotes(),
            listPayments(),
          ]);

        setCompanies(companyResponse.items ?? []);
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

  const dashboardStats = useMemo(() => {
    const activeCompanies = companies.filter((item) => item.is_active).length;
    const mediatorCompanies = companies.filter(
      (item) => item.company_type === "mediator"
    ).length;
    const providerCompanies = companies.filter(
      (item) => item.company_type === "provider"
    ).length;

    return [
      {
        label: "Registered companies",
        value: companies.length,
        helper: `${activeCompanies} active across mediator and provider roles`,
      },
      {
        label: "Provider companies",
        value: providerCompanies,
        helper: "Insurance carriers available for plan publishing",
      },
      {
        label: "Published plans",
        value: plans.length,
        helper: "Plan inventory currently available to quote generation",
      },
      {
        label: "Live activity",
        value: quotes.length + payments.length,
        helper: `${quotes.length} quotes and ${payments.length} payments seen on the provider side`,
      },
    ];
  }, [companies, payments.length, plans.length, quotes.length]);

  return (
    <div className="page-stack">
      <header className="page-intro">
        <p className="eyebrow-text">Provider-admin overview</p>
        <h2>Better coverage begins with clear decisions, trusted partners, and care that reaches people on time.</h2>
        <p className="muted-copy">
          Build a health-insurance network that feels dependable from the first onboarding step to the final policy purchase.
        </p>
      </header>

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

      <SectionCard title="Provider promise" subtitle="The work here supports a smoother, more trustworthy insurance experience.">
        <div className="banner-grid">
          <article className="hero-mini-card">
            <strong>Trust starts early</strong>
            <p>Strong onboarding creates a cleaner path for every company, every plan, and every future customer.</p>
          </article>
          <article className="hero-mini-card">
            <strong>Good networks matter</strong>
            <p>The right insurer relationships turn technical setup into real protection that people can rely on.</p>
          </article>
          <article className="hero-mini-card">
            <strong>Clarity builds confidence</strong>
            <p>Well-structured plans and add-ons help teams explain value with confidence and consistency.</p>
          </article>
          <article className="hero-mini-card">
            <strong>Care should feel seamless</strong>
            <p>When quotes and payments move smoothly, the insurance journey feels faster, safer, and more reassuring.</p>
          </article>
        </div>
      </SectionCard>

      <div className="content-grid">
        <SectionCard title="Recent companies" subtitle="Mediator and provider registrations from the backend.">
          {isLoading ? (
            <p className="muted-copy">Loading companies...</p>
          ) : companies.length === 0 ? (
            <EmptyState
              title="No companies yet"
              description="Register the buyer app and provider companies from the Companies page."
            />
          ) : (
            <div className="list-stack">
              {companies.slice(0, 6).map((company) => (
                <article key={`${company.company_name}-${company.company_type}`} className="list-card">
                  <div>
                    <h4>{company.company_name}</h4>
                    <p>{company.company_type} · {company.contact_email || "No contact email"}</p>
                  </div>
                  <span className={company.is_active ? "status-pill status-active" : "status-pill"}>
                    {company.is_active ? "Active" : "Inactive"}
                  </span>
                </article>
              ))}
            </div>
          )}
        </SectionCard>

        <SectionCard title="Recent plans" subtitle="Published plan records exposed to quote generation.">
          {isLoading ? (
            <p className="muted-copy">Loading plans...</p>
          ) : plans.length === 0 ? (
            <EmptyState
              title="No plans yet"
              description="Create the first provider plan from the Plans page."
            />
          ) : (
            <div className="list-stack">
              {plans.slice(0, 6).map((plan) => (
                <article key={plan.plan_code} className="list-card">
                  <div>
                    <h4>{plan.plan_name}</h4>
                    <p>{plan.company_name} · {plan.plan_code}</p>
                  </div>
                  <strong className="currency-value">Rs. {plan.base_premium.toLocaleString()}</strong>
                </article>
              ))}
            </div>
          )}
        </SectionCard>
      </div>

      <div className="content-grid">
        <SectionCard title="Provider-side quotes" subtitle="Latest quote journeys visible to the provider admin.">
          {isLoading ? (
            <p className="muted-copy">Loading quotes...</p>
          ) : quotes.length === 0 ? (
            <EmptyState
              title="No quotes yet"
              description="Quotes will appear once the customer app submits a completed form and asks the provider backend for plan matches."
            />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Transaction</th>
                    <th>Selected plan</th>
                    <th>Items</th>
                  </tr>
                </thead>
                <tbody>
                  {quotes.slice(0, 8).map((quote) => (
                    <tr key={quote.transaction_id}>
                      <td>{quote.transaction_id}</td>
                      <td>{quote.selected_plan_id || "-"}</td>
                      <td>{quote.items.length}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>

        <SectionCard title="Provider-side payments" subtitle="Latest payment records processed by the provider backend.">
          {isLoading ? (
            <p className="muted-copy">Loading payments...</p>
          ) : payments.length === 0 ? (
            <EmptyState
              title="No payments yet"
              description="Provider-side payment records will appear here after a customer reaches the payment verification step."
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
