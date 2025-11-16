import { useRef, useEffect } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import "./SCSS/MapBox.scss";

export default function MapBox() {
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    mapboxgl.accessToken =
      "pk.eyJ1IjoieWFzc2luZS1zYWhsaSIsImEiOiJjbWkwZHhlamMwaWgxMmxweWloOWJ3YmdtIn0.dJtTsXAcQy2eErlpsMoUWA";

    if (!mapContainerRef.current) return;

    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: "mapbox://styles/mapbox/standard",
      config: {
        basemap: {
          theme: "monochrome",
          lightPreset: "night",
        },
      },
      center: [-103.5917, 40.6699],
      zoom: 3,
    });
    mapRef.current.on("load", () => {
      if (!mapRef.current) return;
      mapRef.current.addSource("earthquakes", {
        type: "geojson",
        generateId: true,
        data: "https://docs.mapbox.com/mapbox-gl-js/assets/earthquakes.geojson",
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
          "circle-color": "#11b4da",
          "circle-radius": 4,
          "circle-stroke-width": 1,
          "circle-stroke-color": "#fff",
          "circle-emissive-strength": 1,
        },
      });

      // // When a click event occurs on a cluster,
      // // getClusterExpansionZoom grabs the zoomlevel where the cluster expands
      // // Then the viewport zooms in to show the expanded cluster
      // // Displaying the underlying individual points and/or smaller clusters
      // mapRef.current.addInteraction("click-clusters", {
      //   type: "click",
      //   target: { layerId: "clusters" },
      //   handler: (e) => {
      //     if (!mapRef.current) return;
      //     const features = mapRef.current.queryRenderedFeatures(e.point, {
      //       layers: ["clusters"],
      //     });
      //     if (features.length === 0 || !features[0].properties) return;
      //     const clusterId = features[0].properties.cluster_id;
      //     mapRef.current
      //       .getSource("earthquakes")
      //       .getClusterExpansionZoom(clusterId, (err, zoom) => {
      //         if (err) return;

      //         mapRef.current.easeTo({
      //           center: features[0].geometry.coordinates,
      //           zoom: zoom,
      //         });
      //       });
      //   },
      // });

      // // When a click event occurs on a feature in
      // // the unclustered-point layer, open a popup at
      // // the location of the feature, with
      // // description HTML from its properties.
      // mapRef.current.addInteraction("click-unclustered", {
      //   type: "click",
      //   target: { layerId: "unclustered-point" },
      //   handler: (e) => {
      //     const coordinates = e.feature.geometry.coordinates.slice();
      //     const mag = e.feature.properties.mag;
      //     const tsunami = e.feature.properties.tsunami === 1 ? "yes" : "no";

      //     new mapboxgl.Popup()
      //       .setLngLat(coordinates)
      //       .setHTML(`magnitude: ${mag}<br>Was there a tsunami?: ${tsunami}`)
      //       .addTo(mapRef.current);
      //   },
      // });

      // // Change the cursor to a pointer when the mouse is over a cluster of POIs.
      // mapRef.current.addInteraction("clustered-mouseenter", {
      //   type: "mouseenter",
      //   target: { layerId: "clusters" },
      //   handler: () => {
      //     mapRef.current.getCanvas().style.cursor = "pointer";
      //   },
      // });

      // // Change the cursor back to a pointer when it stops hovering over a cluster of POIs.
      // mapRef.current.addInteraction("clustered-mouseleave", {
      //   type: "mouseleave",
      //   target: { layerId: "clusters" },
      //   handler: () => {
      //     mapRef.current.getCanvas().style.cursor = "";
      //   },
      // });

      // // Change the cursor to a pointer when the mouse is over an individual POI.
      // mapRef.current.addInteraction("unclustered-mouseenter", {
      //   type: "mouseenter",
      //   target: { layerId: "unclustered-point" },
      //   handler: () => {
      //     mapRef.current.getCanvas().style.cursor = "pointer";
      //   },
      // });

      // // Change the cursor back to a pointer when it stops hovering over an individual POI.
      // mapRef.current.addInteraction("unclustered-mouseleave", {
      //   type: "mouseleave",
      //   target: { layerId: "unclustered-point" },
      //   handler: () => {
      //     mapRef.current.getCanvas().style.cursor = "";
      //   },
      // });
    });

    return () => mapRef.current.remove();
  }, []);

  return <div id="map-container" ref={mapContainerRef} />;
}
