import { Check, Pencil, Sparkles, X } from "lucide-react";

export function AIQualityBadge({ quality }) {
  if (!quality) return null;
  const labels = { strong:"Strong", good:"Good", needs_improvement:"Could be stronger", weak:"Needs improvement", insufficient_information:"Needs detail" };
  return <span className={`quality-label quality-${quality}`}>{labels[quality] || quality}</span>;
}

export function AIActionMenu({ actions, busy }) {
  return <div className="inline-ai-actions">{actions.map(action=><button type="button" key={action.label} disabled={busy} className={action.primary?"primary":""} onClick={action.onClick}>{action.sparkle!==false&&<Sparkles size={12}/>} {action.label}</button>)}</div>;
}

export function AISuggestionCard({ suggestion, current, onUse, onEdit, onDismiss }) {
  return <article className="ai-suggestion-option"><header><span>{suggestion.label || "CareerPilot suggestion"}</span><small>Grounded suggestion</small></header>{current&&<div className="rewrite-current"><b>Current</b><p>{current}</p></div>}<div className="rewrite-suggested"><b>Suggested</b><p>{suggestion.suggestion}</p></div><small className="suggestion-reason">{suggestion.reason}</small><footer><button className="use" onClick={onUse}><Check size={12}/>Use this</button><button onClick={onEdit}><Pencil size={12}/>Edit first</button><button onClick={onDismiss}><X size={12}/>Dismiss</button></footer></article>;
}

export function AIClarificationCard({ question, answer, setAnswer, onContinue, busy }) {
  return <div className="ai-clarification-card"><strong>CareerPilot needs one detail</strong><p>{question}</p><textarea rows="3" value={answer} onChange={event=>setAnswer(event.target.value)} placeholder="Answer CareerPilot…"/><button disabled={!answer.trim()||busy} onClick={onContinue}>Continue with my answer</button><small>Your answer is used for this Resume. It is not silently added to your Profile.</small></div>;
}

export function ResumeAIHint({ onClose }) {
  return <div className="resume-ai-hint"><span><Sparkles size={15}/></span><div><strong>CareerPilot AI can help write every section</strong><p>Look for ✨ actions beside Summary, Experience, Projects, Education, and Skills.</p></div><button onClick={onClose}>Got it</button></div>;
}
