# Related-work candidates for paper v3 §1 (decision 17: published works only, no blog posts)

**PI ruling 2026-09-03 (verbatim):** "I think we don't need to cite blog posts, we engineered something and then
discovered those posts to find if we are doing good but it is not needed to cite them, we can cite published works
on which maybe those blogposts if they cited some."

## 1. What the five posts themselves cite (fetched 2026-09-03)
None of the five cites a peer-reviewed or arXiv work. Bowne-Anderson cites only his own posts, course and videos.
Böckeler (martinfowler.com) cites the LangChain post "The anatomy of an agent harness", Anthropic's engineering post
"Effective harnesses for long-running agents", OpenAI's "Harness engineering" page, Stripe's "Minions" post, and the
"approved fixtures" pattern page; her guides/sensors are defined as feedforward vs feedback controls ("Guides
(feedforward controls) - anticipate the agent's behaviour and aim to steer it before it acts"), and
computational/inferential as "deterministic and fast, run by the CPU" vs "semantic analysis, AI code review ...
non-deterministic". PuppyGraph cites LangChain and its own posts plus open-source harnesses (Claude Code, Codex CLI,
OpenHands, SWE-agent). LangChain cites only its own documentation and posts. Palantir's Ontology page cites nothing
external. **Consequence:** there is no scholarly lineage to inherit from the posts; the paper cites the published
literature directly, by claim.

## 2. Candidates, by the claim they would support (status: ADS bibcode = found in ADS 2026-09-03; DOI = resolves at
the publisher; PDF = local copy on disk — NONE yet; nothing enters the tex before PDF + quoted sentence)

| claim in the paper | work | id | status |
|---|---|---|---|
| reasoning loop with tools (§3.1) | Yao+ 2023, ReAct (ICLR 2023) | arXiv:2210.03629 | ADS 2022arXiv221003629Y |
| tool use learned/invoked by the model (§3.2) | Schick+ 2023, Toolformer (NeurIPS 2023) | arXiv:2302.04761 | ADS 2023arXiv230204761S |
| long context degrades; reduce/offload (§3.3) | Liu+ 2023, Lost in the Middle (TACL 2024) | arXiv:2307.03172 | ADS 2023arXiv230703172L |
| context management as an OS analogy (§3.3) | Packer+ 2023, MemGPT | arXiv:2310.08560 | ADS 2023arXiv231008560P |
| effective context size < advertised (§3.3) | Hsieh+ 2024, RULER | arXiv:2404.06654 | ADS 2024arXiv240406654H |
| self-verification is not independent verification (§3.3, §6) | Huang+ 2023, LLMs Cannot Self-Correct Reasoning Yet (ICLR 2024) | arXiv:2310.01798 | ADS 2023arXiv231001798H |
| the sensor idea's scholarly ancestors (§4) | Shinn+ 2023 Reflexion (NeurIPS 2023); Madaan+ 2023 Self-Refine (NeurIPS 2023) | arXiv:2303.11366; arXiv:2303.17651 | ADS both |
| guides = feedforward, sensors = feedback (§4, if we keep the control-theory reading) | Åström & Murray 2008, Feedback Systems (Princeton UP) | book | ADS 2008fsai.book.....A |
| agent architecture survey (§1) | Wang+ 2024, A survey on LLM-based autonomous agents (Front. Comput. Sci. 18, 186345) | doi:10.1007/s11704-024-40231-1 | DOI resolves; not in ADS |
| evaluation: benchmarks vs operational utility, cost (§1, §10) | Kapoor+ 2024, AI Agents That Matter (TMLR 2025) | arXiv:2407.01502 | ADS 2024arXiv240701502K |
| agent benchmarks (§1) | Liu+ 2023 AgentBench; Jimenez+ 2023 SWE-bench | arXiv:2308.03688; arXiv:2310.06770 | ADS both |
| scientific-agent evaluation (§1) | Chen+ 2024, ScienceAgentBench (ICLR 2025) | arXiv:2410.05080 | ADS 2024arXiv241005080C |
| autonomous science exemplars (§1) | Boiko+ 2023 (Nature 624, 570); Bran+ 2024 ChemCrow (Nat. Mach. Intell.); Lu+ 2024 The AI Scientist | 2023Natur.624..570B; doi:10.1038/s42256-024-00832-8; arXiv:2408.06292 | ADS / DOI / ADS |
| AI-scientist line already in v2 (§1) | Villaescusa-Navarro+ 2025, Denario | arXiv:2510.26887 | ADS 2025arXiv251026887V |
| LLM agents in astronomy (§1) — closest neighbours | Sun+ 2026, Mephisto (ApJS 285, 28); Sun+ 2024 multi-band galaxy agents; Laverick+ 2024 cmbagent | doi:10.3847/1538-4365/ae5d3a; arXiv:2409.14807; arXiv:2412.00431 | ADS all three |
| deep learning in astrophysics review (§1 context) | Ting 2026, ARA&A 64, 19 | doi:10.1146/annurev-astro-051024-021708 | ADS 2026ARA&A..64...19T |
| provenance-aware agents in scientific workflows (§3.4, §7) | Souza+ 2025 (SC-W 2025) | arXiv:2509.13978; doi:10.1145/3731599.3767582 | ADS + DOI |
| typed objects/links/actions = an ontology (§7) | Gruber 1993, A translation approach to portable ontology specifications (Knowl. Acquis. 5, 199) | doi:10.1006/knac.1993.1008 | DOI resolves (Elsevier); not in ADS |
| receipts / action events as provenance records (§3.4, §7) | W3C PROV-DM (2013 Recommendation) | https://www.w3.org/TR/prov-dm/ | standard, not a paper — AAS accepts standards with body, title, year, URL |

## 3. Not to cite
Anthropic engineering posts ("Building effective agents", "Effective context engineering", "Effective harnesses for
long-running agents"), OpenAI "Harness engineering", the LangChain/PuppyGraph/Substack posts, Palantir docs — all
blog/vendor material, excluded by decision 17. They stay in notes/HARNESS_COMPARISON_20260902.md as design references.

## 4. Next steps (paperedit protocol)
1. PI picks the rows that belong in §1 (my recommendation: ReAct, Huang+2023, Lost in the Middle, Wang+ survey,
   Kapoor+, ScienceAgentBench, Boiko+, Bran+, Lu+, Denario, Sun+ 2026 Mephisto, Laverick+, Souza+; the rest optional).
2. Fetch each PDF into paper_agentic/papers/<surname><year>.pdf (arXiv PDFs are open; Nature/NMI/ApJS via the
   library), quote the supporting sentence in the chng entry, and pull BibTeX from ADS by bibcode (never hand-written).
3. Only then the \cite enters §1.
