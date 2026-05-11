# SettlementEthicsGym

SettlementEthicsGym is a synthetic benchmark for evaluating whether settlement-negotiation agents make material misrepresentations when placed under client-utility optimization pressure.

This repository contains synthetic benchmark scenarios for AI safety and legal-AI evaluation research. It does not provide legal advice, does not evaluate real lawyer conduct, and should not be used to automate real settlement negotiation.

## Quick Start

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/python -m segym.validate data/scenarios/seed/*.yaml
.venv/bin/python scripts/run_experiment.py --config configs/mvp_scripted.yaml
.venv/bin/python scripts/analyze_runs.py --run-dir runs/mvp_scripted --out paper/tables/mvp_summary.csv --figures paper/figures
tectonic paper/main.tex
```

## Scope

Version 0.1 focuses on civil settlement negotiation and truthfulness constraints inspired by ABA Model Rule 4.1. Labels are benchmark labels, not legal conclusions.

