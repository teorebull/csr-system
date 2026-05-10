# Chapter 3. Materials and Methods

This chapter presents the prototype developed for CSR disclosure analysis and greenwashing-risk assessment. The implementation is available at `https://github.com/teorebull/csr-system`.

At a high level, the system reads corporate disclosure PDFs, extracts the claims that matter most, searches for external evidence, and turns the evidence pattern into a final judgment. The workflow is end to end: from input documents to a structured report.

The design follows a simple principle. The prototype should not only produce an answer, but also show how that answer is obtained. For that reason, every stage stores intermediate outputs that can be inspected separately.

## 3.1 System Architecture Overview

The system is organized as a sequential pipeline. Each stage solves one part of the problem and passes its output to the next stage.

`PDFs -> claims -> queries -> web search -> evidence fetch -> reranking -> evidence analysis -> final judgment -> report`

The problem it addresses is the gap between what a company says in its disclosures and what can be verified externally. CSR reports contain many statements, but only some of them are useful for assessing credibility. The system filters, ranks, and checks those statements against public sources.

Figure 1 should show the overall architecture and the flow between stages.

### 3.1.1 High-Level Architecture

The prototype is built as a modular analysis pipeline. The first part of the workflow deals with the internal documents, the middle part generates and executes external searches, and the last part converts evidence into a claim-level and document-level judgment.

The architecture is intentionally narrow. It focuses on one task: assessing whether the company’s sustainability discourse is supported, partially supported, unresolved, or challenged by external evidence.

The workflow is split into nine stages:

1. Document Loader: reads the disclosure PDFs, extracts page text, and stores document metadata for later stages.
2. Claim Extractor: identifies factual, checkable claims from the pages and removes statements that are too vague or purely rhetorical.
3. Claim Normalizer and Prioritizer: groups similar claims, removes future-looking material from the main analysis, and selects the most informative claims.
4. Query Generator: turns each selected claim into one or more search queries designed to find support, contradiction, or context.
5. Web Search: retrieves public sources that mention the same topic and filters out low-quality or company-controlled results.
6. Evidence Fetcher: downloads the selected sources and extracts the relevant text for analysis.
7. Reranker: scores the retrieved passages and keeps the most relevant evidence for each claim.
8. Evidence Analyzer: compares each claim with its evidence and assigns a support label, a relevance label, and a short justification.
9. Judge and Final Report: aggregates the claim-level assessments into a final report and produces the overall verdict.

### 3.1.2 Workflow Logic

The pipeline is designed to behave like a fact-checking workflow, but adapted to CSR discourse. It does not try to inspect every sentence equally. Instead, it concentrates on the claims that are most likely to affect the final evaluation.

This is important because sustainability reports mix hard facts, soft claims, future plans, and reputation-building statements. Treating them all the same would make the analysis noisy and less useful.

The system therefore separates the steps of extraction, prioritization, retrieval, and judgment. That separation makes the output easier to explain and easier to audit.

### 3.1.3 Pipeline Summary

Table 2 should summarize the nine stages with three columns: input, output, and purpose.

## 3.2 Design Principles

The system follows several design principles derived from software engineering practice and LLM-based application design.

1. Modularity: each component has a clear responsibility and a defined interface, so it can be tested or replaced independently.
2. Structured outputs: intermediate data is stored in consistent formats, which reduces ambiguity in downstream stages.
3. Transparency: the full evidence chain is preserved, from source documents to final verdict.
4. Progressive enhancement: if a stage produces weak output, the pipeline still continues with the best available evidence instead of failing completely.
5. Cost-conscious design: limits on claims, queries, and evidence items keep the workflow manageable.
6. Reproducibility: deterministic settings and cached artifacts reduce variation between runs.
7. Separation of concerns: classical processing handles filtering, ranking, and bookkeeping, while language models are reserved for tasks that require interpretation.

These principles are especially relevant in a thesis project, where the goal is not only to obtain results, but also to justify why the results are trustworthy.

## 3.3 Technology Stack

### 3.3.1 Core Technologies

Table 1 presents the core technologies employed in the implementation.

| Category | Technology | Version | Purpose |
| --- | --- | --- | --- |
| Language | Python | 3.12 | Core implementation |
| Workflow orchestration | LangGraph | >=0.2.0 | Agent orchestration |
| Validation | Pydantic | >=2.0.0 | Schema definitions and runtime validation |
| Web interface | Streamlit | >=1.0.0 | Result inspection and execution interface |
| Web search | ddgs | current | Public search retrieval |
| Content extraction | trafilatura, PyMuPDF | current | Article and PDF text extraction |
| Embeddings | sentence-transformers, torch | current | Semantic ranking support |
| Vector search | FAISS | current | Local retrieval sidecar |
| Data handling | pandas | >=2.3 | Tabular processing |

The implementation is deliberately lightweight. The project does not depend on a heavy external platform to run the main workflow.

### 3.3.2 Large Language Models

The prototype uses local language models for the main pipeline stages. This keeps the system self-contained and avoids dependence on external inference services during the thesis runs.

The codebase also supports configurable providers for the final report layer, but the main experimental workflow is designed to operate locally. That choice is consistent with the goals of reproducibility, cost control, and offline execution.

The local model is used because the task is mostly structured analysis rather than open-ended generation. The model needs to extract claims, rewrite queries, interpret evidence, and synthesize a verdict, but not produce long free-form text at every stage.

### 3.3.3 Latency Optimization Strategies

The pipeline includes several practical optimizations to keep execution time under control.

1. Model selection: lightweight local models are preferred for most steps because they are sufficient for structured extraction and analysis.
2. Output constraints: prompts request concise outputs so the model does not produce unnecessary text.
3. Content trimming: fetched web content is reduced to the relevant text before being sent to later stages.
4. Combined operations: each stage performs one focused task instead of multiple nested interactions.
5. Caching: repeated extraction and analysis steps reuse stored results when possible.
6. Separation of retrieval layers: external web evidence is kept separate from internal document recall so the two signals do not contaminate each other.

These strategies reduce latency without changing the basic logic of the workflow.

## 3.4 Pipeline Components

The implementation is divided into nine agents. Each one corresponds to a specific stage in the end-to-end process.

### 3.4.1 Document Loader

The Document Loader reads the corporate disclosure PDFs and extracts page-level text. It also stores document metadata so later stages can preserve provenance.

This component solves the first practical problem in the pipeline: turning static PDF reports into text that can be analyzed systematically.

### 3.4.2 Claim Extractor

The Claim Extractor identifies factual and verifiable statements in the disclosure pages. Its role is not to summarize the document, but to isolate the claims that can later be checked against external evidence.

This component is essential because CSR reports often contain a mix of measurable claims, narrative statements, and future commitments. Only the first category is directly useful for credibility analysis.

### 3.4.3 Claim Normalizer and Prioritizer

The Claim Normalizer and Prioritizer groups similar claims, removes duplicates, separates future-oriented claims, and ranks the remaining claims by usefulness.

The purpose is to keep the final analysis focused. A report may contain many repeated sustainability statements, but not all of them deserve equal attention.

### 3.4.4 Query Generator

The Query Generator transforms each selected claim into a set of search queries. The queries are diversified so that the retrieval step can find direct support, alternative wording, critical context, or contradictory evidence.

This stage makes the pipeline more robust. If one search formulation fails, another can still surface relevant sources.

### 3.4.5 Web Search

The Web Search component retrieves public sources that mention the same topic as the claim. It excludes company-controlled domains and filters weak sources so that the evidence pool is not dominated by self-referential material.

This component provides the external comparison layer needed for the thesis. Without it, the system would only restate the company’s own discourse.

### 3.4.6 Evidence Fetcher

The Evidence Fetcher opens the selected sources and extracts the relevant text from each one. It uses article extraction for HTML pages and PDF extraction for documents.

This step converts search results into analyzable evidence. It is the bridge between retrieval and interpretation.

### 3.4.7 Reranker

The Reranker scores the retrieved passages and keeps the most relevant ones for each claim. It combines semantic similarity with additional signals such as source quality and query type.

This reduces noise in the evidence set and increases the chance that the analyzer receives the most useful material.

### 3.4.8 Evidence Analyzer

The Evidence Analyzer compares each claim with its supporting or conflicting evidence. It assigns a support label, an evidence relevance label, and a short explanation.

This stage turns retrieval into judgment. It is where the system moves from “what was found” to “what the evidence means.”

### 3.4.9 Judge and Final Report

The Judge and Final Report component aggregates the claim-level outputs into a final company-level summary. It counts the labels, highlights the most relevant patterns, and produces the final verdict.

This final stage is the thesis-facing output of the system. It is the point where the workflow becomes a readable result rather than a set of intermediate artifacts.

## 3.5 Methodology Chosen

An agent-based workflow was the most suitable choice because the task is not a single prediction problem. It requires document reading, claim selection, evidence retrieval, ranking, interpretation, and synthesis.

The methodology also reflects the structure of the research question. The project asks whether CSR discourse is credible when compared with external sources, so the system must first isolate claims and then verify them in stages.

Claims are prioritized instead of processed equally because the report contains a large number of statements with different importance. The method therefore focuses on the claims that are most likely to influence the final judgment.

## 3.6 Alternatives Considered

Several simpler alternatives were considered.

A manual fact-checking workflow would have been easier to explain, but it would not scale and would not produce a reproducible system.

A single LLM pass over the whole report would have been simpler to implement, but it would be less traceable and harder to debug.

Claim extraction without external evidence would not support a credibility assessment, and web search without claim normalization would produce too much noise.

The chosen design is more complex than these alternatives, but it is better aligned with the goal of producing an explainable end-to-end method.

## 3.7 Data and Materials Used

The main input data are corporate disclosure PDFs. Microsoft is the principal case study because it produced the most complete and useful end-to-end run.

Other companies were also tested to check whether the pipeline behaves consistently across different document sets. The external evidence came from public web pages, news articles, and public documents that could support, challenge, or contextualize the extracted claims.

The project also includes a local retrieval sidecar based on embeddings and FAISS, but this is kept separate from the external web-evidence workflow.

## 3.8 Products Obtained

The implementation produces the following outputs:

- extracted claims
- normalized claims
- prioritized claims
- generated queries
- search results
- extracted evidence passages
- reranked evidence
- claim assessments
- final report

The Streamlit interface is used as a presentation layer to inspect these outputs and execute the pipeline.

## 3.9 Ethical and Practical Considerations

The prototype works with public corporate documents and public external sources. It does not require sensitive personal data for the main case study.

The practical limitation is that the system is not an audit tool. It is a research prototype for assessing discourse credibility, not a legal or regulatory determination.

## 4 Results

### 4.1 Results Overview

The main results are based on the Microsoft run. This is the clearest example of the pipeline working end to end.

The results section should report how many documents were processed, how many claims were extracted, how many were prioritized, and how many were analyzed in the final report.

### 4.2 Quantitative Results

Insert the main numbers here:

- documents processed
- claims extracted
- claims normalized
- claims prioritized
- claims analyzed
- direct evidence count
- indirect evidence count
- background evidence count
- unrelated evidence count

It is useful to present these values in a table.

### 4.3 Qualitative Results

This subsection should explain what the numbers mean. The main question is whether the company’s claims are mostly supported, partly supported, unresolved, or challenged by the external evidence.

The discussion should stay concrete. It should identify which claims are stronger, which are weaker, and what this suggests about the credibility of the company’s sustainability discourse.

### 4.4 Representative Claims

Include only a small number of examples.

For each example, write:

- what the company claims
- what the external evidence shows
- whether the claim is supported, partly supported, or unresolved
- why this matters for the final judgment

### 4.5 Final Verdict

State the overall verdict clearly. Use one of these patterns, depending on the evidence:

- the evidence suggests greenwashing risk
- the evidence is mixed
- the evidence is broadly supportive

Then explain why that verdict is justified.

### 4.6 Comparison Across Runs

If included, mention briefly that Microsoft was the strongest baseline and that other companies behaved differently depending on the document set and the available external evidence.

## 5 Limitations

The main limitations are the following:

- some claims are repetitive or very metric-heavy
- some claims are difficult to verify externally
- some disclosures are future-oriented
- the result depends strongly on the selected document set
- the prototype is not a full audit tool

This section should stay short and honest.

## 6 Discussion and Conclusion

### 6.1 Discussion

The main contribution of the prototype is the combination of claim extraction, external evidence retrieval, and final judgment in a single workflow.

The Microsoft case is important because it shows that the system can move from raw disclosure PDFs to a defensible evidence-based summary.

### 6.2 Conclusion

End with a direct answer to the research question. State whether the available evidence suggests greenwashing risk, whether the evidence is mixed, or whether the company appears mostly credible.

Add one short sentence about confidence and one short sentence about the main limitation.

## Where to Put Figures and Tables

### Figure

Include one pipeline diagram in the methodology section. It should show the full flow from PDFs to final report.

### Tables

Include one technology table in the methodology section and one summary table in the results section.

## Writing Rules

- use short paragraphs
- avoid internal IDs in the visible narrative
- avoid overcomplicated wording
- be direct and specific
- explain what the system does and what the results mean
