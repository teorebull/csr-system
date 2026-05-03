# Final Summary - Microsoft

## Overview
- Total claims analyzed: 14
- Claims excluded from main analysis: 21
- Future claims excluded: 3

## Run Metadata
- Generated at UTC: 2026-05-03T15:20:28.037491+00:00
- Pipeline mode: fast
- Documents processed: 1
- Document IDs: doc_1_2025-microsoft-environmental-data-fact-sheet-pdf
- Document names: 2025 Microsoft Environmental Data Fact Sheet
- Agent 2 model: qwen2.5:14b
- Agent 4 model: mistral-nemo:latest
- Agent 7 embedding model: sentence-transformers/all-MiniLM-L6-v2
- Agent 8 model: qwen2.5:14b
- Agent 9 analysis mode: deterministic_fallback
- Queries generated: 70
- Evidence candidates: 42
- Ranked evidence rows: 38
- Agent 2 cached pages: 18
- Agent 8 cached assessments: 173

## Label Counts
- SUPPORTED: 4
- PARTIALLY_SUPPORTED: 2
- UNVERIFIED: 8
- PARTIALLY_CONTRADICTED: 0
- CONTRADICTED: 0

## Greenwashing Risk Counts
- LOW: 2
- MEDIUM: 11
- HIGH: 0
- UNCLEAR: 1

## Evidence Relevance Counts
- DIRECT: 6
- INDIRECT: 4
- BACKGROUND: 3
- UNRELATED: 1

## Final Conclusion
The analyzed discourse is weakly verified by external evidence. A large share of prioritized claims remain unverified, which suggests limited external confirmation rather than direct falsification.

## Analytical Assessment
The main analysis covers 14 prioritized claims. Most claims are not fully confirmed: 10 are either partially supported or unverified.
Greenwashing risk is concentrated in 11 claims marked as medium or high risk.
Evidence relevance is direct or indirect for 10 claim(s), while 4 claim(s) rely on background or unrelated evidence.
The strongest concern is not direct contradiction, but incomplete substantiation and contextual risk: several claims are factually plausible while the evidence raises concerns about emissions growth, accounting choices, renewable electricity matching, offsets, supplier emissions, or water impacts.

## Main Risk Patterns
- GHG emissions: 7 claim(s), labels {'PARTIALLY_SUPPORTED': 1, 'SUPPORTED': 2, 'UNVERIFIED': 4}, risks {'MEDIUM': 7}.
  Example: [PARTIALLY_SUPPORTED | Risk: MEDIUM] Microsoft has maintained its commitment to carbon neutrality while progressing towards a carbon negative goal.
  Reason: There are concerns about rising emissions due to data center builds for AI systems, which may indicate challenges in achieving their stated goals despite ongoing efforts.
  Example: [SUPPORTED | Risk: MEDIUM] Microsoft defines carbon neutrality as matching the emissions within the carbon neutrality boundary with an equivalent amount of carbon credits.
  Reason: The evidence suggests that while Microsoft is committed to achieving net zero through various measures, there are uncertainties and challenges in meeting the ambitious goals, raising some greenwashing risks if not properly managed or transparently reported.
- Water and data centers: 2 claim(s), labels {'UNVERIFIED': 2}, risks {'UNCLEAR': 1, 'MEDIUM': 1}.
  Example: [UNVERIFIED | Risk: MEDIUM] Microsoft reports that its total water consumption from areas with water stress was 2,423 ML (42% of total water consumption) in FY24.
  Reason: The evidence raises concerns about Microsoft's water usage practices, especially regarding the consumption of vast amounts of water from already water-scarce regions, which could indicate potential greenwashing risks if the reported reductions do not address this issue adequately.
- Renewable electricity and Scope 2 accounting: 3 claim(s), labels {'SUPPORTED': 1, 'PARTIALLY_SUPPORTED': 1, 'UNVERIFIED': 1}, risks {'LOW': 1, 'MEDIUM': 2}.
  Example: [PARTIALLY_SUPPORTED | Risk: MEDIUM] Microsoft procures renewable energy from on-site generation, unbundled EACs, PPAs, and green power products.
  Reason: While the claim is partially supported by direct evidence, there are important limitations regarding specific procurement methods like on-site generation and green power products. The evidence raises concerns about whether Microsoft's renewable energy purchases directly impact local grids.
  Example: [UNVERIFIED | Risk: MEDIUM] Microsoft reports that its percentage of direct renewable electricity is 78% for FY24.
  Reason: The evidence suggests that while Microsoft has contracted significant amounts of renewable electricity, there are concerns over whether this is reflected in a high percentage of direct renewables, given increased energy intensity and overall consumption. This raises caution about the claim's accuracy without direct confirmation.
- Carbon neutrality and removals: 2 claim(s), labels {'UNVERIFIED': 1, 'SUPPORTED': 1}, risks {'MEDIUM': 1, 'LOW': 1}.
  Example: [UNVERIFIED | Risk: MEDIUM] Microsoft only applies carbon removal credits against its carbon neutral boundary if they have been retired and delivered.
  Reason: There is a MEDIUM greenwashing risk as there is insufficient direct evidence to confirm whether Microsoft applies carbon removal credits only if they have been retired and delivered within their carbon neutral boundary. Additional context about the company’s specific policy on this matter would be needed for further verification.

## Evidence Limitations
- 1 claim(s) did not have a selected evidence URL in the final assessment.
- 1 claim(s) had unclear greenwashing risk, usually because the evidence was missing, weak, or not specific enough.
- 4 claim(s) were assessed with background or unrelated evidence, so their risk interpretation should be treated cautiously.
- The report should be read as an evidence-driven screening, not a definitive audit. Claims with weak evidence need targeted retrieval before drawing strong conclusions.

## Overall Interpretation
The analyzed discourse is weakly verified by external evidence. A large share of prioritized claims remain unverified, which suggests limited external confirmation rather than direct falsification.

## Claim Summary
- [PARTIALLY_SUPPORTED | Risk: MEDIUM | Evidence: DIRECT] Microsoft has maintained its commitment to carbon neutrality while progressing towards a carbon negative goal.
  Evidence: https://www.datacenterdynamics.com/en/news/microsoft-emissions-up-23-since-2020-blames-ai-data-centers/
  Risk reasoning: There are concerns about rising emissions due to data center builds for AI systems, which may indicate challenges in achieving their stated goals despite ongoing efforts.
- [SUPPORTED | Risk: MEDIUM | Evidence: DIRECT] Microsoft defines carbon neutrality as matching the emissions within the carbon neutrality boundary with an equivalent amount of carbon credits.
  Evidence: https://sdgs.un.org/partnerships/carbon-neutrality
  Risk reasoning: The evidence suggests that while Microsoft is committed to achieving net zero through various measures, there are uncertainties and challenges in meeting the ambitious goals, raising some greenwashing risks if not properly managed or transparently reported.
- [UNVERIFIED | Risk: MEDIUM | Evidence: BACKGROUND] Microsoft estimates emissions for suppliers who submitted data by multiplying their response-derived factor by the annual spend with the supplier.
  Evidence: https://trellis.net/article/report-climate-goals-at-amazon-apple-google-meta-and-microsoft-have-lost-their-meaning/
  Risk reasoning: While there is no direct contradiction, the evidence suggests that companies like Microsoft face scrutiny over their greenhouse gas accounting practices and methods, which raises concerns about whether their reported practices fully align with accurate environmental impact assessments. This creates a medium risk of greenwashing due to potential methodological issues not being fully addressed.
- [UNVERIFIED | Risk: MEDIUM | Evidence: BACKGROUND] Microsoft has maintained carbon neutrality every year since FY13.
  Evidence: https://carboncredits.com/microsoft-signs-groundbreaking-7mt-carbon-credits-deal-with-u-s-based-chestnut-carbon/
  Risk reasoning: Although the evidence is not directly relevant to verifying Microsoft's carbon neutrality status each year since FY13, it provides context regarding the company’s involvement in carbon credits. This raises a medium-level risk of greenwashing if there are discrepancies between such projects and actual carbon emissions reported by the company.
- [UNVERIFIED | Risk: UNCLEAR | Evidence: UNRELATED] Microsoft’s water inventory includes withdrawal, consumption, and discharge volumes associated with assets under our operational control.
  Evidence: 
  Risk reasoning: Since there is no relevant evidence concerning Microsoft’s specific claim about their water inventory, it is impossible to assess greenwashing risk based on this data alone.
- [SUPPORTED | Risk: LOW | Evidence: DIRECT] Microsoft procures enough renewable electricity to match 100% of our global electricity consumption.
  Evidence: https://parliamentnews.co.uk/microsoft-renewable-energy-strategy-2026
  Risk reasoning: The evidence does not raise concerns or limitations regarding the claim.
- [UNVERIFIED | Risk: MEDIUM | Evidence: INDIRECT] Microsoft only applies carbon removal credits against its carbon neutral boundary if they have been retired and delivered.
  Evidence: https://www.datacenterdynamics.com/en/news/microsoft-to-purchase-44000-tons-of-carbon-removal-credits-from-biochar-firm-carba/
  Risk reasoning: There is a MEDIUM greenwashing risk as there is insufficient direct evidence to confirm whether Microsoft applies carbon removal credits only if they have been retired and delivered within their carbon neutral boundary. Additional context about the company’s specific policy on this matter would be needed for further verification.
- [SUPPORTED | Risk: LOW | Evidence: DIRECT] We have published the criteria we use to help ensure that the carbon removal credits that we contract are high quality: Microsoft Criteria for High-Quality Carbon Dioxide Removal.
  Evidence: https://www.esgdive.com/news/microsoft-buys-ocean-based-carbon-removal-credits-ebb-carbon/731230/
  Risk reasoning: No significant concerns or contradictions are raised regarding the claim's accuracy. The evidence supports the existence of the company’s criteria for high-quality carbon dioxide removal.
- [PARTIALLY_SUPPORTED | Risk: MEDIUM | Evidence: DIRECT] Microsoft procures renewable energy from on-site generation, unbundled EACs, PPAs, and green power products.
  Evidence: https://trellis.net/article/microsoft-signs-its-biggest-renewable-energy-contract-yet/
  Risk reasoning: While the claim is partially supported by direct evidence, there are important limitations regarding specific procurement methods like on-site generation and green power products. The evidence raises concerns about whether Microsoft's renewable energy purchases directly impact local grids.
- [UNVERIFIED | Risk: MEDIUM | Evidence: BACKGROUND] This carbon inventory reflects what is in scope for our carbon negative commitment.
  Evidence: https://www.readkong.com/page/the-microsoft-carbon-fee-theory-practice-6775317
  Risk reasoning: The evidence raises concerns about whether Microsoft’s commitment to becoming carbon negative might be compromised due to its focus on AI, which could impact its reported emissions and methodologies. However, this is indirect and does not specifically address the claim's methodology or scope issues.
- [UNVERIFIED | Risk: MEDIUM | Evidence: INDIRECT] Microsoft reports that its percentage of direct renewable electricity is 78% for FY24.
  Evidence: https://www.latitudemedia.com/news/microsoft-reveals-the-energy-impact-of-artificial-intelligence/
  Risk reasoning: The evidence suggests that while Microsoft has contracted significant amounts of renewable electricity, there are concerns over whether this is reflected in a high percentage of direct renewables, given increased energy intensity and overall consumption. This raises caution about the claim's accuracy without direct confirmation.
- [SUPPORTED | Risk: MEDIUM | Evidence: DIRECT] Microsoft calculates and reports Scope 3 emissions for all relevant categories.
  Evidence: https://trellis.net/article/microsoft-launches-initiative-counter-30-rise-scope-3-emissions-2020/
  Risk reasoning: While the claim is supported by the evidence, there is a medium risk due to the increasing trend in Scope 3 emissions despite efforts to reduce them.
- [UNVERIFIED | Risk: MEDIUM | Evidence: INDIRECT] Microsoft uses an operational control approach for setting organizational boundaries and for corporate reporting of GHG emissions, energy, water, waste and circularity, and ecosystem metrics.
  Evidence: https://jdmeier.com/sustainability-at-microsoft/
  Risk reasoning: The lack of detailed information about the exact methods used by Microsoft raises a concern that there may be discrepancies or gaps in transparency regarding their reporting approach.
- [UNVERIFIED | Risk: MEDIUM | Evidence: INDIRECT] Microsoft reports that its total water consumption from areas with water stress was 2,423 ML (42% of total water consumption) in FY24.
  Evidence: https://www.projectcensored.org/big-tech-data-centers-deplete-water/
  Risk reasoning: The evidence raises concerns about Microsoft's water usage practices, especially regarding the consumption of vast amounts of water from already water-scarce regions, which could indicate potential greenwashing risks if the reported reductions do not address this issue adequately.

## Claims Excluded From Main Analysis
- [LOW | meta_or_reporting_claim_not_substantive] As part of Microsoft’s commitment to disclose information about our environmental footprint, the following sections are a compilation of environmental metrics across greenhouse gas (GHG) emissions, energy, water, waste and circularity, and land.
- [MEDIUM | medium_priority_excluded_from_main_analysis] Microsoft's Scope 1 and 2 (market-based) emissions for FY24 are 402,600 metric tons of CO2e.
- [HIGH | below_main_analysis_priority_cap] Microsoft's Scope 3 emissions for FY24 are 15,140,000 metric tons of CO2e.
- [MEDIUM | medium_priority_excluded_from_main_analysis] Microsoft's total emissions (Scope 1 + 2 + 3) for FY24 are 15,543,000 metric tons of CO2e.
- [HIGH | below_main_analysis_priority_cap] Microsoft reports that its percentage of renewable electricity consumption is 100% for FY20, FY21, FY22, FY23, and FY24.
- [HIGH | below_main_analysis_priority_cap] Microsoft reports that its total water withdrawals from areas with water stress were 4,747 ML (46% of total water withdrawals) in FY24.
- [HIGH | below_main_analysis_priority_cap] Microsoft reports that its total water discharges to areas with water stress were 2,323 ML (51% of total water discharges) in FY24.
- [MEDIUM | medium_priority_excluded_from_main_analysis] Microsoft has identified partnerships through two leading land protection organizations, the National Fish and Wildlife Foundation (NFWF) within the United States and The Nature Conservancy (TNC) globally.
- [MEDIUM | medium_priority_excluded_from_main_analysis] A data-informed approach using TNC’s Last Chance Ecosystem Framework and NFWF’s National Landscape Conservation Framework is used to identify ecosystems most at risk.
- [HIGH | below_main_analysis_priority_cap] Within each of the two partnerships, specific organizations will hold conservation easements or own protected land.
- [MEDIUM | medium_priority_excluded_from_main_analysis] Microsoft’s GHG inventory includes five of the seven GHGs addressed by the Kyoto Protocol—carbon dioxide (CO2), methane (CH4), nitrous oxide (N O), hydrofluorocarbons (HFCs), and sulfur hexafluoride (SF6).
- [HIGH | below_main_analysis_priority_cap] Purchased EACs include renewable energy certificates (RECs) (Green-e certified), guarantees of origin (GOs), renewable energy GOs (REGOs), International RECs (I-RECs), Tradable Instruments for Global Renewables (TIGRs), New Zealand Energy Certificate System (NZECS) certificates, J-Credits, Non-Fossil Fuel Certificates (NFCs), large-scale generation certificates (LGC), Green Electricity Certificates (GECs), Taiwan Renewable Energy Certificates (T-RECs), and PowerPlus.
- [HIGH | below_main_analysis_priority_cap] To calculate Scope 2 emissions from a market-based approach, Microsoft captures the impact across all renewable electricity purchases and matches that with the markets where we operate.
- [MEDIUM | medium_priority_excluded_from_main_analysis] We include operational waste, product packaging recyclability, and single-use plastics in our waste and circularity metrics.
- [MEDIUM | medium_priority_excluded_from_main_analysis] For product packaging, both recyclability and single-use plastics metrics cover all Microsoft hardware packaging (retail and commercial) and consumer software packaging of the products available to be sold during the reporting year.
- [MEDIUM | medium_priority_excluded_from_main_analysis] We use primary data to calculate emissions for both Scope 1 and Scope 2 emissions. Where primary data is not available, we use estimates.
- [MEDIUM | medium_priority_excluded_from_main_analysis] Microsoft uses the 100-year Intergovernmental Panel on Climate Change (IPCC) Fourth Assessment Report for global warming potential values.
- [MEDIUM | medium_priority_excluded_from_main_analysis] In FY23, Microsoft started using LCAs to calculate the emissions associated with the manufacture of devices that we sold during the reporting year.
- [MEDIUM | medium_priority_excluded_from_main_analysis] Microsoft used Makersite, a cloud-based tool with AI and third-party datasets, and other internal software engineering systems to automate and scale the modeling of complex electronic products.
- [MEDIUM | medium_priority_excluded_from_main_analysis] Global warming potentials (GWPs) are from the Intergovernmental Panel on Climate Change (IPCC) Fourth Assessment Report (AR4), 100-year average.
- [MEDIUM | medium_priority_excluded_from_main_analysis] Corporate-wide expense data for all company divisions is obtained from the finance department.