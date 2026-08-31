import { Link, Outlet } from "react-router-dom";
export default function PublicLayout() {
  return <div className="public-shell"><header className="public-header"><Link to="/" className="public-logo"><img src="/careerpilot-logo.png" alt="CareerPilot AI"/></Link><nav><Link to="/login">Sign in</Link><Link className="button primary" to="/signup">Get started</Link></nav></header><Outlet/></div>;
}
