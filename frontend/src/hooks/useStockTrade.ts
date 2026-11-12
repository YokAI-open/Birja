import { useState } from "react";

export function useStockTrade(_symbol: string) {
  const [quantity, setQuantity] = useState("");
  return {
    phase: "draft", quantity, setQuantity,
    preview: async () => {}, confirm: async () => {}, checkResult: async () => {},
  };
}
