import { create } from "zustand";

const storedUserId = localStorage.getItem("career-pilot-user-id");

const useAppStore = create((set) => ({
  userId: storedUserId,
  sidebarOpen: false,
  setUserId: (userId) => {
    if (userId) localStorage.setItem("career-pilot-user-id", userId);
    else localStorage.removeItem("career-pilot-user-id");
    set({ userId });
  },
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
}));

export default useAppStore;
