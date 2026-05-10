# M3 Writing Plan

## Purpose
This plan turns the tutor feedback into a practical writing guide for the M3 delivery.

The goal is to write a solid, academic, and concrete chapter 3, not to keep redesigning the prototype.

## What the tutor feedback means for M3

- The M2 part is acceptable and can be compressed later if page limits become an issue.
- The report must include in-text citations, not only a bibliography.
- The most relevant state-of-the-art topics are fact-checking, ESG analysis, and especially RAG design in CSR discourse analysis.
- M3 should be specific: exact documents, exact sources, exact method, and exact outputs.
- The chapter must describe what was actually implemented, not only what was planned.

## Target style

- Write in English.
- Use short, direct paragraphs.
- Keep the tone academic but readable.
- Explain decisions, not only actions.
- Avoid jargon when the idea can be said more simply.
- Use citations inside the text.

## Chapter 3 structure

### 3.1 Chapter introduction
Write 1 short paragraph explaining:
- this chapter describes the materials and methods of the project
- the work is a prototype for CSR / greenwashing-risk analysis
- the chapter explains the design, the implementation choices, and the produced outputs

### 3.2 Design and development of the work
Write 2-3 paragraphs covering:
- the overall design of the prototype
- the 9-agent pipeline
- the flow from PDFs to final report
- the role of the Streamlit interface, if you want to mention it as a presentation layer

Explain clearly:
- what the system receives as input
- what it produces as output
- why the pipeline is modular

### 3.3 Methodology chosen
Write 2-3 paragraphs explaining:
- why a multi-agent workflow was chosen
- why LangGraph was used to orchestrate the pipeline
- why local models were used for most stages
- why web retrieval is needed to check the company’s claims against external evidence
- why claims are prioritized instead of processing everything equally

You should explicitly justify the decisions:
- modularity
- transparency
- reproducibility
- explainability
- feasibility within the thesis timeline

### 3.4 Alternatives considered
Write 1-2 paragraphs describing alternatives such as:
- manual fact-checking only
- a single LLM pass for the whole task
- no external evidence retrieval
- pure retrieval without claim extraction

For each alternative, say briefly why it was not the best fit.

### 3.5 Data and sources used
Write 1-2 paragraphs describing:
- which documents were analyzed
- why Microsoft was used as the main baseline
- why other companies were also tested
- what kind of external sources were used for validation

Be concrete:
- report PDFs
- corporate disclosure documents
- external news or article sources used as evidence

### 3.6 Products obtained
Write 1 paragraph listing the concrete outputs of the system:
- extracted claims
- normalized claims
- prioritized claims
- generated queries
- search results
- extracted evidence passages
- reranked evidence
- claim assessments
- final report

If useful, mention the Streamlit interface as a front-end presentation layer.

### 3.7 Evaluation of the prototype
Write 1-2 paragraphs explaining:
- how the prototype was checked
- why the Microsoft run is the main example
- what the output shows about the workflow
- what kind of claims are better supported and which ones remain unresolved

### 3.8 Optional economic evaluation
Include this only if it can be justified clearly.

If included, mention:
- development cost
- maintenance cost
- computational cost
- practical benefit of automating the workflow

If it becomes forced or weak, omit it.

## What to emphasize in the text

- The project is a research prototype, not a full legal audit.
- The workflow was designed to make CSR claim analysis more systematic.
- The main contribution is the combination of claim extraction, external evidence retrieval, and final judgment.
- The Microsoft case study is the strongest example of the pipeline working end to end.
- RAG-style design in CSR discourse analysis is especially relevant to justify the method.

## What to avoid

- long internal IDs in the public narrative
- overly technical implementation logs
- repeated explanations of the same step
- unclear or ungrounded claims about what the system does
- writing the methodology as if it were only a list of tools

## How to connect M1, M2, and M3

- M1 defines the project and its objectives.
- M2 justifies the topic with the literature.
- M3 proves what has been built and what it produces.

The final memory should feel like a single coherent story.

## Practical writing order

1. Write chapter 3 introduction.
2. Write design and development.
3. Write methodology and alternatives.
4. Write data and sources.
5. Write products obtained.
6. Write evaluation / results.
7. Write limitations.
8. Write conclusion.
9. Review citations and bibliography.
10. Compress M2 if page count becomes too large.

## Suggested evidence to include in M3

- the Microsoft baseline run
- the current final summary output
- the counts of claims extracted / prioritized / analyzed
- the evidence relevance breakdown
- 2 or 3 representative claims
- the pipeline diagram
- the summary table

## Final recommendation

Write M3 as a concrete description of what the prototype actually does and what it produced.

Do not try to make it look bigger than it is.
Make it clear, justified, and academically readable.
