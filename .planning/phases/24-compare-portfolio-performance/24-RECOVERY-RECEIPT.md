# Phase 24 recovery receipt

All seven stages of the isolated encrypted recovery campaign passed on
November 26, 2026. The receipt verifier accepted the same tested commit,
archive and runtime image records. The separate preflight passed 148 fixture
tests and verified the local tools, including Restic 0.19.1.

## Tested source and artifacts

| Evidence | Exact identity |
|---|---|
| Tested commit | `74e852d7124b89bdbc5490af04e35118f0f88f62` |
| Tested Git tree | `2b3add74bb591072cf0315b17948d6b7797c64c1` |
| Candidate backend app tree | `1c82452c9746c8617262ccd2ab4c81eee9bb62ae` |
| Candidate backend context SHA-256 | `a6981723438a5a586019a3017739bdedd76d9a5a3aaf634487fea182c270cb97` |
| Recovery contract | `deploy-recovery-v9`, payload `8`, schema `0028` |
| Recovery tooling archive | `/tmp/birja-backup-test-phase24-proof/recovery.tar.gz` |
| Recovery archive SHA-256 | `ecbb73237caf9e02b6d7678f1873e09e0e90b83b1d26ef8bf534880bfe1d7046` |
| Authenticated `status.json` SHA-256 | `1a98aef2aa50e31197b94d05c5afce4a12cc4b9bf47552f8b9eb4d2aff0bc97b` |
| Archived canonical manifest SQL SHA-256 | `65548801a5c5b563493e6f26ee77acf47d8806e7a844d87b8d82de34c150442c` |
| Archived backup producer SHA-256 | `39ea67bf98091482e5dc2a2f89898aec9e05ec11c57e0b9ee0de1014d8deaec8` |
| Archived restore verifier SHA-256 | `5961b28f273c3d2526805a7b757c1f110808ab99f53c7662d9e3540881f1410c` |
| Restic 0.19.1 SHA-256 | `20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639` |
| Selected recovery PostgreSQL engine image | `sha256:42c334e9e4d30cf6f99ac6bbc411910d020b02dfb693604887e9cdc9188e3a48` |
| Recovery PostgreSQL OCI config digest | `sha256:4ee05252904571f8901ceb47916108d7da51fc6ecc3edbfa4a161b8b9225051e` |
| Candidate 0028 application image | `sha256:c8ea48cbb2e9b50a17c24654e6dd18e835efa459d79eccccaabf6898115219b6` |
| Candidate image config / root filesystem SHA-256 | `6f17ca541be6bdfad6476515b263e9a62472cf0ae85354f1b0978db977149b61` / `fb4c80c5ce1a46e733a9b9507e0bf7d6a334810acf24e57dfde9680f16aa2157` |
| Candidate image binding SHA-256 | `2409560bfc21035a3be8ede32b4628abdc575e0148823aa2a6f1fa4a0b68c644` |
| Retained 0027 source | v0.8.1 `0c26810fb0bcb15323705a38aae63b531d69b992` |
| Retained 0027 app tree / source archive SHA-256 | `6f4fca6bb9f5915b783c71132db15a5b89c1e485` / `c97958efd402c26a4e81452bda8019c066d977625ff12e5507dcf1d1fa3f9daf` |
| Retained 0027 application image | `sha256:6fe2177fd6884f433702cc7a166b3899c2fa740fcb035dba1a7a77d50a0b5d1e` |
| Retained image config / root filesystem SHA-256 | `824976517cb371078c54792759028446de46fff161ddc9f96995ea22245b73d0` / `077021256737501ca04ba5f3d424dd941fb00f95d36e2d3ed8cd42e8f4a0fae5` |
| Retained image binding SHA-256 recorded in receipt | `d1a752f78cfc6a0d34ca349a10a30c262816ef967c21084035ac3e40d8a73ead` |

## Measured stages

| Stage | Result |
|---|---|
| `image-transition` | Authenticated. PostgreSQL collation/index and Redis clone/restart checks passed with the original data preserved. |
| `retained-roundtrip` | Authenticated. Installed recovery tooling restored the retained SQL, stock, dividend and portfolio evidence. Restricted clients replayed the saved receipts. |
| `current0028-cold` | Authenticated. The populated 0027 book and original sequences survived the upgrade, with empty daily history before capture. The encrypted 0028 snapshot restored to fresh PostgreSQL with exact data and identity state. |
| `roles` | Authenticated. Existing role, lock and grant checks passed, followed by restricted 0028 verified-TLS role checks. |
| `tls-upgraded` | Authenticated. The populated 0027-to-0028 path measured the same 0028 authority as the cold restore. |
| `tls-fresh` | Authenticated. A fresh 0028 database measured the same authority as cold and upgraded. |
| `selected-rollback` | Authenticated. The qualified 0027 original restarted before any candidate writer. After capture, the same 0028 candidate volume restarted with exact data, receipts and restored owner history, and the 0027 application refused 0028. |

The controlled capture recorded four observations with original starting cash
of `10000.00000000` each. The owner had a complete `10251.00` observation,
an incomplete observation with a database null total, and a `10000.00`
observation captured while a portfolio was active and preserved after actual
closure. A separate owner had the fourth complete `10000.00` observation.
The retry after a price change preserved the first value. A later capture
of the closed portfolio was refused. Canonical rows, the daily identity
sequence and the retained terminal row matched the restored evidence.

Both authenticated owners replayed the private history API after recovery
and candidate restart. Their responses contained only their own active
portfolios. The restored test also replayed stock buy/sell, dividend,
correction and split receipts. Redis quote data stayed outside the backup.
Cold, upgraded and fresh PostgreSQL checks agreed on the exact 0028
catalogue, ACL and default fingerprints.

| 0028 authority check | SHA-256 |
|---|---|
| Canonical schema | `d9a4ee43bdb6fa96891dd087a32131510ceb596548a6947b28c15fd699a7dc0b` |
| Granted authority | `00e3ccb0993ae129c28969c11063ec6a5a72c29a73eba383f05ca38da03cd3bd` |
| Normalized restore quarantine | `56f9f871fbd03561e84a51a64274c6f1b5cd3daef3ab8d3ce5a1d5ae3e518c47` |
| Catalogue | `0484dd48782c9f215d1dea18fd767ae22f1b3ac558559c39837c9eef783fea25` |
| ACL | `2faedb917aa58062f5af23449fecb6d699f3580e14d0b69e1ae1c964d2a1eb0b` |
| Private defaults | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |

## Commands and timing

```bash
python3 deploy/tests/run-portfolio-validation.py --phase 24 --suite recovery-successor --preflight
python3 deploy/tests/run-portfolio-validation.py --phase 24 --suite recovery-successor
python3 deploy/tests/run-portfolio-validation.py --phase 24 --suite recovery-successor --verify-successor-receipt 74e852d7124b89bdbc5490af04e35118f0f88f62
```

The serial run took 56 minutes 19 seconds on the local host. Receipt
verification took about 5 seconds. The separate serial step in hosted CI
has a 45-minute limit. Its timing remains unmeasured. The local pass covers
recovery correctness and leaves hosted CI confirmation open.

The serial log is `/tmp/birja-phase24-serial-74e852d.log` with SHA-256
`e66d8913dedf55e7cbcaf7fe9db342722d5424a07f8d7b3af90416d0b432dd02`.
The verifier log is `/tmp/birja-phase24-verify-74e852d.log` with SHA-256
`04ce7b1a450c739d4bbb58a7e96588f25c3d75c3980ed976127990769e871233`.
