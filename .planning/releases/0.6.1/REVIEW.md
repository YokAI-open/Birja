# Bounded hotfix review

Independent GSD debug session manager reviewed the complete changed bootstrap,
administrator SQL, current recovery/deploy source bindings, regression test,
first-party metadata and audit policy. Result:0blockers,0warnings.

The exact inherited0008 ACL is admitted only with private defaults during
explicit bootstrap. Runtime admission still separately requires canonical71896…
permissions; catalogue59aeeee… and final private defaults stay unchanged. Existing
normalization resets the redundant historical column permissions. Qualified0017/
0020 literals and all grant procedures remain byte-identical. Current producer/
consumer pins and deploy source binding match actual files. Dependency graphs
are unchanged; the existing issue35 scope/expiry is unchanged.

The new genuine PostgreSQL test independently reconstructs the missing state
from released0008 grants and unchanged migrations. Both actual normalizers run
twice and compare original finances, owner associations and six identity tails.
Extra/missing permissions and mismatched defaults refuse on both surfaces without
mutation. Original RED results and final GREEN2cases/18.24s are retained in the
debug report. This review did not conduct an unrelated hardening sweep.

## Reviewed source bindings

- backend/app/db/portfolio_bootstrap.py: 15d84249e11bad99c8e259c54680fdc5303e6771c63b501c71f79601ab0bc071
- deploy/db/bootstrap-roles.sql: d8010e470c14cc397f29ae86eb55c1e8918fa39751083c8fa7435a8105c58265
- deploy/backup-snapshot.py: 8c90b7f79eb244dedeeed1a21c492c6a49b4f4ecec9ce2ba045ba0e4d54e4412
- deploy/verify-restore.py: 60432949e65238517dfa2baaa0f19683b151c65adb5f37ec2724bb8dda79a968
- deploy/deploy.sh: d782db4942692cf740bc8e3c775c7a5e83cbc24512a4d22e7f14468411e108c4
