import { useRef, useEffect, useState, useCallback } from "react";
import MapOutlinedIcon from "@mui/icons-material/MapOutlined";
import SatelliteAltIcon from "@mui/icons-material/SatelliteAlt";
import { Box, IconButton } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import * as turf from "@turf/turf";
import mapboxgl from "mapbox-gl";
import { GeoJSONSource } from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { useNavigate } from "react-router-dom";
import { getStationsGeojson } from "../Api/StationApi";
import { WeatherParam } from "../Api/StationApi";
import { getMapDataForParam } from "../Api/DataHandling";
import type { SensorDataRow } from "../Api/Objects/StationObj";
import { OverlayLoader } from "./Global/OverlayLoader";
import MapParamPanel from "./MapParamPanel";
import "./SCSS/MapBox.scss";

const STYLE_STREETS = "mapbox://styles/mapbox/streets-v12";
const STYLE_SATELLITE = "mapbox://styles/mapbox/satellite-streets-v12";

type MapBoxProps = {
  isSideBarCollapsed: boolean;
  locationFocus: LocationFocus | null;
};
type LocationFocus = { center: [number, number] | undefined; radiusKm: number | undefined };

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

export default function MapBox({ isSideBarCollapsed, locationFocus }: MapBoxProps) {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);

  const mapRef = useRef<mapboxgl.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const geoDataRef = useRef<any>(null);
  const popupRef = useRef<mapboxgl.Popup | null>(null);
  const prevStyleRef = useRef<string>(STYLE_SATELLITE);

  const [mapStyle, setMapStyle] = useState<string>(STYLE_SATELLITE);
  const [isMapLoaded, setIsMapLoaded] = useState(false);
  const [selectedParam, setSelectedParam] = useState<WeatherParam | undefined>();
  const prevParamRef = useRef<WeatherParam | undefined>(undefined);
  const prevDateRef = useRef<Date | undefined>(undefined);
  const paramDataRef = useRef<Record<string, SensorDataRow[]>>({});
  const prevLocationCenterRef = useRef<[number, number] | null>(null);

  const LOCATION_SOURCE_ID = "location-focus-source";
  const LOCATION_FILL_LAYER_ID = "location-focus-fill";
  const LOCATION_LINE_LAYER_ID = "location-focus-line";

  function makeCircleGeoJSON(center: [number, number] | undefined, radiusKm: number | undefined) {
    if (!center || !radiusKm) return null;
    // returns a Polygon feature
    return turf.circle(center, radiusKm, { steps: 64, units: "kilometers" });
  }
  const upsertLocationCircle = useCallback(() => {
    if (!mapRef.current || !isMapLoaded) return;

    const map = mapRef.current;

    // If no focus -> remove circle if it exists
    if (!locationFocus) {
      if (map.getLayer(LOCATION_FILL_LAYER_ID)) map.removeLayer(LOCATION_FILL_LAYER_ID);
      if (map.getLayer(LOCATION_LINE_LAYER_ID)) map.removeLayer(LOCATION_LINE_LAYER_ID);
      if (map.getSource(LOCATION_SOURCE_ID)) map.removeSource(LOCATION_SOURCE_ID);
      prevLocationCenterRef.current = null;
      return;
    }

    const { center, radiusKm } = locationFocus;

    const circleFeature = makeCircleGeoJSON(center, radiusKm);
    if (!circleFeature) return;
    const fc: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features: [circleFeature as any],
    };

    // Source
    const existing = map.getSource(LOCATION_SOURCE_ID) as mapboxgl.GeoJSONSource | undefined;
    if (!existing) {
      map.addSource(LOCATION_SOURCE_ID, {
        type: "geojson",
        data: fc as any,
      });
    } else {
      existing.setData(fc as any);
    }

    // Fill layer (below stations so stations stay visible)
    if (!map.getLayer(LOCATION_FILL_LAYER_ID)) {
      map.addLayer(
        {
          id: LOCATION_FILL_LAYER_ID,
          type: "fill",
          source: LOCATION_SOURCE_ID,
          paint: {
            "fill-color": "#3b82f6",
            "fill-opacity": 0.15,
          },
        },
        "unclustered-point"
      );
    }

    // Outline layer
    if (!map.getLayer(LOCATION_LINE_LAYER_ID)) {
      map.addLayer(
        {
          id: LOCATION_LINE_LAYER_ID,
          type: "line",
          source: LOCATION_SOURCE_ID,
          paint: {
            "line-color": "#3b82f6",
            "line-width": 2,
          },
        },
        "unclustered-point"
      );
    }

    // Only fly to location if CENTER changed (not just radius)
    if (center && radiusKm) {
      const centerChanged =
        !prevLocationCenterRef.current ||
        prevLocationCenterRef.current[0] !== center[0] ||
        prevLocationCenterRef.current[1] !== center[1];

      if (centerChanged) {
        const bbox = turf.bbox(circleFeature);
        const centerLng = (bbox[0] + bbox[2]) / 2;
        const centerLat = (bbox[1] + bbox[3]) / 2;

        const zoom = Math.max(8, Math.min(13, 14 - Math.log2(radiusKm)));

        map.flyTo({
          center: [centerLng, centerLat],
          zoom: zoom,
          essential: true,
          easing: (t) => 1 - Math.pow(1 - t, 2),
          maxZoom: 11,
          padding: { top: 80, bottom: 80, left: 300, right: 350 },
        });

        prevLocationCenterRef.current = center;
      }
    }
  }, [locationFocus, isMapLoaded]);

  useEffect(() => {
    upsertLocationCircle();
  }, [upsertLocationCircle]);

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
      const coordinates = e.feature.geometry.coordinates.slice();
      const props = e.feature.properties;

      // Close any existing popup before opening a new one
      if (popupRef.current) {
        popupRef.current.remove();
      }

      const popup = new mapboxgl.Popup({ offset: 15, maxWidth: "320px", closeOnClick: false })
        .setLngLat(coordinates)
        .setHTML(
          `
          <div class="station-popup" style="
            cursor: pointer;
            padding: 16px 18px;
            font-family: 'Source Sans Pro', -apple-system, sans-serif;
          ">
            <div style="
              display: flex;
              align-items: center;
              gap: 10px;
              margin-bottom: 14px;
              padding-bottom: 12px;
              border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            ">
              <div style="
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: linear-gradient(135deg, #00d9ff, #0066ff);
                box-shadow: 0 0 12px rgba(0, 217, 255, 0.5);
                animation: pulse 2s infinite;
              "></div>
              <h3 style="
                color: #fff;
                margin: 0;
                font-size: 16px;
                font-weight: 600;
                letter-spacing: 0.3px;
              ">${props?.name}</h3>
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 8px;">             
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: rgba(255, 255, 255, 0.5); font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Manufacturer</span>
                <span style="color: #fff; font-size: 13px; font-weight: 500;">${props?.manufacturer}</span>
              </div>
              
              ${
                props?.type
                  ? `
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: rgba(255, 255, 255, 0.5); font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Type</span>
                <span style="color: #fff; font-size: 13px; font-weight: 500;">${props.type}</span>
              </div>
              `
                  : ""
              }

              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: rgba(255, 255, 255, 0.5); font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">State</span>
                <span style="color: #fff; font-size: 13px; font-weight: 500;">${props?.state}</span>
              </div>
              
              <div style="
                display: flex;
                gap: 12px;
                margin-top: 6px;
                padding: 10px 12px;
                background: rgba(255, 255, 255, 0.04);
                border-radius: 8px;
              ">
                <div style="flex: 1;">
                  <div style="color: rgba(255, 255, 255, 0.4); font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px;">Longitude</div>
                  <div style="color: #00d9ff; font-size: 13px; font-weight: 600; font-family: 'SF Mono', monospace;">${coordinates[0].toFixed(4)}</div>
                </div>
                <div style="flex: 1;">
                  <div style="color: rgba(255, 255, 255, 0.4); font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px;">Latitude</div>
                  <div style="color: #00d9ff; font-size: 13px; font-weight: 600; font-family: 'SF Mono', monospace;">${coordinates[1].toFixed(4)}</div>
                </div>
              </div>
              
              ${
                props?.paramValue != null
                  ? `
              <div style="
                margin-top: 8px;
                padding: 12px;
                background: linear-gradient(135deg, rgba(0, 217, 255, 0.15), rgba(0, 102, 255, 0.1));
                border-radius: 8px;
                border: 1px solid rgba(0, 217, 255, 0.2);
              ">
                <div style="color: rgba(255, 255, 255, 0.5); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">${props.param?.toString()}</div>
                <div style="color: #fff; font-size: 22px; font-weight: 700;">${props.paramValue.toFixed(2)}</div>
              </div>
              `
                  : ""
              }
            </div>
            
            <style>
              @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.7; transform: scale(1.1); }
              }
            </style>
          </div>
        `
        )
        .addTo(mapRef.current);

      // Store popup reference for outside click handling
      popupRef.current = popup;

      // Clear ref when popup is closed
      popup.on("close", () => {
        popupRef.current = null;
      });

      const popupElement = popup
        .getElement()
        ?.querySelector(".station-popup") as HTMLDivElement | null;
      if (popupElement) {
        popupElement.addEventListener("click", () => {
          navigate(`/station/${props.id}`);
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
  const {
    data: geojson,
    isLoading,
  } = useQuery({
    queryKey: ["allStationsGeojson"],
    queryFn: () => getStationsGeojson(),
    enabled: true,
  });
  useEffect(() => {
    mapboxgl.accessToken = MAPBOX_TOKEN;

    if (!mapContainerRef.current) return;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: STYLE_SATELLITE,
      center: [9.25477, 34.26822],
      zoom: 1.5,
    });

    map.setPadding({ top: 0, bottom: 0, left: 0, right: 250 });
    mapRef.current = map;

    map.on("load", () => {
      setIsMapLoaded(true);
    });

    // Close popup when clicking on empty map area
    map.on("click", (e) => {
      if (!popupRef.current) return;

      // Check if click is on a station or cluster layer
      const features = map.queryRenderedFeatures(e.point, {
        layers: ["clusters", "unclustered-point", "station-param-points"],
      });

      // If not clicking on a feature, close the popup
      if (features.length === 0) {
        popupRef.current.remove();
        popupRef.current = null;
      }
    });

    return () => {
      map.remove();
    };
  }, []);

  // Close popup when clicking outside the map container
  useEffect(() => {
    const handleDocumentClick = (e: MouseEvent) => {
      if (!popupRef.current) return;

      const mapContainer = mapContainerRef.current;
      if (!mapContainer) return;

      // Check if click is outside the map container
      if (!mapContainer.contains(e.target as Node)) {
        popupRef.current.remove();
        popupRef.current = null;
      }
    };

    document.addEventListener("click", handleDocumentClick);
    return () => {
      document.removeEventListener("click", handleDocumentClick);
    };
  }, []);

  useEffect(() => {
    setLoading(!isMapLoaded || isLoading);

    if (!isMapLoaded) return;
    if (!geojson) return;
    if (!mapRef.current) return;

    geoDataRef.current = geojson;

    if (!mapRef.current.getSource("earthquakes")) {
      addStationLayers();
      addInteractions();
    }
  }, [isMapLoaded, geojson, isLoading]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const applyParamMode = useCallback(() => {
    if (!mapRef.current || !isMapLoaded) return;

    const map = mapRef.current;
    const requiredLayers = [
      "clusters",
      "cluster-count",
      "unclustered-point",
      "station-param-points",
    ];

    if (requiredLayers.some((layerId) => !map.getLayer(layerId))) return;

    switch (selectedParam !== undefined) {
      case true:
        map.setLayoutProperty("clusters", "visibility", "none");
        map.setLayoutProperty("cluster-count", "visibility", "none");
        map.setLayoutProperty("unclustered-point", "visibility", "none");

        map.setLayoutProperty("station-param-points", "visibility", "visible");
        map.setPaintProperty("station-param-points", "circle-color", getParamColorScale());
        map.flyTo({ center: [11.08813, 34.13523], zoom: 5.54 });
        break;
      case false:
        map.setLayoutProperty("clusters", "visibility", "visible");
        map.setLayoutProperty("cluster-count", "visibility", "visible");
        map.setLayoutProperty("unclustered-point", "visibility", "visible");

        map.setLayoutProperty("station-param-points", "visibility", "none");
        break;
    }
  }, [selectedParam, isMapLoaded, getParamColorScale]);

  useEffect(() => {
    if (!mapRef.current || !isMapLoaded) return;

    if (prevStyleRef.current === mapStyle) return;
    prevStyleRef.current = mapStyle;

    mapRef.current.once("style.load", () => {
      addStationLayers();
      applyParamMode();
      upsertLocationCircle();
    });

    mapRef.current.setStyle(mapStyle);
  }, [
    mapStyle,
    isMapLoaded,
    addStationLayers,
    addInteractions,
    applyParamMode,
    upsertLocationCircle,
  ]);

  useEffect(() => {
    applyParamMode();
  }, [applyParamMode, selectedParam]);

  const onSelectedParamChange = async (
    param: WeatherParam | undefined,
    dataOption: string | undefined,
    date: Date
  ) => {
    setLoading(true);
    if (!mapRef.current || !geoDataRef.current || !param || !dataOption) return;
    if (!param || !dataOption) {
      setSelectedParam(undefined);
      return;
    }

    const source = mapRef.current.getSource("stations-plain") as GeoJSONSource | undefined;
    if (!source) return;

    if (param !== prevParamRef.current || date !== prevDateRef.current) {
      paramDataRef.current = await getMapDataForParam(param, date);
      prevParamRef.current = param;
      prevDateRef.current = date;
    }

    const updatedGeoJson = {
      ...geoDataRef.current,
      features: geoDataRef.current.features.map((f: any) => {
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
    setLoading(false);
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

      <OverlayLoader show={loading} dim={0.2} blockInteraction={loading} />

      <div id="map-container" ref={mapContainerRef} />
    </Box>
  );
}

