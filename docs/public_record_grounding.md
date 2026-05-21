# Public-Record-Grounded Scenario Split

`data/splits/public_record_grounded_v0_1_12.txt` contains 12 synthetic settlement-negotiation scenarios grounded in public civil case fact patterns.

The public record is used only for high-level facts such as the type of claim, injury mechanism, procedural posture, evidence dispute, or notice issue. The benchmark still syntheticizes party names, settlement values, role files, hidden knowledge splits, offers, dialogue, and forbidden assertion traps. This keeps the artifact free of confidential matter files while reducing reliance on purely invented factual settings.

The provenance table is `data/public_records/public_record_grounded_sources.csv`. Each row records the public source URL, source type, grounding note, and fields that were syntheticized.

This split is not expert legal annotation. It is a public-record-grounded extension for external-validity stress testing, while legal-ethics labels remain rule-inspired and require the same deterministic and LLM-judge sensitivity checks as the other splits.

Harvey's public Legal Agent Benchmark is useful related work because it shows a free, public legal-agent benchmark with long-horizon tasks and rubric criteria, but it is not used as a proprietary evaluator here. MikeOSS-style open legal assistant projects are not integrated because they do not supply independent legal-ethics labels for settlement misrepresentation and would add product/UI and licensing complexity without solving label validity.
