import { useEffect, useRef } from "react";
import { useUser, useAuth } from "@clerk/clerk-react";
import axios from "axios";

const API_URL = "http://localhost:8000/api";

export function useAuthSync() {
  const { isLoaded, isSignedIn, user } = useUser();
  const { getToken } = useAuth();
  const hasSynced = useRef(false);

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !user || hasSynced.current) {
      return;
    }

    const syncUser = async () => {
      try {
        const token = await getToken();
        
        await axios.post(
          `${API_URL}/users/sync`,
          {},
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        hasSynced.current = true;
      } catch (error) {
        console.error("Failed to sync user:", error);
      }
    };

    syncUser();
  }, [isLoaded, isSignedIn, user, getToken]);

  return { isLoaded, isSignedIn, user };
}
