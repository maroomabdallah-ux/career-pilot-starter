import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import useAppStore from "../../store/useAppStore";
import ProfileAgentDrawer from "../career/ProfileAgentDrawer";

export default function AppShell() {
  const location = useLocation();
  const open = useAppStore((state) => state.sidebarOpen);
  const setOpen = useAppStore((state) => state.setSidebarOpen);
  return (
    <div className="app-shell">
      <Sidebar />
      {open && <button className="sidebar-scrim" aria-label="Close menu" onClick={() => setOpen(false)} />}
      <div className="workspace">
        <Topbar />
        <div className="page-transition" key={location.pathname}>
          <Outlet />
        </div>
        <ProfileAgentDrawer />
      </div>
    </div>
  );
}
