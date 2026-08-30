export default function SectionHeading({ eyebrow, title, copy, action }) {
  return (
    <div className="section-heading">
      <div>{eyebrow && <span className="section-eyebrow">{eyebrow}</span>}<h2>{title}</h2>{copy && <p>{copy}</p>}</div>
      {action}
    </div>
  );
}
