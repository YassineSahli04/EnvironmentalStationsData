import { useRef, useEffect } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

export default function MapBox() {
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    mapboxgl.accessToken =
      "pk.eyJ1IjoieWFzc2luZS1zYWhsaSIsImEiOiJjbWh6dzdwcnEwdHlpMmpwdG5kZ3AyYzk4In0.vsvUv8pZJGyqR81b17vNKg";

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

  return <div id="map-container" ref={mapContainerRef} />;
}
