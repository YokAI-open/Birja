import type { StockFill } from "@/api/stockTrades";
export function StockTradeReceipt({ fill, onTradeAgain }: { fill: StockFill; onTradeAgain: () => void }) { void fill; void onTradeAgain; return <h2>Receipt</h2>; }
