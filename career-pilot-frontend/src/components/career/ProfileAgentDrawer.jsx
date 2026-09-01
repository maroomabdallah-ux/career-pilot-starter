import { Bot, Send, Sparkles, X } from "lucide-react";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { apiErrorMessage, careerApi } from "../../services/careerApi";

export default function ProfileAgentDrawer() {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [threadId, setThreadId] = useState();
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(false);
  const client = useQueryClient();
  const send = async (message = text) => {
    if (!message.trim() || busy) return;
    setItems((old) => [...old, { type: "user", message }]); setText(""); setBusy(true);
    try {
      const reply = await careerApi.profileAgentChat({ message, thread_id: threadId });
      setThreadId(reply.thread_id); setItems((old) => [...old, reply]);
    } catch (error) { setItems((old) => [...old, { type: "error", message: apiErrorMessage(error) }]); }
    finally { setBusy(false); }
  };
  const decide = async (decision) => {
    setBusy(true);
    try { const reply = await careerApi.profileAgentApprove({ thread_id: threadId, decision }); setItems((old) => [...old, reply]); if (decision === "approve") { client.invalidateQueries({ queryKey: ["profile"] }); client.invalidateQueries({ queryKey: ["profile-completion"] }); client.invalidateQueries({ queryKey: ["dashboard"] }); } }
    catch { setItems((old) => [...old, { type: "error", message: "I couldn't save that change. Your profile has not been modified." }]); }
    finally { setBusy(false); }
  };
  return <>
    <button className="profile-agent-launch" onClick={() => setOpen(true)}><Sparkles size={16}/> Ask CareerPilot AI</button>
    {open && <aside className="profile-agent-drawer" aria-label="CareerPilot AI Assistant">
      <header><span><Bot size={18}/> CareerPilot AI</span><button className="icon-button" onClick={() => setOpen(false)}><X size={16}/></button></header>
      <div className="profile-agent-messages">
        {!items.length && <p className="agent-intro">Tell me about your career. I’ll always ask for approval before saving changes.</p>}
        {items.map((item, index) => <article key={index} className={`agent-message ${item.type}`}><p>{item.message}</p>
          {item.proposal && <div className="agent-proposal"><strong>{item.proposal.operation} {item.proposal.domain}</strong>{Object.entries(item.proposal.fields).map(([key, value]) => <span key={key}><small>{key.replaceAll("_", " ")}</small>{Array.isArray(value) ? value.join(", ") : String(value)}</span>)}<footer><button className="button secondary" onClick={() => decide("reject")} disabled={busy}>Reject</button><button className="button primary" onClick={() => decide("approve")} disabled={busy}>Approve</button></footer></div>}
        </article>)}
      </div>
      <form onSubmit={(event) => { event.preventDefault(); send(); }}><input value={text} onChange={(event) => setText(event.target.value)} placeholder="e.g. Add Python to my skills"/><button className="button primary" disabled={busy}><Send size={15}/></button></form>
    </aside>}
  </>;
}
