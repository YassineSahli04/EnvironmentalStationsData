import { useRef, useEffect } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { getStationsGeojson } from "../ApiService/Api";
import "./SCSS/MapBox.scss";

export default function MapBox() {
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (mapRef.current) {
      setTimeout(() => {
        mapRef.current?.resize();
      }, 500);
    }
  }, [mapContainerRef]);

  useEffect(() => {
    mapboxgl.accessToken =
      "pk.eyJ1IjoieWFzc2luZS1zYWhsaSIsImEiOiJjbWkwZHhlamMwaWgxMmxweWloOWJ3YmdtIn0.dJtTsXAcQy2eErlpsMoUWA";

    if (!mapContainerRef.current) return;

    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: "mapbox://styles/mapbox/satellite-streets-v12",
      center: [9.25477, 34.26822],
      zoom: 1.5,
    });

    mapRef.current.on("load", async () => {
      const data = await getStationsGeojson();

      if (!mapRef.current) return;
      mapRef.current.addSource("earthquakes", {
        type: "geojson",
        generateId: true,
        data: data,
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
          "circle-color": ["step", ["get", "point_count"], "#51bbd6", 5, "#f1f075", 10, "#f28cb1"],
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
          "circle-radius": 4,
          "circle-stroke-width": 1,
          "circle-stroke-color": "#fff",
          "circle-emissive-strength": 1,
        },
      });

      // When a click event occurs on a cluster,
      // getClusterExpansionZoom grabs the zoomlevel where the cluster expands
      // Then the viewport zooms in to show the expanded cluster
      // Displaying the underlying individual points and/or smaller clusters
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
          mapRef.current
            .getSource("earthquakes")
            .getClusterExpansionZoom(clusterId, (err, zoom) => {
              if (err) return;

              mapRef.current.easeTo({
                center: features[0].geometry.coordinates,
                zoom: zoom,
              });
            });
        },
      });

      // When a click event occurs on a feature in
      // the unclustered-point layer, open a popup at
      // the location of the feature, with
      // description HTML from its properties.
      mapRef.current.addInteraction("click-unclustered", {
        type: "click",
        target: { layerId: "unclustered-point" },
        handler: (e) => {
          const coordinates = e.feature.geometry.coordinates.slice();

          const popup = new mapboxgl.Popup()
            .setLngLat(coordinates)
            .setHTML(
              `
              <div class="station-popup" style="cursor: pointer;">
                <h3 style="color: #2238ffff; margin: 0; ">${e.feature.properties.name}</h3>
                <p style="color: #000000ff; margin: 4px 0 0 0;">
                  <strong style="color:#000000ff;">ID:</strong> ${e.feature.properties.id}<br />
                  <strong style="color:#000000ff;">Manuf:</strong> ${e.feature.properties.manufacturer}<br />
                  ${
                    e.feature.properties.type
                      ? `<strong style="color:#000000ff;">Type:</strong> ${e.feature.properties.type}<br />`
                      : ""
                  }
                  <strong style="color:#000000ff;">Lon:</strong> ${e.feature.geometry.coordinates[0].toFixed(
                    4
                  )}, <strong style="color:#000000ff;">Lat:</strong> ${e.feature.geometry.coordinates[1].toFixed(4)}
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
              console.log(`Station ID: ${e.feature.properties.name}`);
            });
          }
        },
      });

      // Change the cursor to a pointer when the mouse is over a cluster of POIs.
      mapRef.current.addInteraction("clustered-mouseenter", {
        type: "mouseenter",
        target: { layerId: "clusters" },
        handler: () => {
          mapRef.current.getCanvas().style.cursor = "pointer";
        },
      });

      // Change the cursor back to a pointer when it stops hovering over a cluster of POIs.
      mapRef.current.addInteraction("clustered-mouseleave", {
        type: "mouseleave",
        target: { layerId: "clusters" },
        handler: () => {
          mapRef.current.getCanvas().style.cursor = "";
        },
      });

      // Change the cursor to a pointer when the mouse is over an individual POI.
      mapRef.current.addInteraction("unclustered-mouseenter", {
        type: "mouseenter",
        target: { layerId: "unclustered-point" },
        handler: () => {
          mapRef.current.getCanvas().style.cursor = "pointer";
        },
      });

      // Change the cursor back to a pointer when it stops hovering over an individual POI.
      mapRef.current.addInteraction("unclustered-mouseleave", {
        type: "mouseleave",
        target: { layerId: "unclustered-point" },
        handler: () => {
          mapRef.current.getCanvas().style.cursor = "";
        },
      });
    });
    return () => mapRef.current.remove();
  }, []);

  return <div id="map-container" ref={mapContainerRef} />;
}
