import { afterEach, expect, it, vi } from "vitest";
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useStockTrade } from "./useStockTrade";
import { contextFixture, fillFixture, quoteFixture } from "@/test/stockTradeFixtures";

const clients:QueryClient[]=[];
function setup(){
  const client=new QueryClient({defaultOptions:{queries:{retry:false,gcTime:Infinity}}});
  clients.push(client);client.setQueryData(["me"],{email:"first@example.test",cash_usd:"10000"});
  const wrapper=({children}:{children:ReactNode})=><QueryClientProvider client={client}>{children}</QueryClientProvider>;
  return {client,...renderHook(()=>useStockTrade("AAPL"),{wrapper})};
}
afterEach(()=>{cleanup();clients.forEach(c=>c.clear());clients.length=0;vi.restoreAllMocks();vi.unstubAllGlobals();vi.useRealTimers();document.cookie="bj_csrf=; Max-Age=0; path=/";});

it("keeps one frozen attempt after response loss and resolves it explicitly after market closure",async()=>{
  document.cookie="bj_csrf=test; path=/";
  const bodies:unknown[]=[];
  vi.stubGlobal("fetch",vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{
    const path=String(input);
    if(path.endsWith("/context"))return new Response(JSON.stringify(contextFixture()));
    if(path.endsWith("/quote"))return new Response(JSON.stringify(quoteFixture()));
    bodies.push(JSON.parse(init!.body as string));
    if(bodies.length===1)throw new Error("response lost");
    return new Response(JSON.stringify(fillFixture()));
  }));
  const {client,result}=setup();
  act(()=>result.current.setQuantity("2"));
  await act(async()=>{await result.current.preview();});
  await waitFor(()=>expect(result.current.phase).toBe("preview"));
  await act(async()=>{await result.current.confirm();});
  expect(result.current.phase).toBe("unknown");
  const closed=contextFixture();closed.execution_enabled=false;closed.execution_reason="market_closed";
  closed.valid_until=null;closed.quote=null;closed.buy_max_quantity="0";closed.session.state="closed";
  act(()=>client.setQueryData(["stockContext","first@example.test","AAPL"],{
    ...closed,transport:{started_at:performance.now(),received_at:performance.now(),round_trip_ms:0},
  }));
  act(()=>result.current.setQuantity("3"));
  expect(result.current.quantity).toBe("2");
  await act(async()=>{await result.current.checkResult();});
  expect(result.current.phase).toBe("filled");
  expect(bodies).toHaveLength(2);expect(bodies[1]).toEqual(bodies[0]);
});
