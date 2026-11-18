import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import PortfoliosPage from "./PortfoliosPage";
import { usePortfolioOverview } from "@/hooks/usePortfolioOverview";
import { usePortfolioManagement } from "@/hooks/usePortfolioManagement";
import { cashPortfolio } from "@/test/portfolioFixtures";
vi.mock("@/hooks/usePortfolioOverview");
vi.mock("@/hooks/usePortfolioManagement");
const refetch=vi.fn();
function show(data: unknown, extra={}) {
  vi.mocked(usePortfolioOverview).mockReturnValue({data, isPending:false,isError:false,isFetching:false,refetch,...extra} as ReturnType<typeof usePortfolioOverview>);
  vi.mocked(usePortfolioManagement).mockReturnValue({ready:true,creation:{phase:"editing",attempt:null,error:null}} as ReturnType<typeof usePortfolioManagement>);
  return render(<MemoryRouter><PortfoliosPage /></MemoryRouter>);
}
afterEach(()=>{cleanup();vi.clearAllMocks();});
it("shows genuine zero-book empty state and restores create trigger focus",()=>{
  show([]);
  expect(screen.getByText("No portfolios yet")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button",{name:"Create portfolio"}));
  fireEvent.click(screen.getByRole("button",{name:"Discard draft"}));
  expect(screen.getByRole("button",{name:"Create portfolio"})).toHaveFocus();
});
it("renders exact server values, stored baseline, incomplete return and source times",()=>{
  show([{...cashPortfolio(),id:"2",name:"<script>safe</script>",description:"Line\nTwo"}, {...cashPortfolio(),id:"10",name:"Unpriced",description:"",valuation_complete:false,total_value:null,total_pl:null,total_pl_percent:null,known_value:"9000.12000000",unvalued_holding_count:1}]);
  expect(screen.getByText("<script>safe</script>")).toBeInTheDocument();
  expect(document.querySelector("script")).toBeNull();
  expect(screen.getByText(/Known value: \$9,000.12/)).toBeInTheDocument();
  expect(screen.getByText("Return unavailable")).toBeInTheDocument();
  expect(screen.getAllByText(/Calculated at/)).toHaveLength(2);
  expect(screen.getAllByRole("link",{name:"Open portfolio"}).map(a=>a.getAttribute("href"))).toEqual(["/portfolios/2","/portfolios/10"]);
});
it("distinguishes loading, initial error and failed refresh without hiding permitted rows",()=>{
  const view=show(undefined,{isPending:true});
  expect(screen.getByRole("status")).toHaveTextContent("Loading portfolios");
  view.unmount();show(undefined,{isError:true});
  expect(screen.getByRole("alert")).toHaveTextContent("Can't load your portfolios");
});
it("keeps permitted data after refresh failure and offers retry",()=>{
  show([{...cashPortfolio(),id:"1",description:""}],{isError:true});
  expect(screen.getByRole("alert")).toHaveTextContent("Couldn't refresh");
  fireEvent.click(screen.getByRole("button",{name:"Retry refresh"}));
  expect(refetch).toHaveBeenCalled();
});
it("shows ten books and the visible cap reason",()=>{
  show(Array.from({length:10},(_,i)=>({...cashPortfolio(),id:String(i+1),name:`Book ${i+1}`,description:""})));
  expect(screen.getByText("10 of 10 active portfolios")).toBeInTheDocument();
  expect(screen.getByRole("button",{name:"Create portfolio"})).toBeDisabled();
  expect(screen.getByText(/You have 10 active portfolios/)).toBeInTheDocument();
});
