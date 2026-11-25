---
status: incomplete
---

# Activate simulated US stock trading

1. Verify that the configured Alpaca account can retrieve IEX quotes and
   corporate actions. Determine how Birja can establish each stock's current
   trading status at startup and recover it after a disconnect. The owner
   chose to proceed using documented sources without contacting Alpaca.
2. Verify that the existing scheduler can persist live IEX quotes and that
   Markets can display them in isolated PostgreSQL and Redis. Keep the
   existing action and calendar checks in the test.
3. Once a supported status source is identified, connect it to the scheduler.
   Verify startup, reconnect, halt, resume, stale input and disconnect. Prove
   an in-session simulated buy and sell through Birja's API, with verified
   stock data and isolated balances and holdings.
4. Use the existing [production admission procedure](../../../deploy/STOCK-DATA-ADMISSION.md)
   for the actual account and data products. Verify the release candidate
   before enabling production collection or execution.
