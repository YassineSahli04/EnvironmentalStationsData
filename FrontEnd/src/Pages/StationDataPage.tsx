import { useParams } from "react-router-dom";

export default function StationDataPage() {
  const { stationId } = useParams<{ stationId: string }>();
  return (
    <div style={{ backgroundColor: "#ee1111ff" }}>
      <h1>Hello, this is station {stationId}</h1>
    </div>
  );
}
