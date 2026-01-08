import { useState } from "react";
import { CssBaseline, ThemeProvider } from "@mui/material";
import "mapbox-gl/dist/mapbox-gl.css";
import { Routes, Route, useNavigate } from "react-router-dom";
import { PrefetchData } from "./Api/PrefetchData";
import "./App.css";
import Sidebar from "./Components/Global/Sidebar";
import Topbar from "./Components/Global/Topbar";
import MapBox from "./Components/MapBox";
import StationDataPage from "./Pages/StationDataPage";
import { ColorModeContext, useMode } from "./theme";

function App() {
  const [theme, colorMode] = useMode();
  const [isSideBarCollapsed, setIsSideBarCollapsed] = useState(false);

  const navigate = useNavigate();
  const onStationViewData = (stationId: string) => {
    navigate(`/station/${stationId}`);
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
            />

            <main className="content">
              <PrefetchData />
              <Routes>
                <Route path="/" element={<MapBox isSideBarCollapsed={isSideBarCollapsed} />} />
                <Route
                  path="/station/:stationId"
                  element={<StationDataPage isSideBarCollapsed={isSideBarCollapsed} />}
                />
              </Routes>
            </main>
          </div>
        </div>
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}

export default App;
