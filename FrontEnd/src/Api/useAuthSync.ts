import { useEffect, useRef } from "react";
import { useUser, useAuth } from "@clerk/clerk-react";
import axios from "axios";
import { useAppUser } from "../Context/AppUserContext.tsx";
import type { AppUser } from "./Objects/UserObj.ts";

const API_URL = import.meta.env.VITE_API_URL;
const url = `${API_URL}/api`;

export function useAuthSync() {
  const { isLoaded, isSignedIn, user } = useUser();
  const { getToken } = useAuth();
  const hasSynced = useRef(false);
  const { appUser, setAppUser } = useAppUser();

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !user || hasSynced.current) {
      return;
    }

    const syncUser = async () => {
      try {
        const token = await getToken();

        const { data } = await axios.post<AppUser>(
          `${url}/users/sync`,
          {},
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        setAppUser(data);
        hasSynced.current = true;
      } catch (error) {
        console.error("Failed to sync user:", error);
      }
    };

    syncUser();
  }, [isLoaded, isSignedIn, user, getToken, setAppUser]);

  return { isLoaded, isSignedIn, user, appUser };
}
