# Phase 16 Code Review

**Status:** Independent findings addressed. Owner UI and native 200% checks passed.
The complete integration run is tracked separately.

| Severity | Finding | Disposition |
|---|---|---|
| Blocking | Selected stock on mobile omitted the reason trading is unavailable. | Display the applicable stock restriction and keep the existing quote, permission and action checks. |
| Blocking | Opening the portfolio editor from the keyboard disabled the trigger and left focus outside the form. | Focus the editor on open and retain focus restoration to Edit. |
| Warning | Focus on the OTP and other shared inputs could be difficult to see. | Use the existing focus ring styles directly on shared inputs. |
| Warning | Portfolio History selector opened the other portfolio's detail. | Switch to the selected portfolio's History route with a specific accessible label. |
| Warning | Holdings lost the exact recorded cost, price and allocation display. | Keep each card compact and provide a collapsed Cost and price disclosure. |
| Warning | Cards with dated closed/halted stock marks looked current. | Add compact conditional dated-price copy and retain the source timestamp. |
| Warning | Portfolio subroutes did not indicate the active navigation destination. | Keep Portfolios active on its subroutes and History active on scoped History. |
| Warning | Stock catalogue tests counted the selected asset's CTA along with the catalogue's links. | Scope exact link counts to the catalogue and test the selected pane separately. |

The scope was the application and affected tests. Backend source, schema,
dependency locks and live-provider configuration match the released base.


After the independent re-review, the unavailable-History chooser was aligned
with the scoped History route, and the holding disclosure gained the exact
fresh price timestamp. The current phone and desktop layouts were
then checked at 320, 375, 768 and 1280 CSS pixels with normal-size header,
long stock name and 200%-sized History text checks. The real-backend focused
suite passed all 11 cases on matching source inputs. Frontend lint, format,
build and all 1,332 unit tests passed.
