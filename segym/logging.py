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


def write_episode_result(out_dir: str | Path, scenario: Scenario, result: EpisodeResult) -> EpisodeResult:
    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    transcript_path = p / "transcript.jsonl"
    write_transcript(transcript_path, result.transcript)
    result.transcript_path = str(transcript_path)
    write_json(p / "result.json", result.model_dump(mode="json"))
    write_json(p / "scenario.json", scenario.model_dump(mode="json"))
    return result

