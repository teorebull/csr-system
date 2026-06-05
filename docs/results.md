# Results

These results come from the last saved run in the repository.

This project produces two final artifacts for each company:

- `final_summary.md`: the human-readable result
- `final_traceability_report.md`: the evidence trail for each claim

The report is claim-by-claim. It does not give one simple yes or no answer.

## Why Results Can Change

The pipeline is not fully deterministic because it still uses LLMs and live web search.

That means two runs can produce almost the same overall result, but one or two claim labels may change. This usually happens on borderline claims, where the evidence is indirect or the model is deciding between two close labels.

The repository keeps saved snapshots of each run, but it does not store every intermediate rerun. So the exact output can vary slightly from run to run, even when the general pattern stays stable.

## Claim Labels

- `supported`: outside evidence clearly backs up the claim.
- `partially_supported`: the evidence supports part of the claim, but not all of it.
- `unverified`: the evidence is too weak, too general, or too indirect to confirm the claim.
- `partially_contradicted`: the evidence raises a real concern, but it does not fully overturn the claim.
- `contradicted`: the evidence directly conflicts with the claim.

## Risk Labels

The environmental subset also gets a risk signal.

- `low`: little concern from the selected evidence.
- `medium`: some caution is needed.
- `high`: the evidence raises a serious claim-specific concern.
- `unclear`: the evidence is too weak or too unrelated to judge.

## Real Result Snapshot: Microsoft

This is the clearest stored run in the repository.

- Total claims assessed: 15
- Supported: 7
- Partially supported: 1
- Unverified: 7
- Partially contradicted: 0
- Contradicted: 0
- Verdict: `Mixed Evidence`

Environmental subset:

- Environmental claims assessed: 7
- Supported: 1
- Partially supported: 0
- Unverified: 6
- Partially contradicted: 0
- Contradicted: 0

What this means:

- The system found real support for several claims.
- A large part of the set stayed unverified, which usually means the sources were not specific enough.
- There was no contradiction-level evidence in that run.
- The environmental subset was mostly cautious, not strongly adverse.

## Real Result Snapshot: Meta

- Total claims assessed: 15
- Supported: 4
- Partially supported: 0
- Unverified: 8
- Partially contradicted: 3
- Contradicted: 0
- Verdict: `Questionable`

This run is stronger on concern signals than the Microsoft one.

## How To Read The Final Summary

- Many `supported` claims usually mean the company's story is fairly well backed.
- Many `unverified` claims usually mean the evidence was thin, not that the company is lying.
- Several `partially_contradicted` or `contradicted` claims usually mean the narrative has real weaknesses.

## What To Send To The Judges

- `final_summary.md`
- `final_traceability_report.md`
- `final_report.json` if they want structured data

## Reproducibility Note

The pipeline is not fully deterministic because it still uses LLMs and web search.

That means a new run can change one or two claim labels, especially when the evidence is borderline or indirect. The repository does not save every rerun, so the exact intermediate outputs may differ slightly from one execution to the next.

Even so, the overall pattern stays almost the same across runs. In practice, the final verdict and the main supported or unverified claims remain very similar.

## Important Note

This is not a legal finding. It is a structured reading of the selected claims and the selected external evidence.
