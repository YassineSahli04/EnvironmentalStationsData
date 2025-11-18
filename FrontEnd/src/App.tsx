import { useState } from "react";
import { CssBaseline, ThemeProvider } from "@mui/material";
import "mapbox-gl/dist/mapbox-gl.css";
import { Routes, Route } from "react-router-dom";
import Sidebar from "./Components/Global/Sidebar";
import Topbar from "./Components/Global/Topbar";
import Home from "./Pages/Home";
import { ColorModeContext, useMode } from "./theme";

function App() {
  const [theme, colorMode] = useMode();
  const [isSideBarCollapsed, setIsSideBarCollapsed] = useState(false);

  return (
    <ColorModeContext.Provider value={colorMode}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <div className="app">
          <Topbar />
          <div className="app-body">
            <Sidebar isCollapsed={isSideBarCollapsed} setIsCollapsed={setIsSideBarCollapsed} />
            <main className="content">
              <Routes>
                <Route path="/" element={<Home isSideBarCollapsed={isSideBarCollapsed} />} />
              </Routes>
            </main>
          </div>
        </div>
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}

export default App;
