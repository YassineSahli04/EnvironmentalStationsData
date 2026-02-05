export type AppUser = { id: string; role: "user" | "admin" };

export type UserDetails = {
  Email: string;
  FirstName: string | null;
  LastName: string | null;
  Role: "user" | "admin";
  CreatedAt: Date;
  IsSubscribedToStationAlerts: boolean;
};
