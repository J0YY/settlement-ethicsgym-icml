# Result Interpretation Caveats

Do not use this note directly in the paper without rewriting it into paper voice.

The recent stress results are mixed but useful. The rewrite shield reaching zero
deterministic violations is evidence that the shield suppresses the violation
patterns captured by the deterministic evaluator, but it is not independent proof
that unsafe negotiation behavior has been eliminated. The shield uses the same
deterministic evaluator family that supplies the headline deterministic metric, so
the zero result is detector-aligned and could overstate safety.

The paper should therefore describe the shield result as zero deterministic
material/severe violations, report uncertainty intervals, and pair it with
independent LLM-judge and adjudicated audits. The main claim should be that
optimization pressure can surface misrepresentation and that detector-based
mitigations can reduce measured violations, not that the current shield proves
full legal or ethical safety.

Remaining high-risk interpretation issues:

- Zero of 48 observed violations still leaves nontrivial statistical uncertainty.
- LLM-judge and human-adjudicated audits are needed for detector-independent
  validation.
- Stress cases should include factual claims that are plausible but not covered by
  deterministic phrase rules, because a detector-aligned shield can overfit.
- Cross-model replication is promising, but model-specific utility and parse
  differences need to be reported explicitly.
