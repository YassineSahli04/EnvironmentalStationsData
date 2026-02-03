import { useEffect, useRef } from "react";
import { useUser } from "@clerk/clerk-react";
import axios from "axios";

const API_URL = "http://localhost:8000/api";

export function useAuthSync() {
  const { isLoaded, isSignedIn, user } = useUser();
  const hasSynced = useRef(false);

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !user || hasSynced.current) {
      return;
    }

    const syncUser = async () => {
      try {
        await axios.post(`${API_URL}/users/sync`, {
          clerkId: user.id,
          email: user.primaryEmailAddress?.emailAddress,
          firstName: user.firstName,
          lastName: user.lastName,
          imageUrl: user.imageUrl,
        });
        hasSynced.current = true;
      } catch (error) {
        console.error("Failed to sync user:", error);
      }
    };

    // syncUser();
  }, [isLoaded, isSignedIn, user]);

  return { isLoaded, isSignedIn, user };
}

