export type AppUser = { id: string; role: "user" | "admin"; typeFilter: string[] };

export type UserDetails = {
  Id: string;
  Email: string;
  FirstName: string | null;
  LastName: string | null;
  Role: "user" | "admin";
  CreatedAt: Date;
  IsSubscribedToStationAlerts: boolean;
  TypeFilter: string[];
};
