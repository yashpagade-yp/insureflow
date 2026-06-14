import { useEffect, useMemo, useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import StatCard from "../components/StatCard";
import { listCompanies, listPlans } from "../lib/api";

function DashboardPage() {
  const [companies, setCompanies] = useState([]);
  const [plans, setPlans] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const [companyResponse, planResponse] = await Promise.all([
          listCompanies(),
          listPlans(),
        ]);

        setCompanies(companyResponse.items ?? []);
        setPlans(planResponse.items ?? []);
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
    const providerCompanies = companies.filter(
      (item) => item.company_type === "provider"
    ).length;
    const mediatorCompanies = companies.filter(
      (item) => item.company_type === "mediator"
    ).length;

    return [
      {
        label: "Registered companies",
        value: companies.length,
        helper: `${activeCompanies} active right now`,
      },
      {
        label: "Provider companies",
        value: providerCompanies,
        helper: "Health insurers ready for plan publishing",
      },
      {
        label: "Mediator companies",
        value: mediatorCompanies,
        helper: "Broker-side health distribution integrations configured",
      },
      {
        label: "Published plans",
        value: plans.length,
        helper: "Live health policy records in provider backend",
      },
    ];
  }, [companies, plans]);

  return (
    <div className="page-stack">
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

      <div className="content-grid">
        <SectionCard
          title="Recent companies"
          subtitle="A quick look at the latest health-insurance-side organization records."
        >
          {isLoading ? (
            <p className="muted-copy">Loading companies...</p>
          ) : companies.length === 0 ? (
            <EmptyState
              title="No companies yet"
              description="Create the mediator and provider companies from the Companies page."
            />
          ) : (
            <div className="list-stack">
              {companies.slice(0, 4).map((company) => (
                <article key={`${company.company_name}-${company.company_type}`} className="list-card">
                  <div>
                    <h4>{company.company_name}</h4>
                    <p>
                      {company.company_type} | {company.contact_email || "No email"}
                    </p>
                  </div>
                  <span className={company.is_active ? "status-pill status-active" : "status-pill"}>
                    {company.is_active ? "Active" : "Inactive"}
                  </span>
                </article>
              ))}
            </div>
          )}
        </SectionCard>

        <SectionCard
          title="Recent plans"
          subtitle="Published health insurance products available in the provider backend."
        >
          {isLoading ? (
            <p className="muted-copy">Loading plans...</p>
          ) : plans.length === 0 ? (
            <EmptyState
              title="No plans yet"
              description="Create the first provider plan from the Plans page."
            />
          ) : (
            <div className="list-stack">
              {plans.slice(0, 4).map((plan) => (
                <article key={plan.plan_code} className="list-card">
                  <div>
                    <h4>{plan.plan_name}</h4>
                    <p>
                      {plan.company_name} | {plan.insurance_type} | {plan.plan_code}
                    </p>
                  </div>
                  <strong className="currency-value">
                    Rs. {plan.base_premium.toLocaleString()}
                  </strong>
                </article>
              ))}
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}

export default DashboardPage;
