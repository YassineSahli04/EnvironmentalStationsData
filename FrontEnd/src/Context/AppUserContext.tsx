import { createContext, useState, useContext } from "react";
import type { Dispatch, ReactNode, SetStateAction } from "react";
import type { AppUser } from "../Api/Objects/UserObj";

type AppUserContextValue = {
  appUser: AppUser | null;
  setAppUser: Dispatch<SetStateAction<AppUser | null>>;
};

const AppUserContext = createContext<AppUserContextValue | undefined>(undefined);

export function AppUserProvider({ children }: { children: ReactNode }) {
  const [appUser, setAppUser] = useState<AppUser | null>(null);

  return (
    <AppUserContext.Provider value={{ appUser, setAppUser }}>{children}</AppUserContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAppUser() {
  const ctx = useContext(AppUserContext);
  if (!ctx) throw new Error("useAppUser must be used inside AppUserProvider");
  return ctx;
}
