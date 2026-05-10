# M3 Draft

## 3 Materials and Methods

The project is a prototype for CSR disclosure analysis and greenwashing-risk assessment. It combines document reading, claim extraction, external evidence retrieval, and final judgment in a single workflow.

The aim is to make the analysis systematic, traceable, and easy to evaluate. The system starts from disclosure PDFs, extracts the most relevant claims, searches for external evidence, compares both sides, and produces a final report.

### 3.1 Workflow Overview
The prototype follows a sequential pipeline. Each stage receives one clear input and produces one clear output for the next stage.

`PDFs -> claims -> queries -> web search -> evidence fetch -> reranking -> evidence analysis -> final judgment -> report`

This structure keeps the process modular. It also makes the intermediate results easier to inspect, which is useful for debugging, explanation, and evaluation.

Figure 1 should show the full pipeline from the input documents to the final report.

### 3.2 Design Principles
The system is modular by design. Each component can be tested and adjusted separately, without changing the rest of the workflow.

Transparency is another core principle. The final judgment must be traceable back to the selected claims and the external sources used during analysis.

Reproducibility also matters. The implementation uses deterministic processing where possible, local execution for several stages, and cached intermediate results for expensive steps.

### 3.3 Technology Stack
The workflow is orchestrated with LangGraph. Local models are used for most processing stages, while web retrieval is used to contrast company claims with external evidence. A simple Streamlit interface is used to run and inspect the pipeline.

The stack was kept deliberately simple. The goal was not to build a large software product, but to keep the prototype understandable and feasible within the thesis scope.

Table 1 should summarize the main technologies, their role, and the reason for using each one.

### 3.4 Pipeline Components
The implementation is divided into nine agents. Table 2 should summarize them with their input, output, and purpose.

#### Agent 1. Document Loader
Reads the PDF files, extracts page-level text, and stores the document metadata needed later in the workflow.

#### Agent 2. Claim Extractor
Identifies concrete claims in the documents and keeps only those that can be checked against external evidence.

#### Agent 3. Claim Normalizer and Prioritizer
Groups similar claims, separates future-looking claims, and selects the claims most useful for the main analysis.

#### Agent 4. Query Generator
Converts the selected claims into search queries.

#### Agent 5. Web Search
Retrieves external sources that may support, challenge, or contextualize the claims.

#### Agent 6. Evidence Fetcher
Downloads the selected sources and extracts the relevant text from them.

#### Agent 7. Reranker
Ranks the retrieved evidence and keeps the most relevant items for each claim.

#### Agent 8. Evidence Analyzer
Compares each claim with its evidence and assigns a support label, a risk label, and a short explanation.

#### Agent 9. Judge and Final Report
Combines the claim-level assessments into the final report and produces the overall judgment.

### 3.5 Methodology Chosen
An agent-based workflow was the most suitable choice because the task is not a single classification problem. It requires document reading, claim selection, external retrieval, evidence ranking, claim analysis, and final synthesis.

LangGraph was used to connect the agents in a clear sequence. Local models were preferred for most steps to keep the prototype reproducible and inexpensive to run. Web retrieval was necessary because the project needs evidence outside the company documents in order to assess credibility.

Claims were prioritized instead of treating every statement equally. CSR reports often contain many statements, but only some are meaningful for the final judgment.

### 3.6 Alternatives Considered
Several simpler alternatives were possible.

A manual fact-checking process would have been more direct, but it would not scale well and would not produce a reproducible pipeline. A single LLM pass over the full report would have been easier to implement, but the result would have been less traceable and harder to debug.

Other options, such as extracting claims without external evidence or searching the web without claim normalization, were also less useful. They would not support a structured and explainable analysis.

### 3.7 Data and Materials Used
The main input data are corporate disclosure PDFs. Microsoft is the principal case study because it produced the most useful end-to-end run for the current prototype.

Other companies were also tested to check whether the pipeline behaves consistently when the document set changes. The external sources used for validation were public web pages and articles that could support or challenge the extracted claims.

### 3.8 Products Obtained
The implementation produced these outputs:

- extracted claims
- normalized claims
- prioritized claims
- generated queries
- search results
- extracted evidence passages
- reranked evidence
- claim assessments
- final report

The Streamlit interface is the presentation layer used to inspect the results and run the pipeline.

### 3.9 Ethical and Practical Considerations
The prototype works with public corporate documents and public external sources. The main case study does not require sensitive personal data. The work therefore raises limited ethical issues in its current form, although any future expansion to more sensitive data would need stronger ethical review.

### 3.10 Economic Evaluation of Work
Only include this subsection if it can be justified clearly. If used, it should mention development time, computational cost, maintenance cost, and the practical value of automating CSR claim analysis.

If the economic angle does not add much, it is better to keep it brief or omit it.

## 4 Results

### 4.1 Results Overview
The main results are based on the Microsoft run. This is the most complete example of the pipeline working from start to finish.

The results should show how many documents were processed, how many claims were extracted, how many were prioritized, and how many were analyzed in the final report.

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
This subsection should explain the meaning of the numbers. The main point is whether the company’s claims are mostly supported, partly supported, unresolved, or challenged by the external evidence.

The text here should be direct. It should say which claims are stronger, which claims are weaker, and what this tells us about the credibility of the company’s sustainability discourse.

### 4.4 Representative Claims
Include a small number of examples only.

For each example, write:

- what the company claims
- what the external evidence shows
- whether the claim is supported, partly supported, or unresolved
- why this matters for the final judgment

Keep this section concrete and short.

### 4.5 Final Verdict
State the overall verdict clearly. Use one of these patterns, depending on the evidence:

- the evidence suggests greenwashing risk
- the evidence is mixed
- the evidence is broadly supportive

Then explain why that verdict is justified.

### 4.6 Comparison Across Runs
If included, briefly mention that Microsoft was the strongest baseline and that other companies behaved differently depending on the document set and the available external evidence.

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
Explain what the prototype contributes. The main contribution is the combination of claim extraction, external evidence retrieval, and final judgment in a single workflow.

Also explain why the Microsoft case is important and what it shows about the usefulness of the approach.

### 6.2 Conclusion
End with a direct answer to the research question. State whether the available evidence suggests greenwashing risk, whether the evidence is mixed, or whether the company appears mostly credible.

Add one short sentence about confidence and one short sentence about the main limitation.

## Where to Put Figures and Tables

### Figure
Include one pipeline diagram in the methodology section. It should show the full flow from PDFs to final report.

### Table
Include one technology table in the methodology section and one summary table in the results section.

## Writing Rules
- use short paragraphs
- avoid internal IDs in the visible narrative
- avoid overcomplicated wording
- be direct and specific
- explain what the system does and what the results mean
