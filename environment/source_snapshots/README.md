# Exact installation-source snapshots

These archives contain the software/build files recorded in `../sources.json`, including the
recorded RouteInspector working-tree GUI edit. They are deterministic tar/gzip
archives (fixed timestamps, ownership, modes, and order) with archive hashes in
`manifest.json`. Setup also verifies the complete file sets and individual hashes.

| Project | Recorded Git revision | Files | Compressed bytes |
| --- | --- | ---: | ---: |
| SynPlanner | `53ffed21794e829cd660b63effaaf4351e10cf95` | 200 | 504,012 |
| RouteInspector | `f38f668a185801c37780f94db78fd76af1d4a122` | 372 | 986,935 |

Both upstream MIT licenses are preserved as `LICENSE` inside their respective
archives. Sources: [SynPlanner](https://github.com/Laboratoire-de-Chemoinformatique/SynPlanner)
and [RouteInspector](https://github.com/Laboratoire-de-Chemoinformatique/route-inspector).
The file-level manifest, rather than the Git revision alone, defines each snapshot.

Run `python3.12 scripts/setup_environment.py --verify-only` from the project root
for an offline integrity check. Full installation also downloads pinned package
dependencies. See `docs/MOBILITY.md` for reconstruction and platform limitations.

Two generated GUI TLS files under `route_inspector/outputs/gui/tls/` are
excluded: `server.key` and `server.crt`. Their names and original hashes are
recorded in `manifest.json`, with both the original inventory digest and the
portable content digest. No source code is changed by this exclusion.
