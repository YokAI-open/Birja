import { useParams } from "react-router";

function TradePage() {
  const { symbol = "" } = useParams();
  return <h1>Trade {symbol.toUpperCase()}</h1>;
}

export default TradePage;
