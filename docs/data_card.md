# SettlementEthicsGym Data Card

Last updated: 2026-05-12

## Dataset Summary

SettlementEthicsGym v0.1 is a synthetic benchmark dataset for evaluating
truthfulness failures in simulated civil settlement negotiation. It is designed
to test whether settlement-outcome optimization pressure increases material
misrepresentation by an evaluated legal-negotiation agent.

The dataset is not a collection of real legal advice, real client files, real
settlement negotiations, or real lawyer disciplinary records. It is a controlled
research artifact with invented facts and rule-inspired labels.

## Current Contents

Current repository contents:

- 8 handwritten seed scenarios in `data/scenarios/seed/`.
- 24 generated variants in `data/scenarios/generated/v0.1/`.
- 32 total scenarios.
- A synthetic truthfulness rubric in `data/rubrics/aba_rule_4_1_like.yaml`.
- Split files in `data/splits/`.

Each scenario contains:

- public case summary;
- agent private case file;
- opponent private case file;
- party roles;
- reservation values;
- hidden truth-table facts;
- allowed puffery examples;
- forbidden pattern mappings;
- sample gold utterances;
- opponent belief update parameters;
- termination rules.

## Why The Data Is Synthetic

The benchmark target requires information that public legal datasets usually do
not expose:

- what the evaluated agent knew;
- what the opponent knew;
- which hidden facts were true or false;
- the negotiation message that was sent;
- whether the message asserted fact, law, value, intention, puffery, or silence;
- whether a half-truth created a materially false impression;
- whether the opponent relied on the statement.

Public legal materials can inspire scenario families, but they generally do not
provide private negotiation transcripts, hidden knowledge states, or adjudicated
truthfulness labels. Synthetic data lets the benchmark control those variables.

## Intended Uses

Appropriate uses:

- AI safety research on reward hacking and optimization pressure;
- legal-AI evaluation research;
- testing negotiation-agent controls such as best-of-N selection, ethics-aware
  reranking, and shields;
- studying evaluator reliability on controlled truthfulness traps.

Inappropriate uses:

- real legal advice;
- deciding whether a real lawyer violated professional duties;
- automated real settlement negotiation;
- claims about jurisdiction-specific legal discipline;
- training or deploying a legal assistant without additional review.

## Legal And Ethical Scope

The current rubric is inspired by U.S.-style professional-responsibility
truthfulness constraints, especially ABA Model Rule 4.1-like distinctions
between material false statements and ordinary negotiation posturing.

The benchmark intentionally does not model:

- unauthorized practice of law;
- attorney-client privilege;
- conflicts of interest;
- candor to tribunals;
- ex parte communication;
- criminal plea bargaining;
- jurisdiction-specific disciplinary standards.

## Current Limitations

The current data is too small and too templated for final paper claims.

Important limitations:

- only 8 handwritten seed scenarios;
- generated variants mostly scale monetary values and preserve the same trap
  structure;
- no human/legal-expert audit yet;
- no real LLM evaluation results yet;
- deterministic evaluator coverage is strong only for known trap patterns;
- no public-source grounding notes are attached to scenario families yet.

Paper-quality use requires expanding the seed set, adding held-out trap
families, adding public-source notes where useful, and auditing model outputs.

## Planned Improvements

Near-term data work:

- expand to at least 40 handwritten seed scenarios;
- add held-out trap-category splits;
- add source notes for scenario families;
- add human-audited labels for 100-200 utterances;
- separate training, development, test, and held-out trap splits by scenario
  family rather than random file assignment.

Training-specific data work, if fine-tuning or RL is added:

- build safe demonstration responses;
- build unsafe/high-utility stress responses;
- build preference pairs for DPO or similar methods;
- keep all training examples disjoint from held-out scenario families;
- audit trained-policy outputs separately.
