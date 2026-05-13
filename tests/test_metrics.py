import pandas as pd
import pytest

from segym.analysis.metrics import aggregate_by_model, discover_summary_paths, load_summary


def write_run(root, name, *, fake_env="", provider="openai_compatible", model_fake=False):
    run_dir = root / name
    run_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "model_id": "llm_zero_shot",
                "condition": "zero_shot",
                "scenario_id": "scenario_a",
                "settled": True,
                "client_utility": 1.0,
                "episode_has_material_violation": False,
                "episode_has_severe_violation": False,
                "material_violation_count": 0,
                "provider": provider,
            }
        ]
    ).to_csv(run_dir / "summary.csv", index=False)
    (run_dir / "metadata.json").write_text(
        (
            "{"
            f'"experiment_name": "llm_zero_shot", "fake_model_env": "{fake_env}", '
            f'"model_configs": [{{"id": "llm_zero_shot", "provider": "{provider}", "fake": {str(model_fake).lower()}}}]'
            "}"
        ),
        encoding="utf-8",
    )
    return run_dir


def test_aggregate_by_model_includes_best_of_n_rates_when_available():
    df = pd.DataFrame(
        [
            {
                "model_id": "best_of_n_utility",
                "condition": "neutral",
                "scenario_id": "a",
                "settled": True,
                "client_utility": 1.0,
                "episode_has_material_violation": True,
                "episode_has_severe_violation": True,
                "material_violation_count": 1,
                "safe_candidate_available": True,
                "selected_unsafe_despite_safe": True,
            },
            {
                "model_id": "best_of_n_utility",
                "condition": "neutral",
                "scenario_id": "b",
                "settled": True,
                "client_utility": 1.0,
                "episode_has_material_violation": False,
                "episode_has_severe_violation": False,
                "material_violation_count": 0,
                "safe_candidate_available": True,
                "selected_unsafe_despite_safe": False,
            },
        ]
    )

    summary = aggregate_by_model(df)

    assert summary.loc[0, "safe_candidate_available_rate"] == 1.0
    assert summary.loc[0, "selected_unsafe_despite_safe_rate"] == 0.5


def test_aggregate_by_model_includes_shield_rates_when_available():
    df = pd.DataFrame(
        [
            {
                "model_id": "shielded",
                "condition": "llm_shield",
                "scenario_id": "a",
                "settled": True,
                "client_utility": 1.0,
                "episode_has_material_violation": False,
                "episode_has_severe_violation": False,
                "material_violation_count": 0,
                "shield_triggered": True,
                "shield_trigger_count": 2,
            },
            {
                "model_id": "shielded",
                "condition": "llm_shield",
                "scenario_id": "b",
                "settled": True,
                "client_utility": 0.8,
                "episode_has_material_violation": False,
                "episode_has_severe_violation": False,
                "material_violation_count": 0,
                "shield_triggered": False,
                "shield_trigger_count": 0,
            },
        ]
    )

    summary = aggregate_by_model(df)

    assert summary.loc[0, "shield_triggered_rate"] == 0.5
    assert summary.loc[0, "mean_shield_trigger_count"] == 1.0


def test_aggregate_by_model_includes_llm_parse_failure_rates_when_available():
    df = pd.DataFrame(
        [
            {
                "model_id": "llm",
                "condition": "zero_shot",
                "scenario_id": "a",
                "settled": False,
                "client_utility": 0.0,
                "episode_has_material_violation": False,
                "episode_has_severe_violation": False,
                "material_violation_count": 0,
                "llm_parse_failed": True,
                "llm_parse_failure_count": 2,
            },
            {
                "model_id": "llm",
                "condition": "zero_shot",
                "scenario_id": "b",
                "settled": True,
                "client_utility": 1.0,
                "episode_has_material_violation": False,
                "episode_has_severe_violation": False,
                "material_violation_count": 0,
                "llm_parse_failed": False,
                "llm_parse_failure_count": 0,
            },
        ]
    )

    summary = aggregate_by_model(df)

    assert summary.loc[0, "llm_parse_failed_rate"] == 0.5
    assert summary.loc[0, "mean_llm_parse_failure_count"] == 1.0


def test_load_summary_latest_only_selects_latest_run_per_root(tmp_path):
    root = tmp_path / "runs" / "llm_zero_shot"
    old = write_run(root, "2026-05-12T000000Z_seed1")
    latest = write_run(root, "2026-05-13T000000Z_seed1")

    paths = discover_summary_paths(root, latest_only=True)
    df = load_summary(root, latest_only=True, require_real=True)

    assert paths == [latest / "summary.csv"]
    assert set(df["source_run_dir"]) == {str(latest)}
    assert str(old) not in set(df["source_run_dir"])


def test_load_summary_require_real_rejects_fake_env(tmp_path):
    root = tmp_path / "runs" / "llm_zero_shot"
    run_dir = write_run(root, "2026-05-12T000000Z_seed1", fake_env="1")

    with pytest.raises(ValueError, match="fake_model_env"):
        load_summary(root, require_real=True)

    df = load_summary(root, require_real=False)
    assert set(df["source_run_dir"]) == {str(run_dir)}


def test_load_summary_require_real_rejects_provider_fake(tmp_path):
    root = tmp_path / "runs" / "llm_zero_shot"
    write_run(root, "2026-05-12T000000Z_seed1", provider="fake")

    with pytest.raises(ValueError, match="provider=fake"):
        load_summary(root, require_real=True)


def test_load_summary_accepts_multiple_roots(tmp_path):
    root_a = tmp_path / "runs" / "llm_zero_shot"
    root_b = tmp_path / "runs" / "llm_ethics_prompt"
    latest_a = write_run(root_a, "2026-05-13T000000Z_seed101")
    latest_b = write_run(root_b, "2026-05-13T010000Z_seed102")

    df = load_summary([root_a, root_b], latest_only=True, require_real=True)

    assert set(df["source_run_dir"]) == {str(latest_a), str(latest_b)}
