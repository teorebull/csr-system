# CSR System

This project checks how credible a company's CSR story is.

It reads company reports, pulls out claims, looks for outside evidence, and builds a final judgment. The goal is simple: see which claims are supported, which are weak, and which raise concern.

The pipeline is split into small agents so each step stays clear and traceable.

## What it does

- Reads CSR or sustainability documents
- Extracts claims from the text
- Removes duplicates and weak claims
- Creates web search queries for each claim
- Finds external evidence
- Ranks the best sources
- Compares claims with evidence
- Produces a final report

## Agent Overview

- Agent 1 loads and cleans the documents.
- Agent 2 extracts candidate claims from the pages.
- Agent 3 merges similar claims and keeps the useful ones.
- Agent 4 writes focused search queries for each claim.
- Agent 5 searches the web for outside sources.
- Agent 6 downloads and extracts the source text.
- Agent 7 ranks the evidence and keeps the best matches.
- Agent 8 checks each claim against the evidence.
- Agent 9 combines everything into the final report.

## Purpose Of These Sections

- The `agents` section describes what each stage of the pipeline does.
- The `results` section explains the final labels and shows real outputs from the pipeline.

## What To Submit

- `README.md`: short project overview and structure.
- `DELIVERY_README.md`: guide to the zip package contents.
- `memoria`: the full written report.
- `presentació`: the defense slides.
- `codi`: the full implementation.
- `docs/results.md`: real result summary and label guide.
- `data/processed/langgraph/<company>/agent_9/final_summary.md`: human-readable final outcome.
- `data/processed/langgraph/<company>/agent_9/final_traceability_report.md`: claim-by-claim traceability.
- `data/processed/langgraph/<company>/agent_9/final_report.json`: structured final output.

## Results And Traceability

The final summary tells the story in plain language.
The traceability report shows where every final claim came from.
The pipeline is not fully deterministic because it still uses LLMs and live web search, so small label changes can happen between reruns. The saved reports capture one stable snapshot, and the overall results stay very close across runs.

For the final defense, the two most useful files are:

- `final_summary.md`
- `final_traceability_report.md`

## More Detail

See `docs/agents.md` for a fuller explanation of every agent.
See `docs/results.md` for the actual result labels and example outputs.

## Project shape

- `src/pipeline/` contains the pipeline logic
- `src/graph/` connects the steps into a workflow
- `src/schemas/` defines the data shapes
- `tests/` holds the basic checks

## Goal

The system is not trying to prove legal wrongdoing. It is trying to give a clear, structured read on whether the company's own claims hold up against outside evidence.
