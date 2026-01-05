import { useState } from "react";
import { CssBaseline, ThemeProvider } from "@mui/material";
import "mapbox-gl/dist/mapbox-gl.css";
import { Routes, Route, useNavigate } from "react-router-dom";
import "./App.css";
import Sidebar from "./Components/Global/Sidebar";
import Topbar from "./Components/Global/Topbar";
import MapBox from "./Components/MapBox";
import StationDataPage from "./Pages/StationDataPage";
import { ColorModeContext, useMode } from "./theme";

type LocationFocus = { center: [number, number]; radiusKm: number };

function App() {
  const [theme, colorMode] = useMode();
  const [isSideBarCollapsed, setIsSideBarCollapsed] = useState(false);

  const [locationFocus, setLocationFocus] = useState<LocationFocus | null>(null);

  const navigate = useNavigate();
  const onStationViewData = (stationId: string) => {
    navigate(`/station/${stationId}`);
  };

  const handleLocationSelected = (center: [number, number], radiusKm: number) => {
    setLocationFocus({ center, radiusKm });
  };

  return (
    <ColorModeContext.Provider value={colorMode}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <div className="app">
          <Topbar />
          <div className="app-body">
            <Sidebar
              isCollapsed={isSideBarCollapsed}
              setIsCollapsed={setIsSideBarCollapsed}
              onStationViewData={onStationViewData}
              onLocationSelected={handleLocationSelected}
            />

            <main className="content">
              <Routes>
                <Route
                  path="/"
                  element={
                    <MapBox isSideBarCollapsed={isSideBarCollapsed} locationFocus={locationFocus} />
                  }
                />
                <Route path="/station/:stationId" element={<StationDataPage />} />
              </Routes>
            </main>
          </div>
        </div>
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}

export default App;
