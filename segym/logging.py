from __future__ import annotations

import json
from pathlib import Path

from segym.types import EpisodeResult, Scenario, TurnRecord


def write_json(path: str | Path, data: object) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)


def write_transcript(path: str | Path, transcript: list[TurnRecord]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as handle:
        for turn in transcript:
            handle.write(turn.model_dump_json() + "\n")


def write_candidate_log(path: str | Path, result: EpisodeResult) -> None:
    records = []
    for turn_index, record in enumerate(result.metadata.get("best_of_n", [])):
        for candidate in record.get("candidate_records", []):
            enriched = {
                "turn_index": turn_index,
                "n_candidates": record.get("n_candidates"),
                "selected_index": record.get("selected_index"),
                "selector": record.get("selector"),
                "lambda_ethics": record.get("lambda_ethics"),
                "base_model": record.get("base_model"),
                **candidate,
            }
            records.append(enriched)
    if not records:
        return

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def write_episode_result(out_dir: str | Path, scenario: Scenario, result: EpisodeResult) -> EpisodeResult:
    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    transcript_path = p / "transcript.jsonl"
    write_transcript(transcript_path, result.transcript)
    write_candidate_log(p / "candidates.jsonl", result)
    result.transcript_path = str(transcript_path)
    write_json(p / "result.json", result.model_dump(mode="json"))
    write_json(p / "scenario.json", scenario.model_dump(mode="json"))
    return result
