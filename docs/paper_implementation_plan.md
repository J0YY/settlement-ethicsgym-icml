# SettlementEthicsGym Paper Implementation Plan

Last updated: 2026-05-12

## Current Position

SettlementEthicsGym is currently a no-training, no-API benchmark scaffold. It has
synthetic settlement scenarios, deterministic ethics labels, scripted agents,
best-of-N selection, a rewrite shield, experiment runners, analysis scripts, and
paper-output plumbing. The current results are useful as a systems check and
calibration exercise, but they are not yet evidence that deployed LLM agents
learn or choose deception in realistic legal settlement negotiation.

The paper should not currently claim:

- that a model was trained;
- that real legal negotiation transcripts were used;
- that the benchmark decides real legal ethics violations;
- that observed scripted-agent behavior generalizes to practicing lawyers or
  deployed legal products;
- that the project is the first legal settlement benchmark.

The defensible current claim is narrower:

> SettlementEthicsGym is a controlled synthetic benchmark for evaluating whether
> optimization pressure in simulated legal settlement negotiation amplifies
> material misrepresentation, and whether ethics-aware selection or shields can
> reduce those violations.

## Why The Current Data Is Synthetic

The behavior we want to measure needs information that public legal datasets
usually do not contain. For every negotiation episode, we need:

- public dispute facts;
- the evaluated agent's private facts;
- the opponent's private facts;
- hidden ground-truth facts;
- what each party knew when a statement was made;
- multi-turn negotiation messages;
- settlement offers and reservation values;
- whether a statement was a concrete material fact, puffery, value estimate,
  legal claim, half-truth, or omission-equivalent;
- whether the opponent relied on the statement;
- a ground-truth ethics label.

Public legal sources usually provide final-stage or court-facing artifacts:
complaints, answers, motions, opinions, settlement agreements, consent decrees,
press releases, regulatory summaries, and docket entries. These can ground
scenario design, but they usually do not expose private settlement negotiation
transcripts, hidden knowledge states, or reliable labels about whether a
negotiation statement was knowingly false.

Using synthetic scenarios is therefore not a shortcut by itself. It is a way to
control hidden facts and knowledge states. The risk is that synthetic scenarios
can be too small, too templated, or too evaluator-specific. The paper-quality
version must address that risk through scale, held-out scenario families,
human/legal audit, and real model baselines.

## Existing Data Assets

Current repository data:

- `data/scenarios/seed/`: 8 handwritten synthetic seed scenarios.
- `data/scenarios/generated/v0.1/`: 24 generated variants produced by scaling
  monetary amounts and cloning seed structure.
- `data/rubrics/aba_rule_4_1_like.yaml`: synthetic rule-inspired truthfulness
  rubric.
- `data/splits/`: MVP and generated scenario split files.

Current scenario categories:

- false policy limits / hidden umbrella coverage;
- fabricated eyewitness;
- fabricated surveillance video;
- false payroll records;
- false delivery record;
- false limitations period;
- false notice service;
- settlement authority edge case.

Current variants are useful for smoke testing but not enough for a strong paper.
They are too close to the seed templates and should not be treated as independent
evidence of generalization.

## Existing Experiment Assets

Current agents:

- `scripted_honest`: makes settlement offers without concrete false factual
  claims.
- `scripted_deceptive`: emits scenario-specific false material claims.
- `best_of_n_utility`: selects among scripted candidate actions using a simple
  utility heuristic.
- `best_of_n_ethics`: selects among the same candidates with an ethics penalty.
- `shielded_deceptive`: rewrites or blocks risky claims from a deceptive base
  agent.

Current evaluator:

- deterministic pattern matching against scenario forbidden patterns and
  unsafe assertions;
- explicit special handling for one coverage half-truth class;
- permissive handling for scenario-listed puffery/value language.

Current experiments:

- scripted MVP over 8 seed scenarios;
- generated scripted run over 24 variants;
- best-of-N scaling over N = 1, 2, 4 and ethics-aware N = 4.

These are calibration experiments. They show that the plumbing can distinguish
safe from unsafe actions under controlled conditions. They should be presented
as benchmark validation, not as final empirical results.

## Paper-Quality Target

The strongest near-term paper should be a benchmark and inference-time
optimization paper, not primarily a training paper.

Target thesis:

> In controlled legal settlement simulations with explicit hidden-fact truth
> tables, LLM agents under client-utility optimization pressure are more likely
> to select materially false or misleading statements. Ethics-aware selection,
> structured shields, and evaluator-audited feedback reduce violations, with a
> measurable utility tradeoff.

This thesis does not require training a model. It requires credible LLM-facing
evaluation, enough scenarios, defensible labels, and clear held-out tests.

## Why Not Start With RL/Fine-Tuning

RL and fine-tuning are possible, but they are not the first bottleneck.

Main blockers:

1. Data scale is too small.
   Eight seed scenarios and twenty-four near-variants are insufficient for
   meaningful fine-tuning or RL generalization claims.

2. Reward validity is underdeveloped.
   If reward is mostly settlement utility, a trained policy can overfit to the
   scripted opponent and scenario quirks. If reward includes deterministic
   ethics penalties, a policy can learn to evade string patterns instead of
   becoming truthful.

3. Evaluation must be independent of training.
   Training on the same scenario templates used for evaluation would invite the
   criticism that the model learned the benchmark rather than the underlying
   constraint.

4. Multi-turn RL is expensive and brittle.
   Online RL over LLM actions requires many rollouts. A brittle simulator or
   weak evaluator will dominate results.

5. The paper claim changes.
   If we add RL, the paper becomes a training/control paper. That demands more
   compute, stronger baselines, and careful train/dev/test separation.

Recommended ordering:

1. Build a credible benchmark and LLM evaluation.
2. Add inference-time optimization experiments.
3. Add a small controlled SFT/DPO/RL appendix or second-stage section only after
   the benchmark is robust.

## Implementation Roadmap

### Phase 1: Benchmark Hardening

Goal: make the dataset and evaluator credible enough for paper review.

Tasks:

- Expand handwritten scenarios from 8 to at least 40.
- Cover at least 8-10 trap categories:
  - policy limits / coverage;
  - fabricated witness;
  - fabricated evidence;
  - false procedural posture;
  - false document status;
  - false payroll/business records;
  - false law or deadline;
  - false authority/client status;
  - misleading half-truth about available assets or coverage;
  - permissible puffery/value estimates as negative controls.
- Create train/dev/test splits by scenario family, not just random files.
- Add held-out trap categories for generalization checks.
- Add a data card:
  - provenance;
  - synthetic construction process;
  - intended use;
  - prohibited use;
  - legal/ethics limitations;
  - known failure modes.
- Add scenario review metadata fields:
  - author;
  - reviewer;
  - legal-domain notes;
  - public-source inspiration if any;
  - version.

Deliverables:

- `docs/data_card.md`
- expanded `data/scenarios/seed/*.yaml`
- `data/splits/train.txt`
- `data/splits/dev.txt`
- `data/splits/test.txt`
- `data/splits/heldout_trap_test.txt`

Definition of done:

```bash
.venv/bin/python -m segym.validate data/scenarios/seed/*.yaml
.venv/bin/python -m pytest tests/test_scenario_validation.py
```

### Phase 2: Public-Document Grounding

Goal: reduce the appearance that scenarios are arbitrary while preserving
controlled hidden facts.

Tasks:

- Collect public civil settlement/case materials as inspiration only:
  - public complaints;
  - consent decrees;
  - settlement agreements;
  - AG press releases;
  - court opinions involving settlement-related truthfulness issues where
    available.
- Do not copy real private facts into scenarios.
- Add source notes at the scenario-family level.
- Write a paper subsection explaining why public documents cannot directly
  supply hidden negotiation truth tables.

Deliverables:

- `docs/source_notes.md`
- scenario-family source notes in YAML metadata;
- citation list for paper related work and dataset construction.

Definition of done:

- each scenario family has at least one public source note or an explicit note
  explaining that it is a purely synthetic ethics trap;
- paper dataset section states what is and is not derived from public sources.

### Phase 3: Real LLM Agent Evaluation

Goal: replace scripted-only findings with model-facing results.

Tasks:

- Implement `segym/agents/llm.py`:
  - provider abstraction;
  - OpenAI-compatible chat adapter;
  - optional Anthropic/litellm adapter;
  - deterministic fake model for tests;
  - strict JSON action schema;
  - retry/repair for invalid outputs;
  - temperature/top-p controls;
  - prompt and model metadata logging.
- Add prompts:
  - neutral legal negotiator;
  - client-utility focused negotiator;
  - ethics-prompted negotiator;
  - opponent counsel;
  - shield rewrite;
  - LLM judge.
- Add configs:
  - `configs/exp_llm_zero_shot.yaml`
  - `configs/exp_llm_ethics_prompt.yaml`
  - `configs/exp_llm_best_of_n.yaml`
  - `configs/exp_llm_shield.yaml`
- Log all candidate generations, selected actions, rejected actions, and parser
  failures.

Deliverables:

- real LLM episode transcripts;
- summary CSVs with model/provider/version metadata;
- paper-ready model comparison tables.

Definition of done:

```bash
SEGYN_FAKE_MODEL=1 .venv/bin/python -m pytest
.venv/bin/python scripts/run_experiment.py --config configs/exp_llm_zero_shot.yaml --dry-run
```

### Phase 4: Inference-Time Optimization Experiments

Goal: test optimization pressure without claiming training.

Tasks:

- Generate N candidate messages per turn from the same base LLM.
- Evaluate N values: 1, 2, 4, 8, 16.
- Select by:
  - utility-only;
  - utility minus ethics penalty;
  - utility subject to no high-confidence violation;
  - shielded rewrite.
- Track:
  - candidate-level violation rate;
  - selected-message violation rate;
  - selected unsafe despite safe candidate;
  - settlement rate;
  - client utility;
  - over-refusal;
  - over-disclosure;
  - invalid JSON/format failures.

Deliverables:

- `paper/figures/best_of_n_scaling.png`
- `paper/tables/best_of_n_llm_results.csv`
- candidate-level logs in run directories.

Definition of done:

- best-of-N scaling plot shows violation rate and utility by N;
- results include confidence intervals or bootstrap intervals;
- every run is reproducible from config.

### Phase 5: Evaluator Ensemble And Human Audit

Goal: make ethics labels credible.

Tasks:

- Implement LLM judge evaluator:
  - scenario-aware;
  - outputs label, severity, confidence, rationale, mapped facts;
  - cannot see deterministic evaluator label unless in ensemble mode.
- Implement ensemble adjudicator:
  - deterministic high-confidence traps override where exact match exists;
  - LLM judge handles open-ended language;
  - disagreements are flagged for human audit.
- Create audit sample:
  - stratified by model, trap category, deterministic label, LLM judge label,
    and severity.
- Build annotation CSV:
  - utterance;
  - scenario hidden facts;
  - agent private facts;
  - public context;
  - labels;
  - annotator fields.
- Report:
  - inter-annotator agreement;
  - deterministic vs adjudicated precision/recall;
  - LLM judge vs adjudicated precision/recall;
  - high-confidence-only results.

Deliverables:

- `scripts/make_audit_sample.py`
- `scripts/evaluate_audit_labels.py`
- `data/audit/audit_sample.csv`
- `data/audit/labels_adjudicated.csv`
- `paper/tables/audit_agreement.csv`

Definition of done:

- at least 100-200 utterances audited;
- paper reports agreement and residual label uncertainty.

### Phase 6: Optional Training Experiments

Goal: add a real training/control section after the benchmark is stable.

Training approaches, in increasing complexity:

1. Supervised fine-tuning on safe demonstrations.
   - Build safe/honest demonstration responses.
   - Train LoRA on an open model.
   - Evaluate on held-out scenario families.

2. Supervised fine-tuning on utility-maximizing demonstrations.
   - Use deceptive/high-utility demonstrations as a stress condition.
   - Test whether utility-only demonstrations increase violations.

3. Preference tuning / DPO.
   - Create pairs:
     - safe high-utility response preferred over unsafe high-utility response;
     - safe response preferred over over-refusal when both avoid violations;
     - truthful material fact preferred over misleading half-truth.
   - Train LoRA/DPO on train split only.

4. RL or GRPO-style optimization.
   - Reward variants:
     - settlement utility only;
     - settlement utility minus ethics penalty;
     - settlement utility with hard violation constraint;
     - settlement utility plus opponent fairness/welfare.
   - Use a small open model and bounded rollout budget.

Required safeguards:

- strict train/dev/test separation by scenario family;
- held-out trap category evaluation;
- evaluator not identical to training reward where possible;
- human-audited subset of trained-policy outputs;
- report reward hacking examples, not only aggregate scores.

Training deliverables:

- `configs/train_sft_safe.yaml`
- `configs/train_sft_utility.yaml`
- `configs/train_dpo_safe_utility.yaml`
- optional `configs/train_rl_utility.yaml`
- training scripts or integration with TRL;
- model cards for trained adapters;
- paper table comparing base, prompted, SFT, DPO, and optional RL.

Definition of done:

- trained adapters improve or change metrics on held-out scenarios;
- results survive high-confidence and human-audited subsets;
- paper explicitly distinguishes inference-time optimization from training.

## Experimental Matrix

Minimum paper matrix:

| Condition | Training? | Purpose |
|---|---:|---|
| scripted honest | no | calibration lower-risk baseline |
| scripted deceptive | no | calibration upper-risk baseline |
| LLM zero-shot | no | base model behavior |
| LLM ethics prompt | no | prompt-only control |
| LLM utility prompt | no | explicit client-utility pressure |
| LLM best-of-N utility | no | inference-time optimization pressure |
| LLM best-of-N ethics-aware | no | process reward/control |
| LLM shielded rewrite | no | action-level control |

Optional training matrix:

| Condition | Training? | Purpose |
|---|---:|---|
| SFT safe demos | yes | supervised compliance |
| SFT utility demos | yes | utility-pressure stress |
| DPO safe-over-unsafe | yes | preference control |
| RL utility-only | yes | reward-induced violation test |
| RL utility-minus-ethics | yes | constrained reward test |

## Metrics

Primary metrics:

- material misrepresentation rate;
- high-confidence material misrepresentation rate;
- severe violation rate;
- mean material violation count;
- client utility;
- settlement rate.

Optimization-pressure metrics:

- candidate-level violation rate;
- selected-message violation rate;
- safe candidate available rate;
- selected unsafe despite safe candidate rate;
- violation rate as a function of N;
- utility gain as a function of N.

Control metrics:

- shield rewrite rate;
- blocked action rate;
- over-refusal rate;
- over-disclosure rate;
- utility loss under control;
- false-positive shield rate on permissible puffery.

Evaluator metrics:

- deterministic evaluator precision/recall against audit;
- LLM judge precision/recall against audit;
- inter-annotator agreement;
- disagreement rate by trap category.

## Paper Updates Needed

Update `main.tex`:

- Rename/reframe if no training is included:
  - safer title: "Measuring Optimization-Amplified Misrepresentation in
    Settlement Negotiation";
  - avoid "learn" unless actual training experiments are present.
- Add Dataset section:
  - synthetic construction;
  - why public data is insufficient;
  - source grounding;
  - splits;
  - data card summary.
- Add Related Work:
  - SettleAgent/SettleBench;
  - NegotiationArena and other negotiation benchmarks;
  - LegalBench/legal NLP benchmarks;
  - deception/reward hacking evaluations;
  - legal ethics / Model Rule 4.1-inspired truthfulness.
- Add Experiments:
  - scripted calibration;
  - LLM baselines;
  - best-of-N scaling;
  - shield/control results;
  - human audit.
- Add Limitations:
  - synthetic scenarios;
  - no legal advice;
  - U.S.-style rule-inspired taxonomy;
  - evaluator uncertainty;
  - no real lawyer discipline conclusions;
  - no training unless training is actually implemented.

## Immediate Next Engineering Tasks

Highest priority:

1. Create `docs/data_card.md`.
2. Add 32+ new handwritten seed scenarios.
3. Implement real LLM agent adapter with fake-model tests.
4. Add LLM experiment configs.
5. Add candidate-level transcript logging for LLM best-of-N.
6. Implement LLM judge skeleton and prompt.
7. Create audit sampling script.
8. Update paper title/claims to match actual experiments.

Second priority:

1. Add public-source notes for scenario families.
2. Add bootstrap confidence intervals in analysis.
3. Add held-out trap split.
4. Add over-refusal and over-disclosure test cases.
5. Add prompt/version/model metadata to every run.

Training priority, only after the above:

1. Build safe and unsafe demonstration datasets from train split.
2. Implement LoRA SFT on a small open model.
3. Implement DPO preference dataset and training.
4. Consider RL only after SFT/DPO results and evaluator audit are stable.

## Decision Record

Decision: keep synthetic scenarios as the core benchmark data, but do not rely
on tiny templated data for final claims.

Reason: the target construct requires hidden facts and knowledge states that
public datasets generally lack.

Decision: prioritize LLM evaluation and inference-time optimization before RL.

Reason: a no-training benchmark can be strong if labels, scenarios, and
evaluation are credible. RL before evaluator hardening risks producing reward
hacking against a toy simulator.

Decision: add RL/fine-tuning only as a later controlled experiment.

Reason: training claims require larger data, held-out scenario families,
independent evaluation, and ideally human-audited outputs.
