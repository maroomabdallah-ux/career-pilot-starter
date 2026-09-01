import { Bell, Menu, Search, SlidersHorizontal } from "lucide-react";
import { useCareerData } from "../../hooks/useCareerData";
import useAppStore from "../../store/useAppStore";

export default function Topbar() {
  const setOpen = useAppStore((state) => state.setSidebarOpen);
  const { user, profile } = useCareerData();
  const name = user.data
    ? `${user.data.first_name} ${user.data.last_name}`
    : "Career professional";
  const initials = user.data
    ? `${user.data.first_name[0]}${user.data.last_name[0]}`
    : "CP";
  return (
    <header className="topbar">
      <button className="icon-button menu-button" onClick={() => setOpen(true)}>
        <Menu size={21} />
      </button>
      <label className="global-search">
        <Search size={18} />
        <input
          aria-label="Search"
          placeholder="Search jobs, skills, or companies"
        />
        <kbd>⌘ K</kbd>
      </label>
      <div className="topbar-actions">
        <button className="icon-button quiet">
          <SlidersHorizontal size={18} />
        </button>
        <button className="icon-button quiet notification">
          <Bell size={18} />
          <span />
        </button>
        <div className="user-chip">
          <span className="avatar">
            {profile.data?.profile_picture ? (
              <img src={profile.data.profile_picture} alt="" />
            ) : (
              initials
            )}
          </span>
          <span className="user-copy">
            <strong>{name}</strong>
            <small>Essential plan</small>
          </span>
        </div>
      </div>
    </header>
  );
}
