import {
  BadgeHelp,
  BookOpen,
  BriefcaseBusiness,
  CircleUserRound,
  CreditCard,
  FileText,
  FolderKanban,
  GraduationCap,
  LayoutDashboard,
  MessageSquareText,
  Settings,
  Sparkles,
  Wrench,
  X,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import useAppStore from "../../store/useAppStore";

const primary = [
  ["Dashboard", "/", LayoutDashboard, true],
  ["My Profile", "/profile", CircleUserRound],
  ["Education", "/profile/education", GraduationCap],
  ["Experience", "/profile/experience", BriefcaseBusiness],
  ["Projects", "/profile/projects", FolderKanban],
  ["Skills", "/profile/skills", Wrench],
];

const careerTools = [
  ["Resume Studio", "/resume", FileText],
  ["Job Matches", "/jobs", Sparkles],
  ["Applications", "/applications", BookOpen],
  ["Interview Prep", "/interview", MessageSquareText],
];

const secondary = [
  ["Premium & Billing", "/billing", CreditCard],
  ["Settings", "/settings", Settings],
  ["Help & Support", "/help", BadgeHelp],
];

function RailLink({ item, onNavigate }) {
  const [label, path, Icon, end] = item;
  return (
    <NavLink
      className={({ isActive }) => `rail-link ${isActive ? "active" : ""}`}
      to={path}
      end={end}
      aria-label={label}
      onClick={onNavigate}
    >
      <Icon size={19} strokeWidth={1.8} />
      <span className="rail-tooltip" role="tooltip">{label}</span>
    </NavLink>
  );
}

export default function Sidebar() {
  const open = useAppStore((state) => state.sidebarOpen);
  const setOpen = useAppStore((state) => state.setSidebarOpen);
  const close = () => setOpen(false);

  return (
    <aside className={`sidebar navigation-rail ${open ? "is-open" : ""}`}>
      <div className="rail-top">
        <NavLink className="rail-logo" to="/" aria-label="CareerPilot AI" onClick={close}>
          <img src="/careerpilot-logo.png" alt="CareerPilot AI" />
        </NavLink>
        <button className="icon-button rail-close mobile-only" onClick={close} aria-label="Close navigation">
          <X size={18} />
        </button>
        <NavLink className="rail-ai" to="/profile" aria-label="AI Assistant" onClick={close}>
          <Sparkles size={18} strokeWidth={1.8} />
          <span className="rail-tooltip">AI Assistant</span>
        </NavLink>
      </div>

      <nav className="rail-navigation" aria-label="Main navigation">
        <div className="rail-group">{primary.map((item) => <RailLink key={item[0]} item={item} onNavigate={close} />)}</div>
        <div className="rail-divider" />
        <div className="rail-group">{careerTools.map((item) => <RailLink key={item[0]} item={item} onNavigate={close} />)}</div>
      </nav>

      <div className="rail-bottom">
        <div className="rail-divider" />
        {secondary.map((item) => <RailLink key={item[0]} item={item} onNavigate={close} />)}
        <NavLink className="rail-avatar" to="/profile" aria-label="User profile" onClick={close}>
          CP<span className="rail-tooltip">Your profile</span>
        </NavLink>
      </div>
    </aside>
  );
}
