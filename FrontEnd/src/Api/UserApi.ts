import axios from "axios";
import type { UserDetails } from "./Objects/UserObj";
import { useQuery } from "@tanstack/react-query";

const usersUrl = "http://localhost:8000/api/users";

export async function getAllUsers(token: string): Promise<UserDetails[]> {
    const allUsersUrl = `${usersUrl}/all`;
    try {
      const response = await axios.get<UserDetails[]>(allUsersUrl, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return response.data;
    } catch (err) {
      if (axios.isAxiosError(err)) {
        console.error("Failed to fetch users:", {
          status: err.response?.status,
          detail: err.response?.data?.detail ?? err.message,
        });
      }
      throw err;
    }
  }
  
  export function useAllUsers(token: string | null) {
    return useQuery<UserDetails[]>({
      queryKey: ["allUsers", token],
      queryFn: () => getAllUsers(token!),
      enabled: !!token,
    });
  }
  