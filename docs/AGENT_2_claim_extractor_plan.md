# Agent 2 - Claim Extractor plan

## Goal

Take the page-level CSV from Agent 1 and create a new CSV with extracted claims.

## Input

- `pages.csv` from Agent 1

## Output

- `claims.csv`

Minimum columns:
- `claim_id`
- `document_name`
- `page_number`
- `claim_text`
- `claim_type`
- `topic`
- `is_future`
- `is_verifiable`
- `confidence`
- `source_excerpt`

## Flow

1. read the page CSV
2. send each useful page to the LLM
3. ask for structured JSON
4. collect the claims returned for that page
5. append those claims to an in-memory table / list of rows
6. after all page calls are finished, save everything in a CSV

In other words, the pipeline for this agent is:

`pages.csv -> one LLM call per page -> claim rows -> one final claims.csv`

## Why this is reasonable

Yes, this is the right next step.

The first agent leaves the document in a clean, page-level format.
The second agent can now focus only on extracting claims.

This is useful because each claim keeps a page reference from the beginning.

## Local model recommendation for 16 GB VRAM

Best first option:
- `qwen2.5:7b-instruct`

Why:
- good instruction following
- usually better than many small models at structured extraction
- realistic on 16 GB VRAM, especially quantized

Other reasonable options:
- `llama3.1:8b-instruct`
- `mistral:7b-instruct`

My recommendation:
1. start with `qwen2.5:7b-instruct`
2. if it behaves badly, try `llama3.1:8b-instruct`

## Current implementation choice

The script uses a local `Ollama` endpoint because it is simple.

If you use another local setup later, you only need to change:
- model name
- LLM call function

## Prompt engineering strategy

The first version of the extractor was too broad and produced noise.

To reduce that noise, the prompt was tightened in several ways:

1. it now defines a claim more strictly as a specific, official, externally checkable statement
2. it explicitly excludes vague marketing language, titles, footnotes, isolated keywords, and generic sustainability context
3. it tells the model to be conservative: if unsure, do not extract
4. it requires `source_excerpt` to be copied exactly from the page text
5. it asks the model to output `is_verifiable` and `confidence`

This is important because prompt engineering helps narrow the answer space.

There is always some risk of hallucinations or borderline claims when using an LLM, but a stricter prompt reduces that risk and makes post-filtering much easier.

The current logic also filters low-quality claims after extraction.

## Script created

- `scripts/agent_2/extract_claims_with_llm.py`

## What to validate after running it

1. are the extracted claims really official statements?
2. are they broader than just numeric claims?
3. are `is_future = true` cases being detected?
4. are weak or vague claims being filtered out?
5. is `claim_type` useful?
6. is `topic` useful or too noisy?
7. is the `source_excerpt` enough to trace the origin?
8. do `is_verifiable` and `confidence` help reduce noise?

## Current claim output fields

The current CSV should contain:

- `claim_id`
- `document_name`
- `page_number`
- `claim_text`
- `claim_type`
- `topic`
- `is_future`
- `is_verifiable`
- `confidence`
- `source_excerpt`

## Storage recommendation

For the MVP, storing claims in a `CSV` is a good choice.

Why CSV is good now:
- easy to inspect manually
- easy to open in Excel or pandas
- easy to debug
- enough for one company and one document pilot

When CSV may stop being enough:
- many companies
- many documents
- repeated runs with different models
- need to preserve nested metadata or versioned outputs

Practical recommendation:
- for now, keep `claims.csv`
- later, if the project grows, also save a `JSON` version or move to SQLite

So the short answer is:
- `CSV` is the right storage format now
- `JSON` or `SQLite` can come later if needed
