function SectionCard({ title, subtitle, actions, children }) {
  return (
    <section className="section-card">
      <div className="section-head">
        <div>
          <h3>{title}</h3>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        {actions ? <div>{actions}</div> : null}
      </div>
      <div className="section-body">{children}</div>
    </section>
  );
}

export default SectionCard;
