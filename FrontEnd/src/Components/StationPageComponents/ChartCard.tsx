import type { ReactNode } from "react";
import { Box, Typography, Collapse } from "@mui/material";

type ChartCardProps = {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  actions?: ReactNode;
  expanded?: boolean;
  onToggle?: () => void;
  accentColor?: string;
};

export default function ChartCard({
  title,
  subtitle,
  children,
  actions,
  expanded = true,
  onToggle,
  accentColor = "#3b82f6",
}: ChartCardProps) {
  const isCollapsible = onToggle !== undefined;

  return (
    <Box
      sx={{
        bgcolor: "#1F2A40",
        borderRadius: 3,
        overflow: "hidden",
        boxShadow: expanded
          ? "0 8px 32px rgba(0,0,0,0.3)"
          : "0 4px 16px rgba(0,0,0,0.2)",
        border: "1px solid rgba(255,255,255,0.06)",
        mb: 2,
        mt: 2,
        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
      }}
    >
      {/* Header */}
      {(title || subtitle || actions) && (
        <Box
          onClick={isCollapsible ? onToggle : undefined}
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            px: 2.5,
            py: 2,
            cursor: isCollapsible ? "pointer" : "default",
            userSelect: isCollapsible ? "none" : "auto",
            background: expanded
              ? `linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, transparent 60%)`
              : "transparent",
            borderBottom: expanded ? "1px solid rgba(255,255,255,0.06)" : "none",
            transition: "all 0.3s ease",
            "&:hover": isCollapsible
              ? {
                  background: `linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(59, 130, 246, 0.02) 60%)`,
                }
              : undefined,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            {/* Accent bar / indicator */}
            <Box
              sx={{
                width: 4,
                height: expanded ? 44 : 32,
                borderRadius: 2,
                background: expanded
                  ? `linear-gradient(180deg, ${accentColor} 0%, ${accentColor}88 100%)`
                  : "rgba(148, 163, 184, 0.3)",
                transition: "all 0.3s ease",
                boxShadow: expanded ? `0 0 12px ${accentColor}40` : "none",
              }}
            />
            <Box>
              {title && (
                <Typography
                  sx={{
                    fontWeight: 700,
                    fontSize: "1.1rem",
                    color: expanded ? "#f8fafc" : "#cbd5e1",
                    letterSpacing: "0.01em",
                    transition: "color 0.3s ease",
                  }}
                >
                  {title}
                </Typography>
              )}
              {subtitle && (
                <Typography
                  sx={{
                    fontSize: "0.8rem",
                    color: "#64748b",
                    mt: 0.25,
                    fontWeight: 500,
                    opacity: expanded ? 1 : 0.7,
                    transition: "opacity 0.3s ease",
                  }}
                >
                  {subtitle}
                </Typography>
              )}
            </Box>
          </Box>

          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            {actions && <Box onClick={(e) => e.stopPropagation()}>{actions}</Box>}

            {/* Modern toggle indicator */}
            {isCollapsible && (
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 36,
                  height: 36,
                  borderRadius: 2,
                  bgcolor: expanded ? "rgba(59, 130, 246, 0.15)" : "rgba(148, 163, 184, 0.1)",
                  transition: "all 0.3s ease",
                  "&:hover": {
                    bgcolor: expanded ? "rgba(59, 130, 246, 0.25)" : "rgba(148, 163, 184, 0.2)",
                  },
                }}
              >
                {/* Animated chevron lines */}
                <Box
                  sx={{
                    position: "relative",
                    width: 12,
                    height: 12,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "3px",
                  }}
                >
                  <Box
                    sx={{
                      width: 8,
                      height: 2,
                      borderRadius: 1,
                      bgcolor: expanded ? "#3b82f6" : "#94a3b8",
                      transform: expanded
                        ? "rotate(-45deg) translateX(2px)"
                        : "rotate(45deg) translateX(2px)",
                      transformOrigin: "center",
                      transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                    }}
                  />
                  <Box
                    sx={{
                      width: 8,
                      height: 2,
                      borderRadius: 1,
                      bgcolor: expanded ? "#3b82f6" : "#94a3b8",
                      transform: expanded
                        ? "rotate(45deg) translateX(-2px)"
                        : "rotate(-45deg) translateX(-2px)",
                      transformOrigin: "center",
                      transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                    }}
                  />
                </Box>
              </Box>
            )}
          </Box>
        </Box>
      )}

      {/* Body with Collapse animation */}
      <Collapse in={expanded} timeout={300}>
        <Box sx={{ p: 2 }}>{children}</Box>
      </Collapse>
    </Box>
  );
}
