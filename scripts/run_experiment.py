from __future__ import annotations

import argparse
import csv
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from segym.env import SettlementEthicsEnv
from segym.agents.factory import build_agent
from segym.logging import write_episode_result, write_json


def load_split(path: str | Path) -> list[str]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip() and not line.startswith("#")]


def build_agent_from_model(model: dict):
    agent = build_agent(
        model["type"] if model["type"] != "shielded" else "shielded_deceptive",
        n=model.get("n", 4),
        lambda_ethics=model.get("lambda_ethics", 1.0),
        shield_mode=model.get("shield_mode", "rewrite"),
        base_type=model.get("base_type", "scripted_deceptive"),
    )
    if model["type"] == "best_of_n_utility":
        agent.n = int(model.get("n", 4))
        agent.model_id = model["id"]
    if model["type"] == "best_of_n_ethics":
        agent.n = int(model.get("n", 4))
        agent.model_id = model["id"]
    if model["type"] == "shielded":
        agent.model_id = model["id"]
    return agent


def result_row(result, scenario, model, condition, seed: int) -> dict:
    return {
        "run_id": result.run_id,
        "scenario_id": result.scenario_id,
        "domain": scenario.domain,
        "model_id": result.model_id,
        "condition": condition,
        "n_candidates": model.get("n", 1),
        "shield_mode": model.get("shield_mode", ""),
        "role": scenario.agent_role,
        "seed": seed,
        "settled": result.settled,
        "final_amount_usd": result.final_settlement_amount_usd or "",
        "client_utility": result.client_utility,
        "opponent_utility": result.opponent_utility,
        "rounds": result.rounds,
        "material_violation_count": result.material_false_statement_count,
        "severe_violation_count": result.severe_violation_count,
        "misleading_half_truth_count": result.misleading_half_truth_count,
        "false_law_count": sum(1 for f in result.ethics_findings if f.label == "FALSE_STATEMENT_OF_LAW"),
        "puffery_count": result.permissible_puffery_count,
        "over_refusal_count": result.over_refusal_count,
        "over_disclosure_count": result.over_disclosure_count,
        "opponent_reliance_count": result.metadata.get("opponent_reliance_count", 0),
        "episode_has_material_violation": result.material_false_statement_count > 0,
        "episode_has_severe_violation": result.severe_violation_count > 0,
        "selected_unsafe_despite_safe": "",
        "safe_candidate_available": "",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with Path(args.config).open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    scenario_paths = load_split(config["scenario_split"])
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ")
    run_root = Path(config.get("output_dir", "runs/experiment")) / f"{timestamp}_seed{config.get('seed', 0)}"
    if args.dry_run:
        print(f"Would run {len(scenario_paths)} scenarios x {len(config['models'])} models into {run_root}")
        return 0

    rows = []
    for model in config["models"]:
        agent = build_agent_from_model(model)
        for scenario_path in scenario_paths:
            condition = model.get("condition", model["type"])
            env = SettlementEthicsEnv.from_path(
                scenario_path,
                config={
                    "max_rounds": config.get("max_rounds", 6),
                    "model_id": model["id"],
                    "condition": condition,
                    "opponent_stochastic": config.get("opponent", {}).get("stochastic", False),
                },
            )
            obs = env.reset(seed=int(config.get("seed", 0)))
            done = False
            while not done:
                obs, _reward, done, _info = env.step(agent.act(obs))
            episode_dir = run_root / "episodes" / f"{model['id']}_{env.scenario.scenario_id}"
            result = write_episode_result(episode_dir, env.scenario, env.result())
            rows.append(result_row(result, env.scenario, model, condition, int(config.get("seed", 0))))

    run_root.mkdir(parents=True, exist_ok=True)
    with (run_root / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    write_json(run_root / "config.json", config)
    print(f"Wrote {len(rows)} episode rows to {run_root / 'summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
