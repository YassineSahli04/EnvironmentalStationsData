import { useTheme } from "@mui/material";
import { Pulsar } from "ldrs/react";
import "ldrs/react/Pulsar.css";
import { tokens } from "../../theme";

type OverlayLoaderProps = {
  show: boolean;
  size?: number | string;
  speed?: number | string;
  fullScreen?: boolean;
  dim?: number;
  blockInteraction?: boolean;
};

export function OverlayLoader({
  show,
  size = 300,
  speed = 3,
  fullScreen = false,
  dim = 0.5,
  blockInteraction = true,
}: OverlayLoaderProps) {
  const theme = useTheme();
  const colors = tokens(theme.palette.mode);
  if (!show) return null;

  return (
    <div
      aria-busy="true"
      aria-live="polite"
      role="status"
      style={{
        position: fullScreen ? "fixed" : "absolute",
        inset: 0,
        zIndex: 9999,
        display: "grid",
        placeItems: "center",
        background: `rgba(0,0,0,${dim})`,
        pointerEvents: blockInteraction ? "auto" : "none",
      }}
    >
      <div style={{ display: "grid", placeItems: "center", gap: 10 }}>
        <Pulsar size={String(size)} speed={String(speed)} color={colors.primary[400]} />
      </div>
    </div>
  );
}
