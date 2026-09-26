# Solana Ecosystem Pulse

A zero-key, Python-stdlib report generator for the current state of Solana. One command collects public RPC + market/ecosystem data and emits the three formats requested by the Superteam Canada bounty:

- `output/dashboard.html` — interactive, responsive dark-theme dashboard
- `output/report.md` — human-readable briefing
- `output/report.json` — structured machine-readable snapshot

## Why this architecture

The design optimizes for **low maintenance and graceful degradation**. Each source runs independently; one failing source is recorded in `meta.errors` while the remaining reports are still generated. Missing values stay `null`/`n/a` rather than being guessed.

### Data sources

| Area | Source | Key required? | Metrics |
|---|---|---:|---|
| Network | Solana JSON-RPC | No | slot, block height, epoch, TPS, slot time, supply, inflation |
| Validators | Solana JSON-RPC `getVoteAccounts` | No | active/delinquent counts, stake concentration, top validators, commission |
| DeFi | DeFiLlama public API | No | TVL, 30-day TVL series, DEX volume, stablecoin supply |
| Market | CoinGecko public API | No | SOL USD price, 24h move, market cap |
| Development | GitHub public API | No | Agave releases + recent SIMD development activity |
| Ecosystem news | Official Solana RSS | No | latest official ecosystem/developer/upgrade stories |

No paid API key is required. `SOLANA_RPC_URL` can override the public RPC endpoint if an operator wants a dedicated endpoint later.

## Run

```bash
python src/solana_pulse.py --once
```

Outputs land in `output/`. Continuous local refresh:

```bash
python src/solana_pulse.py --watch
```

Edit `refresh_seconds` and anomaly thresholds in `config.json`.

## Test

```bash
python -m unittest discover -s tests -v
```

For a deterministic end-to-end render without network access:

```bash
python src/solana_pulse.py --fixture tests/fixture.json --out output/sample
```

Fixture-generated reports identify themselves as **TEST FIXTURE**. They are never represented as current chain data.

## Automation

`.github/workflows/update.yml` runs hourly, regenerates the three outputs, runs the tests, and commits only when report output changed. A static host such as GitHub Pages can serve `output/dashboard.html` without an application server.

## Anomaly detection

Configurable lightweight rules currently flag:

- TPS below a floor
- slow average slot time
- elevated validator delinquency
- large absolute SOL 24h move
- large absolute TVL 7d move

The JSON output preserves anomaly level, metric, message, and observed value, making it easy to plug into alerts later without changing collectors.

## Coverage and deliberate gaps

The bounty asks for broad coverage, including tokenized equities volume, daily active addresses, REV, and median transaction fees. This implementation prioritizes metrics that are reproducible from public, keyless endpoints. Metrics without a stable canonical no-key endpoint remain explicit extension points rather than being approximated or scraped unreliably.

High-value next adapters:

1. Solana transaction-fee sampler for median fees / REV proxy
2. stable public active-address source or direct indexed calculation
3. tokenized-equity volume adapter from a canonical public endpoint
4. curated RSS/news adapter with per-item source links
5. validator-history enrichment through Jito StakeNet

## Reproducibility / source health

Every generated JSON includes:

- generation timestamp
- per-source `ok`/`error` state
- safe error text
- explicit nulls for unavailable metrics
- fixture flag

This makes stale or partially broken reports visible instead of silently misleading.

## Security / operational notes

- No secrets are stored.
- No wallet, signing, or transaction actions are performed.
- Network requests are read-only.
- This dashboard is informational, not financial advice.
