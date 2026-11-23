# Phase 17 Context

**Goal:** Qualify the redesigned Birja release candidate with the real app stack.

Phase 17 starts after Phase 16 UI and integrated acceptance. The Phase 16 UI
contract remains the design authority. Changes in this phase address demonstrated
defects in approved flows. Existing security, provider and rollout boundaries apply.

Use the same committed source for the final combined browser run and the
candidate. Record source and test inputs when reusing unchanged backend checks.
The standard CI gates apply before merge, with separate owner approval for
publishing, merging and production operations.
