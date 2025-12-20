# Contracts

This directory contains schemas used by repoLens.

## Snapshot Schemas (Fleet / Organism)

**Note:** Snapshot schemas (`fleet.snapshot.schema.json`, `organism.index.snapshot.schema.json`) are **not** hosted here.

They are authoritative in the `metarepo` and are expected to be present in the Hub at:
- `.../metarepo/contracts/fleet/fleet.snapshot.schema.json`
- `.../metarepo/contracts/organism/organism.index.snapshot.schema.json`

repoLens code generates snapshots compliant with these schemas but does not maintain a local copy to avoid drift.

## Sync Reports

`sync.report.schema.json` is currently maintained here as the contract for `repoLens`'s own sync output.
