"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Role = "operator" | "administrator" | "scientist";

interface AuthState {
  token: string | null;
  role: Role | null;
  fullName: string | null;
  email: string | null;
  setSession: (session: { token: string; role: Role; fullName: string; email: string }) => void;
  clearSession: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      role: null,
      fullName: null,
      email: null,
      setSession: ({ token, role, fullName, email }) => set({ token, role, fullName, email }),
      clearSession: () => set({ token: null, role: null, fullName: null, email: null }),
    }),
    { name: "polar-ems-auth" }
  )
);
