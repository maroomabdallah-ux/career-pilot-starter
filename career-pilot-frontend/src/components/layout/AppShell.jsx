import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import useAppStore from "../../store/useAppStore";
import ProfileAgentDrawer from "../career/ProfileAgentDrawer";

export default function AppShell() {
  const location = useLocation();
  const resumeEditor = /^\/app\/resume\/[^/]+\/edit$/.test(location.pathname);
  const open = useAppStore((state) => state.sidebarOpen);
  const setOpen = useAppStore((state) => state.setSidebarOpen);
  return (
    <div className={`app-shell ${resumeEditor ? "resume-editor-app" : ""}`}>
      {!resumeEditor && <Sidebar />}
      {open && <button className="sidebar-scrim" aria-label="Close menu" onClick={() => setOpen(false)} />}
      <div className="workspace">
        {!resumeEditor && <Topbar />}
        <div className="page-transition" key={location.pathname}>
          <Outlet />
        </div>
        {!resumeEditor && <ProfileAgentDrawer />}
      </div>
    </div>
  );
}
