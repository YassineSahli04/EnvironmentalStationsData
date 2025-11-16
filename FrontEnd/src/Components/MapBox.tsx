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
      center: [-74.0242, 40.6941],
      zoom: 10.12,
    });

    return () => {
      mapRef.current?.remove();
    };
  }, []);

  // useEffect(() => {
  //   if (!mapRef.current || !mapContainerRef.current) return;

  //   const observer = new ResizeObserver(() => {
  //     mapRef.current?.resize();
  //   });

  //   observer.observe(mapContainerRef.current);

  //   return () => observer.disconnect();
  // }, []);

  return <div id="map-container" ref={mapContainerRef} />;
}
