# Submission package — Solana Ecosystem Pulse

## Elevator pitch

Solana Ecosystem Pulse is a zero-key, stdlib-only intelligence pipeline that turns public Solana RPC, DeFiLlama, CoinGecko, and GitHub data into an automatically refreshed dark dashboard, Markdown briefing, and structured JSON snapshot. It fails visibly instead of silently when a source is unavailable and ships configurable anomaly detection for network, validator, TVL, and market conditions.

## Bounty alignment

- Comprehensive collection: network, validators, price, TVL, DEX volume, stablecoins, supply/inflation, development activity.
- Automation: one command locally, hourly GitHub Actions workflow included.
- Output formats: HTML + Markdown + JSON.
- UX: responsive dark dashboard with KPI cards, TVL chart, validator table, source-health panel, anomaly radar.
- No API keys: all default sources are public/keyless.
- Maintainability: isolated collectors, explicit source status/errors, no third-party Python packages.
- Innovation: source-health transparency + graceful degradation + machine-readable anomaly objects.

## Demo flow

1. Run `python src/solana_pulse.py --once`.
2. Open `output/dashboard.html`.
3. Show KPI cards, anomaly radar, source health, TVL chart, validator table.
4. Open `output/report.md` and `output/report.json` to demonstrate multi-format generation.
5. Change one threshold in `config.json`, rerun, and show the anomaly output changing.
6. Show `.github/workflows/update.yml` for unattended hourly refresh.

## Submission checklist

- [x] Code prepared
- [x] README/setup prepared
- [x] Automated refresh workflow prepared
- [x] Markdown/JSON/HTML output generators prepared
- [x] Deterministic tests prepared
- [x] Sample fixture outputs generated and clearly marked
- [ ] Public GitHub repository (Human Gate)
- [ ] Optional hosted dashboard / GitHub Pages (Human Gate)
- [ ] Superteam submission (Human Gate)