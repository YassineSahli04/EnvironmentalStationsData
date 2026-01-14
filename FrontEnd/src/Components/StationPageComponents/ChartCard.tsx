import type { ReactNode } from "react";
import { Box, Typography } from "@mui/material";

type ChartCardProps = {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  actions?: ReactNode;
};

export default function ChartCard({ title, subtitle, children, actions }: ChartCardProps) {
  return (
    <Box
      sx={{
        bgcolor: "#1F2A40",
        borderRadius: 2,
        overflow: "hidden",
        boxShadow: "0 4px 20px rgba(0,0,0,0.25)",
        border: "1px solid rgba(255,255,255,0.05)",
        mb: 2,
        mt: 2,
      }}
    >
      {/* Header */}
      {(title || subtitle || actions) && (
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            p: 2,
            pb: 0,
            borderBottom: "1px solid rgba(255,255,255,0.05)",
          }}
        >
          <Box>
            {title && (
              <Typography
                variant="h5"
                sx={{
                  fontWeight: 800,
                  color: "#f1f5f9",
                  mb: 0.5,
                }}
              >
                {title}
              </Typography>
            )}
            {subtitle && (
              <Typography variant="body2" sx={{ color: "#94a3b8", pb: 1 }}>
                {subtitle}
              </Typography>
            )}
          </Box>
          {actions && <Box>{actions}</Box>}
        </Box>
      )}

      {/* Body */}
      <Box sx={{ p: 2 }}>{children}</Box>
    </Box>
  );
}
