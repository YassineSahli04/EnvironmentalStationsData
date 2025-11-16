import MapBox from "../Components/MapBox";

type HomeProps = {
  isSideBarCollapsed: boolean;
};

export default function Home({ isSideBarCollapsed }) {
  return (
    <>
      <MapBox />
    </>
  );
}
