import { useRef, useEffect, useState, useCallback } from "react";
import MapOutlinedIcon from "@mui/icons-material/MapOutlined";
import SatelliteAltIcon from "@mui/icons-material/SatelliteAlt";
import { Box, IconButton } from "@mui/material";
import mapboxgl from "mapbox-gl";
import { GeoJSONSource } from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { getStationsGeojson } from "../ApiService/Api";
import { getMapDataForParam } from "../ApiService/DataHandling";
import type { CfSensorDataRow } from "../ApiService/Objects/StationObj";
import MapParamPanel from "./MapParamPanel";
import { WeatherParam } from "./MapParamPanel";
import "./SCSS/MapBox.scss";

const STYLE_STREETS = "mapbox://styles/mapbox/streets-v12";
const STYLE_SATELLITE = "mapbox://styles/mapbox/satellite-streets-v12";

type MapBoxProps = {
  isSideBarCollapsed: boolean;
};

export default function MapBox({ isSideBarCollapsed }: MapBoxProps) {
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const geoDataRef = useRef<any>(null);
  const prevStyleRef = useRef<string>(STYLE_SATELLITE);

  const [mapStyle, setMapStyle] = useState<string>(STYLE_SATELLITE);
  const [isMapLoaded, setIsMapLoaded] = useState(false);
  const [selectedParam, setSelectedParam] = useState<WeatherParam | undefined>();
  const prevParamRef = useRef<WeatherParam | undefined>(undefined);
  const prevDateRef = useRef<Date | undefined>(undefined);
  const paramDataRef = useRef<Record<string, CfSensorDataRow[]>>({});

  useEffect(() => {
    if (!mapRef.current) return;
    const timeoutId = setTimeout(() => {
      if (mapRef.current && mapRef.current.getCanvas()) {
        mapRef.current.resize();
      }
    }, 250);
    return () => clearTimeout(timeoutId);
  }, [isSideBarCollapsed]);

  const addStationLayers = useCallback(() => {
    if (!mapRef.current || !geoDataRef.current) return;

    mapRef.current.addSource("earthquakes", {
      type: "geojson",
      generateId: true,
      data: geoDataRef.current,
      cluster: true,
      clusterMaxZoom: 14,
      clusterRadius: 50,
    });

    mapRef.current.addLayer({
      id: "clusters",
      type: "circle",
      source: "earthquakes",
      filter: ["has", "point_count"],
      paint: {
        "circle-color": ["step", ["get", "point_count"], "#FFAB40", 5, "#FF7043", 10, "#E53935"],
        "circle-radius": ["step", ["get", "point_count"], 20, 5, 30, 10, 40],
        "circle-emissive-strength": 1,
      },
    });

    mapRef.current.addLayer({
      id: "cluster-count",
      type: "symbol",
      source: "earthquakes",
      filter: ["has", "point_count"],
      layout: {
        "text-field": ["get", "point_count_abbreviated"],
        "text-font": ["DIN Offc Pro Medium", "Arial Unicode MS Bold"],
        "text-size": 12,
      },
    });

    mapRef.current.addLayer({
      id: "unclustered-point",
      type: "circle",
      source: "earthquakes",
      filter: ["!", ["has", "point_count"]],
      paint: {
        "circle-color": [
          "case",
          ["==", ["get", "manufacturer"], "Pessl"],
          "#e53935",
          ["==", ["get", "manufacturer"], "DeltaOHM"],
          "#1e88e5",
          "#757575",
        ],
        "circle-radius": 6,
        "circle-stroke-width": 1,
        "circle-stroke-color": "#fff",
        "circle-emissive-strength": 1,
      },
    });

    mapRef.current.addSource("stations-plain", {
      type: "geojson",
      data: geoDataRef.current,
    });
    mapRef.current.addLayer({
      id: "station-param-points",
      type: "circle",
      source: "stations-plain",
      paint: {
        "circle-color": "#757575",
        "circle-radius": 6,
        "circle-stroke-width": 1,
        "circle-stroke-color": "#fff",
        "circle-emissive-strength": 1,
      },
      layout: {
        visibility: "none",
      },
    });
  }, []);

  const addInteractions = useCallback(() => {
    if (!mapRef.current) return;

    // Shared handlers
    const handleStationClick = (e: any) => {
      if (!mapRef.current || !e.feature) return;
      const coordinates = (e.feature.geometry as any).coordinates.slice();
      const props = e.feature.properties;

      const popup = new mapboxgl.Popup()
        .setLngLat(coordinates)
        .setHTML(
          `
          <div class="station-popup" style="cursor: pointer;">
            <h3 style="color: #2238ffff; margin: 0;">${props?.name}</h3>
            <p style="color: #000000ff; margin: 4px 0 0 0;">
              <strong style="color:#000000ff;">ID:</strong> ${props?.id}<br />
              <strong style="color:#000000ff;">Manuf:</strong> ${props?.manufacturer}<br />
              ${props?.type ? `<strong style="color:#000000ff;">Type:</strong> ${props.type}<br />` : ""}
              <strong style="color:#000000ff;">Lon:</strong> ${coordinates[0].toFixed(4)}, 
              <strong style="color:#000000ff;">Lat:</strong> ${coordinates[1].toFixed(4)}
              ${props?.paramValue != null ? `<br /><strong style="color:#000000ff;">${props.param?.toString()}:</strong> ${props.paramValue.toFixed(2)}` : ""}
            </p>
          </div>
        `
        )
        .addTo(mapRef.current);

      const popupElement = popup
        .getElement()
        ?.querySelector(".station-popup") as HTMLDivElement | null;
      if (popupElement) {
        popupElement.addEventListener("click", () => {
          console.log(`Station ID: ${props?.name}`);
        });
      }
    };

    const handleMouseEnter = () => {
      if (mapRef.current) mapRef.current.getCanvas().style.cursor = "pointer";
    };

    const handleMouseLeave = () => {
      if (mapRef.current) mapRef.current.getCanvas().style.cursor = "";
    };

    // Cluster interactions
    mapRef.current.addInteraction("click-clusters", {
      type: "click",
      target: { layerId: "clusters" },
      handler: (e) => {
        if (!mapRef.current) return;
        const features = mapRef.current.queryRenderedFeatures(e.point, {
          layers: ["clusters"],
        });
        if (features.length === 0 || !features[0].properties) return;
        const clusterId = features[0].properties.cluster_id;
        const source = mapRef.current.getSource("earthquakes") as mapboxgl.GeoJSONSource;
        source?.getClusterExpansionZoom(clusterId, (err: any, zoom: any) => {
          if (err) return;
          mapRef.current?.easeTo({
            center: (features[0].geometry as any).coordinates,
            zoom: zoom,
          });
        });
      },
    });

    mapRef.current.addInteraction("clustered-mouseenter", {
      type: "mouseenter",
      target: { layerId: "clusters" },
      handler: handleMouseEnter,
    });

    mapRef.current.addInteraction("clustered-mouseleave", {
      type: "mouseleave",
      target: { layerId: "clusters" },
      handler: handleMouseLeave,
    });

    // Station point interactions (unclustered-point and station-param-points)
    ["unclustered-point", "station-param-points"].forEach((layerId) => {
      mapRef.current!.addInteraction(`click-${layerId}`, {
        type: "click",
        target: { layerId },
        handler: handleStationClick,
      });

      mapRef.current!.addInteraction(`mouseenter-${layerId}`, {
        type: "mouseenter",
        target: { layerId },
        handler: handleMouseEnter,
      });

      mapRef.current!.addInteraction(`mouseleave-${layerId}`, {
        type: "mouseleave",
        target: { layerId },
        handler: handleMouseLeave,
      });
    });
  }, []);

  useEffect(() => {
    mapboxgl.accessToken =
      "pk.eyJ1IjoieWFzc2luZS1zYWhsaSIsImEiOiJjbWkwZHhlamMwaWgxMmxweWloOWJ3YmdtIn0.dJtTsXAcQy2eErlpsMoUWA";

    if (!mapContainerRef.current) return;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: STYLE_SATELLITE,
      center: [9.25477, 34.26822],
      zoom: 1.5,
    });

    map.setPadding({ top: 0, bottom: 0, left: 0, right: 250 });
    mapRef.current = map;

    map.on("load", async () => {
      geoDataRef.current = await getStationsGeojson();
      addStationLayers();
      addInteractions();
      setIsMapLoaded(true);
    });

    return () => {
      map.remove();
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current || !isMapLoaded) return;

    if (prevStyleRef.current === mapStyle) return;
    prevStyleRef.current = mapStyle;

    mapRef.current.once("style.load", () => {
      addStationLayers();
      applyParamMode();
    });

    mapRef.current.setStyle(mapStyle);
  }, [mapStyle, isMapLoaded, addStationLayers, addInteractions]);

  const applyParamMode = useCallback(() => {
    if (!mapRef.current || !isMapLoaded) return;
    switch (selectedParam !== undefined) {
      case true:
        mapRef.current.setLayoutProperty("clusters", "visibility", "none");
        mapRef.current.setLayoutProperty("cluster-count", "visibility", "none");
        mapRef.current.setLayoutProperty("unclustered-point", "visibility", "none");

        mapRef.current.setLayoutProperty("station-param-points", "visibility", "visible");
        mapRef.current.setPaintProperty(
          "station-param-points",
          "circle-color",
          getParamColorScale()
        );
        mapRef.current.flyTo({ center: [11.08813, 34.13523], zoom: 5.54 });
        break;
      case false:
        mapRef.current.setLayoutProperty("clusters", "visibility", "visible");
        mapRef.current.setLayoutProperty("cluster-count", "visibility", "visible");
        mapRef.current.setLayoutProperty("unclustered-point", "visibility", "visible");

        mapRef.current.setLayoutProperty("station-param-points", "visibility", "none");
        break;
    }
  }, [selectedParam, isMapLoaded]);

  const getParamColorScale = (): mapboxgl.ExpressionSpecification => {
    switch (selectedParam) {
      case WeatherParam.TEMPERATURE:
        return [
          "interpolate",
          ["linear"],
          ["get", "paramValue"],
          0,
          "#1F77B4",
          10,
          "#76B7E0",
          20,
          "#2ECC71",
          30,
          "#F1C40F",
          35,
          "#E67E22",
          40,
          "#E74C3C",
        ];
      case WeatherParam.RELATIVE_HUMIDITY:
        return [
          "interpolate",
          ["linear"],
          ["get", "paramValue"],
          30,
          "#E57373",
          50,
          "#FB8C00",
          70,
          "#66BB6A",
          90,
          "#42A5F5",
          100,
          "#8E44AD",
        ];
      case WeatherParam.WIND_SPEED:
        return [
          "interpolate",
          ["linear"],
          ["get", "paramValue"],
          1,
          "#CFD8DC",
          3,
          "#81D4FA",
          7,
          "#FFD54F",
          10,
          "#FB8C00",
          15,
          "#E53935",
        ];
      case WeatherParam.SOLAR_RADIATION:
        return [
          "interpolate",
          ["linear"],
          ["get", "paramValue"],
          200,
          "#ECEFF1",
          400,
          "#4FC3F7",
          700,
          "#66BB6A",
          900,
          "#FFEB3B",
          1000,
          "#E53935",
        ];
      case WeatherParam.PRECIPITATION:
        return [
          "interpolate",
          ["linear"],
          ["get", "paramValue"],
          0,
          "#B0BEC5",
          5,
          "#81D4FA",
          20,
          "#1E88E5",
          50,
          "#8E44AD",
          75,
          "#C62828",
        ];
      default:
        return ["get", "paramValue"];
    }
  };

  const getParamLegendData = (): { value: number; color: string }[] => {
    switch (selectedParam) {
      case WeatherParam.TEMPERATURE:
        return [
          { value: 0, color: "#1F77B4" },
          { value: 10, color: "#76B7E0" },
          { value: 20, color: "#2ECC71" },
          { value: 30, color: "#F1C40F" },
          { value: 35, color: "#E67E22" },
          { value: 40, color: "#E74C3C" },
        ];
      case WeatherParam.RELATIVE_HUMIDITY:
        return [
          { value: 30, color: "#E57373" },
          { value: 50, color: "#FB8C00" },
          { value: 70, color: "#66BB6A" },
          { value: 90, color: "#42A5F5" },
          { value: 100, color: "#8E44AD" },
        ];
      case WeatherParam.WIND_SPEED:
        return [
          { value: 1, color: "#CFD8DC" },
          { value: 3, color: "#81D4FA" },
          { value: 7, color: "#FFD54F" },
          { value: 10, color: "#FB8C00" },
          { value: 15, color: "#E53935" },
        ];
      case WeatherParam.SOLAR_RADIATION:
        return [
          { value: 200, color: "#ECEFF1" },
          { value: 400, color: "#4FC3F7" },
          { value: 700, color: "#66BB6A" },
          { value: 900, color: "#FFEB3B" },
          { value: 1000, color: "#E53935" },
        ];
      case WeatherParam.PRECIPITATION:
        return [
          { value: 0, color: "#B0BEC5" },
          { value: 5, color: "#81D4FA" },
          { value: 20, color: "#1E88E5" },
          { value: 50, color: "#8E44AD" },
          { value: 75, color: "#C62828" },
        ];
      default:
        return [];
    }
  };

  const getParamUnit = (): string => {
    switch (selectedParam) {
      case WeatherParam.TEMPERATURE:
        return "°C";
      case WeatherParam.RELATIVE_HUMIDITY:
        return "%";
      case WeatherParam.WIND_SPEED:
        return "m/s";
      case WeatherParam.SOLAR_RADIATION:
        return "W/m²";
      case WeatherParam.PRECIPITATION:
        return "mm";
      default:
        return "";
    }
  };

  useEffect(() => {
    applyParamMode();
  }, [selectedParam]);

  const onSelectedParamChange = async (
    param: WeatherParam | undefined,
    dataOption: string | undefined,
    date: Date
  ) => {
    if (!mapRef.current || !geoDataRef.current || !param || !dataOption) return;
    if (!param || !dataOption) {
      setSelectedParam(undefined);
      return;
    }

    const source = mapRef.current.getSource("stations-plain") as GeoJSONSource | undefined;
    if (!source) return;

    if (param !== prevParamRef.current && date !== prevDateRef.current) {
      paramDataRef.current = await getMapDataForParam(param, date);
      prevParamRef.current = param;
      prevDateRef.current = date;
    }

    const updatedGeoJson = {
      ...geoDataRef.current,
      features: geoDataRef.current.features.map((f) => {
        const rows = paramDataRef.current[f.properties.id];
        const lastRow = rows && rows.length > 0 ? rows[rows.length - 1] : null;
        const lastValue = lastRow ? lastRow.values[dataOption] : null;
        const featureUpdated = {
          ...f,
          properties: { ...f.properties, param: param, paramValue: lastValue },
        };
        return featureUpdated;
      }),
    };
    geoDataRef.current = updatedGeoJson;
    source.setData(updatedGeoJson as any);
    setSelectedParam(param);
  };

  return (
    <Box sx={{ position: "relative", width: "100%", height: "100%" }}>
      {/* Param Filter div */}
      <MapParamPanel onSelectedParamChange={onSelectedParamChange} />
      {/* Map Style Toggle */}
      <Box
        sx={{
          position: "absolute",
          bottom: 25,
          right: "-3%",
          transform: "translateX(-50%)",
          zIndex: 2,
          display: "flex",
          backgroundColor: "white",
          borderRadius: "50px",
          padding: "6px 8px",
          boxShadow: "0 2px 12px rgba(0,0,0,0.15)",
        }}
      >
        <IconButton
          onClick={() => setMapStyle(STYLE_STREETS)}
          sx={{
            width: 44,
            height: 44,
            backgroundColor: mapStyle === STYLE_STREETS ? "#1976d2" : "transparent",
            color: mapStyle === STYLE_STREETS ? "white" : "#5f6368",
            "&:hover": {
              backgroundColor: mapStyle === STYLE_STREETS ? "#1565c0" : "rgba(0,0,0,0.04)",
            },
            transition: "all 0.2s ease",
          }}
        >
          <MapOutlinedIcon />
        </IconButton>
        <IconButton
          onClick={() => setMapStyle(STYLE_SATELLITE)}
          sx={{
            width: 44,
            height: 44,
            backgroundColor: mapStyle === STYLE_SATELLITE ? "#1976d2" : "transparent",
            color: mapStyle === STYLE_SATELLITE ? "white" : "#5f6368",
            "&:hover": {
              backgroundColor: mapStyle === STYLE_SATELLITE ? "#1565c0" : "rgba(0,0,0,0.04)",
            },
            transition: "all 0.2s ease",
          }}
        >
          <SatelliteAltIcon />
        </IconButton>
      </Box>

      {/* Color Scale Legend */}
      {selectedParam && (
        <Box
          sx={{
            position: "absolute",
            bottom: 25,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 2,
            backgroundColor: "rgba(255, 255, 255, 0.92)",
            borderRadius: "10px",
            padding: "10px 16px",
            boxShadow: "0 2px 10px rgba(0,0,0,0.12)",
          }}
        >
          <Box
            sx={{
              fontSize: 11,
              fontWeight: 600,
              color: "#444",
              textAlign: "center",
              marginBottom: "6px",
              letterSpacing: "0.3px",
            }}
          >
            {selectedParam} ({getParamUnit()})
          </Box>
          <Box
            sx={{
              width: 240,
              height: 12,
              borderRadius: "6px",
              background: `linear-gradient(to right, ${getParamLegendData()
                .map((d) => d.color)
                .join(", ")})`,
            }}
          />
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              width: 240,
              marginTop: "5px",
            }}
          >
            {getParamLegendData().map((d, i) => (
              <Box
                key={i}
                sx={{
                  fontSize: 10,
                  color: "#555",
                }}
              >
                {d.value}
              </Box>
            ))}
          </Box>
        </Box>
      )}

      <div id="map-container" ref={mapContainerRef} />
    </Box>
  );
}
