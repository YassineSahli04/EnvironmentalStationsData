import { useQuery, type QueryClient } from "@tanstack/react-query";
import axios from "axios";
import type { UserDetails } from "./Objects/UserObj";

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

export type UpdateUserDetailsPayload = {
  IsSubscribedToStationAlerts: boolean;
  Role: "user" | "admin";
};

export async function updateUserInfo(
  token: string,
  updatedUserDetails: UserDetails,
  queryClient?: QueryClient
): Promise<UserDetails> {
  const updateUserUrl = `${usersUrl}/update/${updatedUserDetails.Id}`;
  try {
    const payload: UpdateUserDetailsPayload = {
      IsSubscribedToStationAlerts: updatedUserDetails.IsSubscribedToStationAlerts,
      Role: updatedUserDetails.Role,
    };
    const response = await axios.patch<UserDetails>(updateUserUrl, payload, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (queryClient) {
      queryClient.setQueryData(
        ["allUsers", token],
        (oldData: UserDetails[] | undefined) =>
          oldData?.map((u) =>
            u.Id === updatedUserDetails.Id ? response.data : u
          )
      );
    }

    return response.data;
  } catch (err) {
    if (axios.isAxiosError(err)) {
      console.error("Failed to update user:", {
        status: err.response?.status,
        detail: err.response?.data?.detail ?? err.message,
      });
    }
    throw err;
  }
}
