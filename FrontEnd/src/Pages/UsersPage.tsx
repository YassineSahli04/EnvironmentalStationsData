import { useMemo, useState, useEffect } from "react";
import { useAuth, useUser } from "@clerk/clerk-react";
import AdminPanelSettingsOutlinedIcon from "@mui/icons-material/AdminPanelSettingsOutlined";
import NotificationsActiveOutlinedIcon from "@mui/icons-material/NotificationsActiveOutlined";
import NotificationsOffOutlinedIcon from "@mui/icons-material/NotificationsOffOutlined";
import PeopleAltOutlinedIcon from "@mui/icons-material/PeopleAltOutlined";
import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";
import {
  Box,
  Typography,
  useTheme,
  Chip,
  Avatar,
  Skeleton,
  alpha,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
} from "@mui/material";
import { useQueryClient } from "@tanstack/react-query";
import type { UserDetails } from "../Api/Objects/UserObj";
import { getAllUsers, updateUserInfo } from "../Api/UserApi";
import { tokens } from "../theme";

type UsersPageProps = {
  isSideBarCollapsed: boolean;
};

type GetToken = () => Promise<string | null>;
type QueryClient = ReturnType<typeof useQueryClient>;

async function UpdateUserAsync(
  getToken: GetToken,
  newUserDetails: UserDetails,
  queryClient: QueryClient
) {
  try {
    const token = await getToken();
    if (!token) {
      throw new Error("Not authenticated");
    }
    await updateUserInfo(token, newUserDetails, queryClient);
  } catch (err) {
    console.log(err);
  }
}

export default function UsersPage({ isSideBarCollapsed }: UsersPageProps) {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  const { getToken } = useAuth();
  const { user: currentUser } = useUser();
  const queryClient = useQueryClient();

  const [users, setUsers] = useState<UserDetails[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setIsLoading(true);
        const token = await getToken();
        if (!token) {
          throw new Error("Not authenticated");
        }
        const usersData = await getAllUsers(token);
        setUsers(usersData);
        setError(null);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUsers();
  }, [getToken]);

  const stats = useMemo(() => {
    if (!users) return { total: 0, admins: 0, subscribers: 0 };
    return {
      total: users.length,
      admins: users.filter((u) => u.Role === "admin").length,
      subscribers: users.filter((u) => u.IsSubscribedToStationAlerts).length,
    };
  }, [users]);

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const toggleAlertSubscription = (id: string) => {
    const user = users?.find((u) => u.Id === id);
    if (!user) return;
  
    const newValue = !user.IsSubscribedToStationAlerts;

    setUsers(
      users?.map((u) =>
        u.Id === id ? { ...u, IsSubscribedToStationAlerts: newValue } : u
      ) || []
    );

    UpdateUserAsync(getToken, { ...user, IsSubscribedToStationAlerts: newValue }, queryClient);
  };

  const toggleRole = (id: string) => {
    const user = users?.find((u) => u.Id === id);
    if (!user) return;

    if (user.Email === currentUser?.emailAddresses.find(email => email.id ===  currentUser?.primaryEmailAddressId)?.emailAddress && user.Role === "admin") return;

    const newRole = user.Role === "admin" ? "user" : "admin";

    setUsers(
      users?.map((u) =>
        u.Id === id ? { ...u, Role: newRole } : u
      ) || []
    );

    UpdateUserAsync(getToken, { ...user, Role: newRole }, queryClient);
  };

  const paginatedUsers = useMemo(() => {
    if (!users) return [];
    return users.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  }, [users, page, rowsPerPage]);

  const StatCard = ({
    title,
    value,
    icon,
    gradient,
  }: {
    title: string;
    value: number;
    icon: React.ReactNode;
    gradient: string;
  }) => (
    <Box
      sx={{
        background: `linear-gradient(135deg, ${colors.primary[400]} 0%, ${alpha(colors.primary[400], 0.8)} 100%)`,
        borderRadius: "16px",
        p: 3,
        position: "relative",
        overflow: "hidden",
        border: `1px solid ${alpha(colors.grey[700], 0.3)}`,
        transition: "transform 0.2s ease, box-shadow 0.2s ease",
        "&:hover": {
          transform: "translateY(-4px)",
          boxShadow: `0 12px 40px ${alpha("#000", 0.3)}`,
        },
      }}
    >
      <Box
        sx={{
          position: "absolute",
          top: -20,
          right: -20,
          width: 100,
          height: 100,
          borderRadius: "50%",
          background: gradient,
          opacity: 0.15,
        }}
      />
      <Box display="flex" alignItems="center" gap={2}>
        <Box
          sx={{
            background: gradient,
            borderRadius: "12px",
            p: 1.5,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {icon}
        </Box>
        <Box>
          <Typography variant="h6" sx={{ color: colors.grey[400], fontSize: "0.85rem" }}>
            {title}
          </Typography>
          {isLoading ? (
            <Skeleton width={60} height={40} sx={{ bgcolor: colors.primary[300] }} />
          ) : (
            <Typography variant="h3" sx={{ fontWeight: 700, letterSpacing: "-0.02em" }}>
              {value}
            </Typography>
          )}
        </Box>
      </Box>
    </Box>
  );

  const TableSkeleton = () => (
    <>
      {[...Array(5)].map((_, index) => (
        <TableRow key={index}>
          <TableCell>
            <Skeleton
              variant="circular"
              width={36}
              height={36}
              sx={{ bgcolor: colors.primary[300] }}
            />
          </TableCell>
          <TableCell>
            <Skeleton width={80} sx={{ bgcolor: colors.primary[300] }} />
          </TableCell>
          <TableCell>
            <Skeleton width={80} sx={{ bgcolor: colors.primary[300] }} />
          </TableCell>
          <TableCell>
            <Skeleton width={150} sx={{ bgcolor: colors.primary[300] }} />
          </TableCell>
          <TableCell>
            <Skeleton width={60} sx={{ bgcolor: colors.primary[300] }} />
          </TableCell>
          <TableCell>
            <Skeleton width={100} sx={{ bgcolor: colors.primary[300] }} />
          </TableCell>
          <TableCell>
            <Skeleton width={50} sx={{ bgcolor: colors.primary[300] }} />
          </TableCell>
        </TableRow>
      ))}
    </>
  );

  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        overflow: "auto",
        p: 3,
        background: `linear-gradient(180deg, ${colors.primary[500]} 0%, ${alpha(colors.primary[600], 0.95)} 100%)`,
      }}
    >
      {/* Header */}
      <Box mb={4}>
        <Box display="flex" alignItems="center" gap={2} mb={1}>
          <Box
            sx={{
              background: `linear-gradient(135deg, ${colors.blueAccent[500]} 0%, ${colors.greenAccent[500]} 100%)`,
              borderRadius: "12px",
              p: 1.5,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <PeopleAltOutlinedIcon sx={{ fontSize: "1.75rem" }} />
          </Box>
          <Box>
            <Typography
              variant="h2"
              sx={{
                fontWeight: 700,
                background: `linear-gradient(135deg, ${colors.grey[100]} 0%, ${colors.blueAccent[300]} 100%)`,
                backgroundClip: "text",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                letterSpacing: "-0.02em",
              }}
            >
              Users Dashboard
            </Typography>
            <Typography sx={{ color: colors.grey[400], mt: 0.5 }}>
              Manage and monitor all registered users
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(240px, 1fr))" gap={3} mb={4}>
        <StatCard
          title="Total Users"
          value={stats.total}
          icon={<PeopleAltOutlinedIcon sx={{ color: "#fff", fontSize: "1.5rem" }} />}
          gradient={`linear-gradient(135deg, ${colors.blueAccent[500]} 0%, ${colors.blueAccent[600]} 100%)`}
        />
        <StatCard
          title="Administrators"
          value={stats.admins}
          icon={<AdminPanelSettingsOutlinedIcon sx={{ color: "#fff", fontSize: "1.5rem" }} />}
          gradient={`linear-gradient(135deg, ${colors.redAccent[500]} 0%, ${colors.redAccent[600]} 100%)`}
        />
        <StatCard
          title="Alert Subscribers"
          value={stats.subscribers}
          icon={<NotificationsActiveOutlinedIcon sx={{ color: "#fff", fontSize: "1.5rem" }} />}
          gradient={`linear-gradient(135deg, ${colors.greenAccent[500]} 0%, ${colors.greenAccent[600]} 100%)`}
        />
      </Box>

      {/* Users Table */}
      <Paper
        sx={{
          background: alpha(colors.primary[400], 0.6),
          borderRadius: "16px",
          border: `1px solid ${alpha(colors.grey[700], 0.3)}`,
          overflow: "hidden",
          backdropFilter: "blur(10px)",
        }}
      >
        {error ? (
          <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            p={6}
            gap={2}
          >
            <Typography variant="h5" color="error">
              Failed to load users
            </Typography>
            <Typography sx={{ color: colors.grey[400] }}>
              You may not have permission to view this data
            </Typography>
          </Box>
        ) : (
          <>
            <TableContainer>
              <Table sx={{ minWidth: 650 }}>
                <TableHead>
                  <TableRow
                    sx={{
                      background: alpha(colors.primary[500], 0.8),
                      "& th": {
                        fontWeight: 600,
                        color: colors.grey[200],
                        textTransform: "uppercase",
                        fontSize: "0.75rem",
                        letterSpacing: "0.05em",
                        borderBottom: `1px solid ${alpha(colors.grey[700], 0.5)}`,
                        py: 2,
                      },
                    }}
                  >
                    <TableCell></TableCell>
                    <TableCell>First Name</TableCell>
                    <TableCell>Last Name</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Role</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Alerts</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {isLoading ? (
                    <TableSkeleton />
                  ) : (
                    paginatedUsers.map((user) => {
                      const initials =
                        `${user.FirstName?.[0] || ""}${user.LastName?.[0] || ""}`.toUpperCase();
                      const isAdmin = user.Role === "admin";
                      const date = new Date(user.CreatedAt);

                      return (
                        <TableRow
                          key={user.Id}
                          sx={{
                            "&:hover": {
                              backgroundColor: alpha(colors.blueAccent[500], 0.08),
                            },
                            "& td": {
                              borderBottom: `1px solid ${alpha(colors.grey[700], 0.3)}`,
                              py: 1.5,
                            },
                          }}
                        >
                          <TableCell>
                            <Avatar
                              sx={{
                                width: 36,
                                height: 36,
                                background: `linear-gradient(135deg, ${colors.blueAccent[500]} 0%, ${colors.greenAccent[500]} 100%)`,
                                fontSize: "0.875rem",
                                fontWeight: 600,
                              }}
                            >
                              {initials || "?"}
                            </Avatar>
                          </TableCell>
                          <TableCell>
                            <Typography sx={{ fontWeight: 500 }}>
                              {user.FirstName || "—"}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography sx={{ fontWeight: 500 }}>{user.LastName || "—"}</Typography>
                          </TableCell>
                          <TableCell>
                            <Typography
                              sx={{
                                color: colors.blueAccent[400],
                                fontFamily: "'JetBrains Mono', 'Consolas', monospace",
                                fontSize: "0.85rem",
                              }}
                            >
                              {user.Email}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {(() => {
                              const isSelf = user.Email === currentUser?.emailAddresses.find(email => email.id ===  currentUser?.primaryEmailAddressId)?.emailAddress;
                              const isDisabled = isSelf && isAdmin;
                              return (
                                <Chip
                                  icon={
                                    isAdmin ? (
                                      <AdminPanelSettingsOutlinedIcon
                                        sx={{ fontSize: "1rem !important" }}
                                      />
                                    ) : (
                                      <PersonOutlineOutlinedIcon sx={{ fontSize: "1rem !important" }} />
                                    )
                                  }
                                  onClick={() => !isDisabled && toggleRole(user.Id)}
                                  label={isAdmin ? "Admin" : "User"}
                                  size="small"
                                  sx={{
                                    cursor: isDisabled ? "not-allowed" : "pointer",
                                    opacity: isDisabled ? 0.6 : 1,
                                    background: isAdmin
                                      ? `linear-gradient(135deg, ${alpha(colors.redAccent[500], 0.2)} 0%, ${alpha(colors.redAccent[400], 0.3)} 100%)`
                                      : `linear-gradient(135deg, ${alpha(colors.blueAccent[500], 0.2)} 0%, ${alpha(colors.blueAccent[400], 0.3)} 100%)`,
                                    color: isAdmin ? colors.redAccent[300] : colors.blueAccent[300],
                                    borderRadius: "8px",
                                    fontWeight: 600,
                                    fontSize: "0.75rem",
                                    border: `1px solid ${isAdmin ? alpha(colors.redAccent[500], 0.3) : alpha(colors.blueAccent[500], 0.3)}`,
                                    "& .MuiChip-icon": {
                                      color: "inherit",
                                    },
                                  }}
                                />
                              );
                            })()}
                          </TableCell>
                          <TableCell>
                            <Box>
                              <Typography sx={{ fontSize: "0.85rem", fontWeight: 500 }}>
                                {date.toLocaleDateString("en-US", {
                                  month: "short",
                                  day: "numeric",
                                  year: "numeric",
                                })}
                              </Typography>
                              <Typography sx={{ fontSize: "0.7rem", color: colors.grey[400] }}>
                                {date.toLocaleTimeString("en-US", {
                                  hour: "2-digit",
                                  minute: "2-digit",
                                })}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip
                              icon={
                                user.IsSubscribedToStationAlerts ? (
                                  <NotificationsActiveOutlinedIcon
                                    sx={{ fontSize: "1rem !important" }}
                                  />
                                ) : (
                                  <NotificationsOffOutlinedIcon
                                    sx={{ fontSize: "1rem !important" }}
                                  />
                                )
                              }
                              onClick={() => toggleAlertSubscription(user.Id)}
                              label={user.IsSubscribedToStationAlerts ? "On" : "Off"}
                              size="small"
                              sx={{
                                cursor: "pointer",
                                background: user.IsSubscribedToStationAlerts
                                  ? `linear-gradient(135deg, ${alpha(colors.greenAccent[500], 0.2)} 0%, ${alpha(colors.greenAccent[400], 0.3)} 100%)`
                                  : alpha(colors.grey[700], 0.5),
                                color: user.IsSubscribedToStationAlerts
                                  ? colors.greenAccent[300]
                                  : colors.grey[400],
                                borderRadius: "8px",
                                fontWeight: 600,
                                fontSize: "0.75rem",
                                border: `1px solid ${user.IsSubscribedToStationAlerts ? alpha(colors.greenAccent[500], 0.3) : alpha(colors.grey[600], 0.3)}`,
                                "& .MuiChip-icon": {
                                  color: "inherit",
                                },
                              }}
                            />
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              rowsPerPageOptions={[10, 25, 50]}
              component="div"
              count={users?.length || 0}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              sx={{
                borderTop: `1px solid ${alpha(colors.grey[700], 0.3)}`,
                background: alpha(colors.primary[500], 0.8),
                color: colors.grey[200],
                "& .MuiTablePagination-select": {
                  color: colors.grey[200],
                },
                "& .MuiTablePagination-selectIcon": {
                  color: colors.grey[400],
                },
                "& .MuiTablePagination-actions .MuiIconButton-root": {
                  color: colors.grey[300],
                  "&.Mui-disabled": {
                    color: colors.grey[600],
                  },
                },
              }}
            />
          </>
        )}
      </Paper>
    </Box>
  );
}
