# Phase 14 — Integration Handoffs

## Plan07: retained creation API fixture (Plan15 owner)

`backend/tests/test_portfolio_creation.py::management_api` imports the retained
`test_portfolio_management_authority.authority`, which explicitly creates0020
and applies the historical generic `GRANTS_SQL`. The current application now
correctly admits0023 only. A combined Plan07 regression command passed50
current/transport cases, then failed this older fixture's lifespan with
`SchemaAdmissionError: incompatible_schema` before its first test body.
Receipt: `/tmp/birja-phase14-plan07/final-affected2.log` (87.13s).

This is the broader current-versus-retained fixture adaptation already assigned
to Plan15; it is not a reason to broaden current runtime admission or overlay
current code on fixed0020 recovery. Plan15 must give current API creation tests
an explicit current0023 fixture (with genuine public deletion where applicable),
while retaining actual historical0020 authority/source tests separately. It
must also replace privileged historical `close()` shortcuts when used against
the new lifecycle schema. Full phase qualification remains blocked until that
planned adaptation and required whole gates pass. Plan07 does not claim that
the legacy creation API test file passed.
