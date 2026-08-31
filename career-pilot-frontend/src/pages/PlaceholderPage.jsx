import { Clock3 } from "lucide-react";
import { useLocation } from "react-router-dom";
export default function PlaceholderPage(){const label=useLocation().pathname.split("/").pop().replaceAll("-"," ");return <main className="page"><section className="surface placeholder-page"><Clock3 size={28}/><span className="section-eyebrow">Product preview</span><h1>{label.replace(/\b\w/g,x=>x.toUpperCase())}</h1><p>This workspace is coming soon. No AI behavior or integrations have been enabled yet.</p></section></main>}
