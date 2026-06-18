import { useEffect, useMemo, useState } from "react";

import EmptyState from "../components/EmptyState";
import SectionCard from "../components/SectionCard";
import { createPlan, listPlans, listProviderCompanies } from "../lib/api";

const initialAddOn = {
  name: "",
  description: "",
  price: "",
};

const initialPlanState = {
  company_name: "",
  logo_url: "",
  plan_name: "",
  plan_code: "",
  insurance_type: "health",
  coverage_amount: "",
  base_premium: "",
  duration_years: "",
  benefits: [""],
  terms: "",
  available_add_ons: [initialAddOn],
};

function PlansPage() {
  const [planFormState, setPlanFormState] = useState(initialPlanState);
  const [plans, setPlans] = useState([]);
  const [providerCompanies, setProviderCompanies] = useState([]);
  const [status, setStatus] = useState({ type: "", message: "" });
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const hasProviderCompanies = providerCompanies.length > 0;

  useEffect(() => {
    async function loadPageData() {
      setIsLoading(true);
      setStatus({ type: "", message: "" });

      try {
        const [plansResponse, companiesResponse] = await Promise.all([
          listPlans(),
          listProviderCompanies(),
        ]);

        const providers = companiesResponse.items ?? [];

        setPlans(plansResponse.items ?? []);
        setProviderCompanies(providers);
        setPlanFormState((currentState) => ({
          ...currentState,
          company_name:
            currentState.company_name || providers[0]?.company_name || "",
        }));
      } catch (error) {
        setStatus({ type: "error", message: error.message });
      } finally {
        setIsLoading(false);
      }
    }

    loadPageData();
  }, []);

  const planPreview = useMemo(() => {
    return {
      company: planFormState.company_name || "Choose provider company",
      premium: planFormState.base_premium || "0",
      coverage: planFormState.coverage_amount || "0",
      duration: planFormState.duration_years || "0",
    };
  }, [planFormState]);

  const updatePlanField = (event) => {
    const { name, value } = event.target;
    setPlanFormState((currentState) => ({ ...currentState, [name]: value }));
  };

  const updateBenefit = (index, value) => {
    setPlanFormState((currentState) => {
      const nextBenefits = [...currentState.benefits];
      nextBenefits[index] = value;
      return { ...currentState, benefits: nextBenefits };
    });
  };

  const addBenefit = () => {
    setPlanFormState((currentState) => ({
      ...currentState,
      benefits: [...currentState.benefits, ""],
    }));
  };

  const removeBenefit = (index) => {
    setPlanFormState((currentState) => ({
      ...currentState,
      benefits: currentState.benefits.filter((_, benefitIndex) => benefitIndex !== index),
    }));
  };

  const updateAddOn = (index, fieldName, value) => {
    setPlanFormState((currentState) => {
      const nextAddOns = currentState.available_add_ons.map((item, addOnIndex) =>
        addOnIndex === index ? { ...item, [fieldName]: value } : item
      );

      return { ...currentState, available_add_ons: nextAddOns };
    });
  };

  const addAddOn = () => {
    setPlanFormState((currentState) => ({
      ...currentState,
      available_add_ons: [...currentState.available_add_ons, initialAddOn],
    }));
  };

  const removeAddOn = (index) => {
    setPlanFormState((currentState) => ({
      ...currentState,
      available_add_ons: currentState.available_add_ons.filter(
        (_, addOnIndex) => addOnIndex !== index
      ),
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus({ type: "", message: "" });
    setIsSubmitting(true);

    try {
      const payload = {
        ...planFormState,
        coverage_amount: Number(planFormState.coverage_amount),
        base_premium: Number(planFormState.base_premium),
        duration_years: Number(planFormState.duration_years),
        benefits: planFormState.benefits.filter(Boolean),
        available_add_ons: planFormState.available_add_ons
          .filter((item) => item.name && item.description && item.price !== "")
          .map((item) => ({
            ...item,
            price: Number(item.price),
          })),
      };

      await createPlan(payload);
      setStatus({ type: "success", message: "Provider plan created successfully." });
      const plansResponse = await listPlans();
      setPlans(plansResponse.items ?? []);
      setPlanFormState({
        ...initialPlanState,
        company_name: providerCompanies[0]?.company_name || "",
      });
    } catch (error) {
      setStatus({ type: "error", message: error.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-stack">
      {status.message ? (
        <div className={status.type === "error" ? "alert-box alert-error" : "alert-box alert-success"}>
          {status.message}
        </div>
      ) : null}

      <div className="content-grid content-grid-wide">
        <SectionCard
          title="Create provider plan"
          subtitle="Publish a health insurance plan with benefits and optional riders."
        >
          {!hasProviderCompanies ? (
            <EmptyState
              title="Create a provider company first"
              description="Plans can only be attached to provider companies."
            />
          ) : (
            <form className="form-grid" onSubmit={handleSubmit}>
              <label className="field-label">
                <span>Provider company</span>
                <select
                  className="field-input"
                  name="company_name"
                  value={planFormState.company_name}
                  onChange={updatePlanField}
                  required
                >
                  {providerCompanies.map((company) => (
                    <option key={company.company_name} value={company.company_name}>
                      {company.company_name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field-label">
                <span>Logo URL</span>
                <input
                  className="field-input"
                  name="logo_url"
                  value={planFormState.logo_url}
                  onChange={updatePlanField}
                  placeholder="https://example.com/logo.png"
                />
              </label>

              <label className="field-label">
                <span>Plan name</span>
                <input
                  className="field-input"
                  name="plan_name"
                  value={planFormState.plan_name}
                  onChange={updatePlanField}
                  placeholder="Acme Family Health Shield"
                  required
                />
              </label>

              <label className="field-label">
                <span>Plan code</span>
                <input
                  className="field-input"
                  name="plan_code"
                  value={planFormState.plan_code}
                  onChange={updatePlanField}
                  placeholder="HEALTH-ACME-001"
                  required
                />
              </label>

              <label className="field-label">
                <span>Insurance type</span>
                <select
                  className="field-input"
                  name="insurance_type"
                  value={planFormState.insurance_type}
                  onChange={updatePlanField}
                >
                  <option value="health">Health</option>
                  <option value="life">Life</option>
                  <option value="general">General</option>
                </select>
              </label>

              <label className="field-label">
                <span>Coverage amount</span>
                <input
                  className="field-input"
                  type="number"
                  min="0"
                  name="coverage_amount"
                  value={planFormState.coverage_amount}
                  onChange={updatePlanField}
                  placeholder="500000"
                  required
                />
              </label>

              <label className="field-label">
                <span>Base premium</span>
                <input
                  className="field-input"
                  type="number"
                  min="0"
                  name="base_premium"
                  value={planFormState.base_premium}
                  onChange={updatePlanField}
                  placeholder="12000"
                  required
                />
              </label>

              <label className="field-label">
                <span>Duration years</span>
                <input
                  className="field-input"
                  type="number"
                  min="1"
                  name="duration_years"
                  value={planFormState.duration_years}
                  onChange={updatePlanField}
                  placeholder="20"
                  required
                />
              </label>

              <label className="field-label field-span-full">
                <span>Terms</span>
                <textarea
                  className="field-input field-textarea"
                  name="terms"
                  value={planFormState.terms}
                  onChange={updatePlanField}
                  placeholder="Sample plan terms"
                  rows="4"
                />
              </label>

              <div className="field-span-full">
                <div className="inline-header">
                  <h4>Benefits</h4>
                  <button type="button" className="ghost-button" onClick={addBenefit}>
                    Add benefit
                  </button>
                </div>
                <div className="stacked-fields">
                  {planFormState.benefits.map((benefit, index) => (
                    <div key={`benefit-${index}`} className="inline-field-row">
                      <input
                        className="field-input"
                        value={benefit}
                        onChange={(event) => updateBenefit(index, event.target.value)}
                        placeholder="Hospitalization cover"
                      />
                      {planFormState.benefits.length > 1 ? (
                        <button
                          type="button"
                          className="ghost-button ghost-button-danger"
                          onClick={() => removeBenefit(index)}
                        >
                          Remove
                        </button>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>

              <div className="field-span-full">
                <div className="inline-header">
                  <h4>Available add-ons</h4>
                  <button type="button" className="ghost-button" onClick={addAddOn}>
                    Add add-on
                  </button>
                </div>

                <div className="stacked-fields">
                  {planFormState.available_add_ons.map((addOn, index) => (
                    <div key={`addon-${index}`} className="addon-card">
                      <div className="addon-grid">
                        <input
                          className="field-input"
                          value={addOn.name}
                          onChange={(event) => updateAddOn(index, "name", event.target.value)}
                          placeholder="Critical Illness Rider"
                        />
                        <input
                          className="field-input"
                          value={addOn.price}
                          onChange={(event) => updateAddOn(index, "price", event.target.value)}
                          placeholder="1500"
                          type="number"
                          min="0"
                        />
                        <input
                          className="field-input addon-description"
                          value={addOn.description}
                          onChange={(event) =>
                            updateAddOn(index, "description", event.target.value)
                          }
                          placeholder="Extra protection for major treatment events"
                        />
                      </div>
                      {planFormState.available_add_ons.length > 1 ? (
                        <button
                          type="button"
                          className="ghost-button ghost-button-danger"
                          onClick={() => removeAddOn(index)}
                        >
                          Remove add-on
                        </button>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>

              <button className="primary-button" type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Publishing..." : "Create provider plan"}
              </button>
            </form>
          )}
        </SectionCard>

        <SectionCard
          title="Live plan preview"
          subtitle="A quick health-plan summary of the current form values."
        >
          <div className="preview-panel">
            <div className="preview-header">
              <p className="eyebrow-text">Current draft</p>
              <h3>{planFormState.plan_name || "Untitled health insurance plan"}</h3>
            </div>
            <dl className="preview-grid">
              <div>
                <dt>Company</dt>
                <dd>{planPreview.company}</dd>
              </div>
              <div>
                <dt>Base premium</dt>
                <dd>Rs. {planPreview.premium}</dd>
              </div>
              <div>
                <dt>Coverage</dt>
                <dd>Rs. {planPreview.coverage}</dd>
              </div>
              <div>
                <dt>Duration</dt>
                <dd>{planPreview.duration} years</dd>
              </div>
            </dl>
          </div>
        </SectionCard>
      </div>

      <SectionCard
        title="Published provider plans"
        subtitle="Review existing health plans and confirm their rider structure."
      >
        {isLoading ? (
          <p className="muted-copy">Loading plans...</p>
        ) : plans.length === 0 ? (
          <EmptyState
            title="No plans published yet"
            description="Create your first provider plan from the form above."
          />
        ) : (
          <div className="plan-card-grid">
            {plans.map((plan) => (
              <article key={plan.plan_code} className="plan-card">
                <div className="plan-card-header">
                  <div>
                    <p className="eyebrow-text">{plan.company_name}</p>
                    <h3>{plan.plan_name}</h3>
                  </div>
                  <span className="status-pill">{plan.insurance_type}</span>
                </div>

                <div className="plan-card-meta">
                  <span>{plan.plan_code}</span>
                  <span>Rs. {plan.base_premium.toLocaleString()}</span>
                  <span>{plan.duration_years} years</span>
                </div>

                <p className="plan-card-copy">
                  Coverage: Rs. {plan.coverage_amount.toLocaleString()}
                </p>

                {plan.available_add_ons.length > 0 ? (
                  <div className="chip-list">
                    {plan.available_add_ons.map((addOn) => (
                      <span key={`${plan.plan_code}-${addOn.name}`} className="info-chip">
                        {addOn.name} | Rs. {addOn.price}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="muted-copy">No add-ons configured.</p>
                )}
              </article>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}

export default PlansPage;
