from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.add_wilson_intervals import wilson_interval


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def fmt(value: float | None) -> str:
    return "" if value is None or pd.isna(value) else f"{value:.6f}"


def rate_row(
    *,
    claim_family: str,
    measurement: str,
    model_id: str,
    numerator: int,
    denominator: int,
    status: str,
    notes: str,
) -> dict[str, str]:
    low, high = wilson_interval(numerator, denominator) if denominator else (None, None)
    return {
        "claim_family": claim_family,
        "measurement": measurement,
        "model_id": model_id,
        "numerator": str(numerator),
        "denominator": str(denominator),
        "rate": fmt(numerator / denominator if denominator else None),
        "wilson95_low": fmt(low),
        "wilson95_high": fmt(high),
        "status": status,
        "notes": notes,
    }


def deterministic_episode_rows(summary_path: Path) -> list[dict[str, str]]:
    if not summary_path.exists():
        return []
    frame = pd.read_csv(summary_path)
    rows = []
    for _, row in frame.iterrows():
        episodes = int(row["episodes"])
        count = int(round(float(row["material_misrepresentation_rate"]) * episodes))
        rows.append(
            rate_row(
                claim_family="deterministic_episode_rates",
                measurement="episode_material_misrepresentation",
                model_id=str(row["model_id"]),
                numerator=count,
                denominator=episodes,
                status="automated_deterministic",
                notes="Episode-level deterministic evaluator result; not proof of zero misconduct.",
            )
        )
    return rows


def judge_rows_from_agreement(path: Path, *, claim_family: str, measurement: str, notes: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    frame = pd.read_csv(path)
    row = frame[frame["comparison"] == "deterministic_vs_llm_judge"].iloc[0]
    return [
        rate_row(
            claim_family=claim_family,
            measurement=measurement,
            model_id="all_models",
            numerator=int(row["right_violation_rate_count"]),
            denominator=int(row["right_violation_rate_denominator"]),
            status="llm_judge_gpt41",
            notes=notes,
        )
    ]


def source_type_judge_rows(
    sample_path: Path,
    predictions_path: Path,
    source_type: str,
    *,
    source_label: str = "blindspot BoN",
) -> list[dict[str, str]]:
    if not sample_path.exists() or not predictions_path.exists():
        return []
    sample = pd.read_csv(sample_path).fillna("")
    predictions = pd.read_csv(predictions_path).fillna("")
    merged = sample.merge(
        predictions[["audit_id", "llm_judge_violation"]],
        on="audit_id",
        how="left",
    )
    subset = merged[merged["source_type"] == source_type].copy()
    flags = [bool_value(value) for value in subset["llm_judge_violation"]]
    rows = [
        rate_row(
            claim_family=f"{source_type}_only_risk_rates",
            measurement="row_material_or_misleading_violation",
            model_id="all_models",
            numerator=sum(flags),
            denominator=len(flags),
            status="llm_judge_gpt41",
            notes=f"GPT-4.1 judge over {source_label} {source_type} rows.",
        )
    ]
    for model_id, group in subset.groupby("model_id"):
        model_flags = [bool_value(value) for value in group["llm_judge_violation"]]
        rows.append(
            rate_row(
                claim_family=f"{source_type}_only_risk_rates",
                measurement="row_material_or_misleading_violation",
                model_id=str(model_id),
                numerator=sum(model_flags),
                denominator=len(model_flags),
                status="llm_judge_gpt41",
                notes=f"Model-specific GPT-4.1 judge rate over {source_label} {source_type} rows.",
            )
        )
    return rows


def pending_human_rows(sample_path: Path, predictions_path: Path, *, source_name: str) -> list[dict[str, str]]:
    if not sample_path.exists() or not predictions_path.exists():
        return []
    sample = pd.read_csv(sample_path).fillna("")
    predictions = pd.read_csv(predictions_path).fillna("")
    merged = sample.merge(predictions[["audit_id", "llm_judge_violation"]], on="audit_id", how="left")
    flagged_count = sum(bool_value(value) for value in merged["llm_judge_violation"])
    return [
        {
            "claim_family": "human_adjudicated_subset_rates",
            "measurement": f"{source_name}_flagged_rows",
            "model_id": "all_models",
            "numerator": "",
            "denominator": str(flagged_count),
            "rate": "",
            "wilson95_low": "",
            "wilson95_high": "",
            "status": "pending_human_or_legal_review",
            "notes": "Adjudication packet exists; do not report as human-adjudicated until reviewed by a human/legal expert.",
        }
    ]


def multi_judge_rows(path: Path, *, source_name: str, notes: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    frame = pd.read_csv(path).fillna("")
    rows = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "claim_family": "automated_multi_judge_sensitivity",
                "measurement": f"{source_name}_{row['metric']}",
                "model_id": "judge_panel",
                "numerator": str(int(row["count"])),
                "denominator": str(int(row["denominator"])),
                "rate": fmt(float(row["rate"])),
                "wilson95_low": fmt(float(row["wilson95_low"])),
                "wilson95_high": fmt(float(row["wilson95_high"])),
                "status": "automated_multi_judge_not_human",
                "notes": notes,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="paper/tables/headline_claims.csv")
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    rows.extend(deterministic_episode_rows(Path("paper/tables/blindspot_stress_bon_summary.csv")))
    rows.extend(deterministic_episode_rows(Path("paper/tables/blindspot_verified_shield_summary.csv")))
    rows.extend(deterministic_episode_rows(Path("paper/tables/paper48_stress_core_replication_seed802_chunked_summary.csv")))
    rows.extend(
        judge_rows_from_agreement(
            Path("paper/tables/blindspot_stress_bon_audit_agreement_judge_gpt41.csv"),
            claim_family="llm_judge_row_rates",
            measurement="mixed_transcript_candidate_rows",
            notes="GPT-4.1 judge over 1,000 sampled blindspot BoN transcript and candidate rows.",
        )
    )
    rows.extend(
        judge_rows_from_agreement(
            Path("paper/tables/blindspot_stress_bon_transcript_audit_agreement_judge_gpt41.csv"),
            claim_family="transcript_only_risk_rates",
            measurement="transcript_rows",
            notes="GPT-4.1 judge over final emitted transcript rows only.",
        )
    )
    rows.extend(
        source_type_judge_rows(
            Path("data/audit/blindspot_stress_bon_audit_sample.csv"),
            Path("data/audit/blindspot_stress_bon_audit_predictions_judge_gpt41.csv"),
            "candidate",
        )
    )
    rows.extend(
        source_type_judge_rows(
            Path("data/audit/blindspot_stress_bon_transcript_audit_sample.csv"),
            Path("data/audit/blindspot_stress_bon_transcript_audit_predictions_judge_gpt41.csv"),
            "transcript",
        )
    )
    rows.extend(
        judge_rows_from_agreement(
            Path("paper/tables/blindspot_verified_shield_transcript_audit_agreement_judge_gpt41.csv"),
            claim_family="verifier_shield_transcript_rates",
            measurement="verified_shield_transcript_rows",
            notes="GPT-4.1 judge over transcript rows from the fact-grounded verifier-shield blindspot run.",
        )
    )
    rows.extend(
        source_type_judge_rows(
            Path("data/audit/blindspot_verified_shield_transcript_audit_sample.csv"),
            Path("data/audit/blindspot_verified_shield_transcript_audit_predictions_judge_gpt41.csv"),
            "transcript",
            source_label="verifier-shield blindspot",
        )
    )
    rows.extend(
        pending_human_rows(
            Path("data/audit/blindspot_stress_bon_audit_sample.csv"),
            Path("data/audit/blindspot_stress_bon_audit_predictions_judge_gpt41.csv"),
            source_name="mixed_blindspot_bon",
        )
    )
    rows.extend(
        pending_human_rows(
            Path("data/audit/blindspot_stress_bon_transcript_audit_sample.csv"),
            Path("data/audit/blindspot_stress_bon_transcript_audit_predictions_judge_gpt41.csv"),
            source_name="transcript_blindspot_bon",
        )
    )
    rows.extend(
        pending_human_rows(
            Path("data/audit/blindspot_verified_shield_transcript_audit_sample.csv"),
            Path("data/audit/blindspot_verified_shield_transcript_audit_predictions_judge_gpt41.csv"),
            source_name="transcript_verifier_shield",
        )
    )
    rows.extend(
        multi_judge_rows(
            Path("paper/tables/paper48_stratified_multi_judge_summary.csv"),
            source_name="paper48_stratified",
            notes=(
                "Automated two-model judge sensitivity over the stratified audit packet; "
                "use as robustness evidence, not human/legal adjudication."
            ),
        )
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Wrote {len(rows)} claim rows to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
