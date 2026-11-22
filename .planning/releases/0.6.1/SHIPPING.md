# Software0.6.1 hotfix shipping

Production source a328007 (publishedv0.6.0) reached schema0023, then refused
final role validation. Backend and scheduler remain stopped. Original account,
holding and trade projections and portfolio associations compare unchanged.
Fresh exact0008 backups/restores succeeded before datastore transition and again
after role setup. Latest pre-migration snapshot:
7bc89128bb331074ac729fb114c9a3900ab016b37457d57eef1604b4b0cedb51.

Independent synthetic reproduction of released0008 grants plus untouched
migrations matches the live schema/ACL/default triple. See the debug report.
The local fix admits that exact ACL only with private defaults as a bootstrap
state; normal runtime admission and canonical final grants remain unchanged.
No schema or dependency upgrade, financial write or stock activation is included.

First-party version0.6.1 metadata and its audit bindings are updated. Explicit
parsed Python/Node comparisons prove identical third-party graphs. The issue35
scope and2026-12-17UTC expiry remain unchanged. Production repair, publication
and final CI are pending; do not claim a deployment success.

## Local verification

Focused real PostgreSQL reproduction/normalization/refusal checks pass2cases
in18.24s. Independent bounded review reports0blockers/0warnings. CI contracts
111/111, offline image contracts17/17 and frontend audit contracts12/12 pass.
Ruff/format, Bash syntax, diff and offline83-package lock validation pass.
All79 affected PostgreSQL cases pass507.63s, including both legacy14 default
variants and the existing management/grant cases. The owned test stack and
network are removed. Required hosted full CI remains pending. No production repair or hotfix publication yet.
