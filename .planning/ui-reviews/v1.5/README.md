# v1.5 approved design reference

The owner approved this interactive prototype on 2026-11-26 and requested
a GSD milestone for its interface and features.

Extract [PROTOTYPE.zip](PROTOTYPE.zip) and open `birja-ui-prototype/index.html`.
It includes Markets, portfolio overview, selected portfolio, History, trade,
and sign-in. SHA-256:
`5e361ad60eb0915add082791fd4a8bc2862ec607712b04e00a15d2c53f2b143e`.

The prototype defines the layout, hierarchy, interaction patterns and empty
space. It uses demo prices, curves, fills, countdowns, browser storage, and
a fixed sign-in code. The React implementation uses the current authenticated
APIs, authoritative trading rules, actual market calendars, and new
chart-data contracts. Preserve working capabilities outside the demo, including
crypto orders by dollar amount, exact receipt recovery and paginated History.

Match the approved design on desktop and mobile. Use the existing Birja logo,
warm palette, Inter, one portfolio combobox, and controls that serve a clear
purpose. The real-data versions of the chart and closed-market state need
screenshots from the integrated application to verify the result.
