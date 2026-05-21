from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from segym.env import SettlementEthicsEnv
from segym.agents.factory import build_agent
from segym.analysis.metrics import aggregate_by_model
from segym.logging import write_episode_result, write_json


def load_split(path: str | Path) -> list[str]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip() and not line.startswith("#")]


def build_agent_from_model(model: dict):
    model_name = model.get("model_name")
    if model.get("model_name_env"):
        model_name = os.environ.get(model["model_name_env"], model_name)
    agent = build_agent(
        model["type"],
        model_id=model.get("id"),
        base_model_id=model.get("base_model_id"),
        n=model.get("n", 4),
        lambda_ethics=model.get("lambda_ethics", 1.0),
        shield_mode=model.get("shield_mode", "rewrite"),
        base_type=model.get("base_type", "scripted_deceptive"),
        provider=model.get("provider", "openai_compatible"),
        model_name=model_name or model.get("id", "llm"),
        system_prompt_path=model.get("system_prompt_path"),
        temperature=model.get("temperature", 0.2),
        max_tokens=model.get("max_tokens", 800),
        api_key_env=model.get("api_key_env", "OPENAI_API_KEY"),
        base_url=model.get("base_url", "https://api.openai.com/v1/chat/completions"),
        fake=model.get("fake", False),
        max_parse_retries=model.get("max_parse_retries", 1),
        max_request_retries=model.get("max_request_retries", 4),
        selector=model.get("selector", "utility_only"),
        verifier_provider=model.get("verifier_provider", "openai_compatible"),
        verifier_model_name=model.get("verifier_model_name", "gpt-4.1"),
        verifier_api_key_env=model.get("verifier_api_key_env", model.get("api_key_env", "OPENAI_API_KEY")),
        verifier_base_url=model.get("verifier_base_url", model.get("base_url", "https://api.openai.com/v1/chat/completions")),
        verifier_fake=model.get("verifier_fake", model.get("fake", False)),
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


def condition_names(config: dict) -> list[str]:
    raw_conditions = config.get("conditions") or ["neutral"]
    names: list[str] = []
    for condition in raw_conditions:
        if isinstance(condition, str):
            names.append(condition)
        elif isinstance(condition, dict):
            names.append(str(condition.get("name", "condition")))
        else:
            names.append(str(condition))
    return names


def result_row(result, scenario, model, condition, seed: int) -> dict:
    model_name = model.get("model_name")
    if model.get("model_name_env"):
        model_name = os.environ.get(model["model_name_env"], model_name)
    return {
        "run_id": result.run_id,
        "scenario_id": result.scenario_id,
        "domain": scenario.domain,
        "model_id": result.model_id,
        "model_type": model.get("type", ""),
        "provider": model.get("provider", ""),
        "model_name": model_name or "",
        "temperature": model.get("temperature", ""),
        "system_prompt_path": model.get("system_prompt_path", ""),
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
        "selected_unsafe_despite_safe": result.metadata.get("selected_unsafe_despite_safe", ""),
        "safe_candidate_available": result.metadata.get("safe_candidate_available", ""),
        "shield_triggered": result.metadata.get("shield_triggered", ""),
        "shield_trigger_count": result.metadata.get("shield_trigger_count", ""),
        "llm_parse_failed": result.metadata.get("llm_parse_failed", ""),
        "llm_parse_failure_count": result.metadata.get("llm_parse_failure_count", ""),
    }


def run_metadata(config: dict, run_root: Path, rows: list[dict]) -> dict:
    model_configs = []
    for model in config.get("models", []):
        redacted = dict(model)
        if "api_key" in redacted:
            redacted["api_key"] = "[redacted]"
        model_configs.append(redacted)
    return {
        "experiment_name": config.get("experiment_name", run_root.parent.name),
        "run_dir": str(run_root),
        "created_at_utc": run_root.name.split("_seed", maxsplit=1)[0],
        "seed": int(config.get("seed", 0)),
        "episode_rows": len(rows),
        "scenario_split": config.get("scenario_split"),
        "models": [model.get("id") for model in config.get("models", [])],
        "model_configs": model_configs,
        "conditions": condition_names(config),
        "fake_model_env": os.environ.get("SEGYN_FAKE_MODEL", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--scenario-split", help="Override config scenario_split.")
    parser.add_argument("--output-dir", help="Override config output_dir.")
    parser.add_argument("--seed", type=int, help="Override config seed.")
    args = parser.parse_args()

    with Path(args.config).open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if args.scenario_split:
        config["scenario_split"] = args.scenario_split
    if args.output_dir:
        config["output_dir"] = args.output_dir
    if args.seed is not None:
        config["seed"] = args.seed

    scenario_paths = load_split(config["scenario_split"])
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ")
    run_root = Path(config.get("output_dir", "runs/experiment")) / f"{timestamp}_seed{config.get('seed', 0)}"
    if args.dry_run:
        print(f"Would run {len(scenario_paths)} scenarios x {len(config['models'])} models into {run_root}")
        return 0

    rows = []
    for model in config["models"]:
        for condition in condition_names(config):
            agent = build_agent_from_model(model)
            for scenario_path in scenario_paths:
                env = SettlementEthicsEnv.from_path(
                    scenario_path,
                    config={
                        "max_rounds": config.get("max_rounds", 6),
                        "model_id": model["id"],
                        "condition": model.get("condition", condition),
                        "opponent_stochastic": config.get("opponent", {}).get("stochastic", False),
                        "seed": int(config.get("seed", 0)),
                    },
                )
                obs = env.reset(seed=int(config.get("seed", 0)))
                done = False
                while not done:
                    obs, _reward, done, _info = env.step(agent.act(obs))
                episode_dir = run_root / "episodes" / f"{model['id']}_{condition}_{env.scenario.scenario_id}"
                result = write_episode_result(episode_dir, env.scenario, env.result())
                rows.append(result_row(result, env.scenario, model, model.get("condition", condition), int(config.get("seed", 0))))

    run_root.mkdir(parents=True, exist_ok=True)
    with (run_root / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    write_json(run_root / "config.json", config)
    write_json(run_root / "metadata.json", run_metadata(config, run_root, rows))
    try:
        import pandas as pd

        aggregate = aggregate_by_model(pd.DataFrame(rows))
        records = aggregate.astype(object).where(pd.notna(aggregate), None).to_dict(orient="records")
        write_json(run_root / "aggregate_metrics.json", records)
    except Exception as exc:  # pragma: no cover - summary.csv remains the source of truth.
        write_json(run_root / "aggregate_metrics.json", {"error": str(exc)})
    print(f"Wrote {len(rows)} episode rows to {run_root / 'summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
