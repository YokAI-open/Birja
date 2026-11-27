import { createContext } from "react";

/** Undefined is standalone rendering. Null is a managed toolbar awaiting its DOM slot. */
export const PortfolioToolbarSlot = createContext<HTMLDivElement | null | undefined>(undefined);
