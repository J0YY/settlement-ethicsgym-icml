import subprocess
import sys

from scripts.run_experiment import condition_names
from scripts.run_experiment import load_split


def test_condition_names_reads_top_level_strings():
    assert condition_names({"conditions": ["neutral", "shielded"]}) == ["neutral", "shielded"]


def test_condition_names_reads_top_level_dicts():
    assert condition_names({"conditions": [{"name": "zero_shot"}]}) == ["zero_shot"]


def test_load_split_ignores_comments_and_blank_lines(tmp_path):
    split = tmp_path / "split.txt"
    split.write_text("\n# comment\ndata/scenarios/a.yaml\n\n", encoding="utf-8")

    assert load_split(split) == ["data/scenarios/a.yaml"]


def test_run_experiment_dry_run_accepts_cli_overrides(tmp_path):
    split = tmp_path / "split.txt"
    split.write_text("data/scenarios/seed/pi_policy_limits_001.yaml\n", encoding="utf-8")
    config = tmp_path / "config.yaml"
    config.write_text(
        "\n".join(
            [
                'experiment_name: "override_test"',
                "seed: 1",
                'scenario_split: "data/splits/mvp_test.txt"',
                "models:",
                '  - id: "scripted_honest"',
                '    type: "scripted_honest"',
                'output_dir: "runs/original"',
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_experiment.py",
            "--config",
            str(config),
            "--scenario-split",
            str(split),
            "--output-dir",
            str(tmp_path / "override_runs"),
            "--seed",
            "77",
            "--dry-run",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Would run 1 scenarios x 1 models" in result.stdout
    assert "override_runs" in result.stdout
    assert "seed77" in result.stdout
