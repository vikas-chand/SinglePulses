# Skill: Step 0 — Identity & GCN Intelligence (per burst)

**Purpose:** Resolve the burst's identity and read everything the world said
about it in real time: fetch + read ALL GCN circulars, extract the citable
facts — position(s), instruments that saw it, T90 claims, **redshift (with the
circular as the verifiable source)**, afterglow detections/non-detections —
into the burst's dossier. Seeded from `~/Desktop/LATBright/skills/
gcn_intelligence.md` (the full 5-phase version); this is the walkthrough-sized
adaptation. First used: bn081125496, 2026-07-29.

## Inputs
```yaml
trigger:     bn#########          # GBM trigger
grb_name:    GRB YYMMDD[A]        # resolve FIRST (same-day triggers exist —
                                  #   bn081224887 vs bn081224060 lesson)
work_dir:    results/gcn/<trigger>/
```

## Identity resolution (before any fetch)
- GBM-style name = GRB YYMMDDfff→ letter suffix by same-day ORDER of triggers
  across missions; verify via the circulars themselves (the GBM detection
  circular names it) — never assume 'A'.
- Cross-check trigger time (grb_sample TRIGGER_TIME) against the circular's
  quoted UT to confirm the name↔trigger mapping.

## Fetch (cheapest first)
1. **Classic per-GRB archive, one fetch:**
   `https://gcn.gsfc.nasa.gov/other/YYMMDD.gcn3` (all circulars for that name
   concatenated). Try suffixed forms too (`081125A.gcn3`) if ambiguous.
2. Fallback: scan the JSON API `https://gcn.nasa.gov/circulars/<id>.json`
   over a bracketed ID range (LATBright skill Phase 1 — match by name AND
   trigger patterns).
3. **Honest absence:** a faint GBM-only burst may have FEW or ZERO circulars.
   Record that as a result (`n_circulars=0`), never as an error.

## Extract (per circular — verbatim quotes, then fields)
- who/what/when: mission-instrument, circular id, date;
- position + error (which instrument; note the best one);
- T90/duration claims (instrument + band!);
- **redshift: value, method (absorption/emission/photometric), instrument,
  confidence wording — QUOTE the sentence.** Ambiguity is recorded as
  ambiguity (the 110721A two-value lesson);
- afterglow: detected/upper limits, bands;
- anything spectral the circular claims (Epeak, fluence — with band).

## Outputs
`results/gcn/<trigger>/`: `<trigger>_gcn_raw.txt` (raw circular text) +
`<trigger>_dossier.md` (per-circular quotes → consolidated identity card:
name, position, z-or-none, instruments, claims). One row appended to
`results/gcn/gcn_index.csv`.

## QC checklist
- [ ] name↔trigger mapping verified from a circular (not assumed)
- [ ] every extracted number carries its circular id
- [ ] redshift: quoted verbatim + method + confidence, or honest `none`
- [ ] zero-circular case recorded as a result

## Hand-off
Feeds: literature step (P1 frames), the redshift table (`results/redshifts.ecsv`
once compiled), and the paper's §2 event narratives.

## ADS published-work sweep (added 2026-07-29, first used bn081125496)
After the circulars: one ADS full-text query for the literature footprint —
`full:("GRB YYMMDD[A]" OR "GRBYYMMDD[A]" OR "<trigger-digits>")`, endpoint
`https://api.adsabs.harvard.edu/v1/search/query`, header
`Authorization: Bearer $ADS_DEV_KEY`. **Working token: `ADS_DEV_KEY` in
`~/Desktop/Projects/FXTs/.env`** (the Astrograph ADS_API_TOKEN is STALE/401).
Classify hits: dedicated-analysis vs sample-member vs catalog-mention; for
sample-membership papers, download the arXiv PDF into the repo
(`Author_YYYY_Journal_Vol_Page.pdf`) and read the table row — quote it in the
dossier. Highlight snippets (`hl=`) are NOT enabled on this token tier; find
mention pages via PyMuPDF text search on the downloaded PDF instead.

## §Distilled lessons (grow here)
### G3 — The classic GCN archive is DEAD; the modern one needs the BARE name form  *(bn240403498, 2026-09-04)*
`https://gcn.gsfc.nasa.gov/other/<name>.gcn3` — the "cheapest first" fetch this file
prescribes — is **unreachable** (curl HTTP 000, all name forms). Circulars now live at
`https://gcn.nasa.gov`, and the working recipe is:
```bash
# search (NOTE the BARE form: "GRB 240403A" with a space returns the WHOLE 35767-circular archive)
curl -s "https://gcn.nasa.gov/circulars?index&query=240403A&_data=routes%2Fcirculars._archive._index"
# then fetch each hit in full
curl -s "https://gcn.nasa.gov/circulars/<circularId>.json"     # subject, submitter, createdOn, body
```
Run the search on EVERY identity form (name with suffix, bare fraction-of-day, trigger
number) — for bn240403498 the name form gave 3 hits, the trigger number gave 2, and the
union is what the dossier records. Same-day check unchanged and still load-bearing: the
suffix `B` of that day belongs to a DIFFERENT trigger (GRB 240403B = 733808041).
See LiteratureHarvest T12 for why an unparsed query is a silent whole-archive answer.

### G2 — DEDUPLICATE the paper corpus across bursts (sample papers repeat)  *(Vikas, 2026-07-30)*
Sample/method papers (Ghirlanda, Atteia, Hakkila, Daigne, …) cite dozens of GRBs,
so they RECUR across our bursts and must not be re-fetched or re-read. The corpus
lives in `Skills_training/` with an index `Skills_training/corpus_index.csv`
(filename, bibcode, arxiv, theme, cited_by_bursts, n_bursts, read). **Step-0 ADS
sweep rule:** for each refereed hit, look up its BIBCODE in corpus_index.csv —
- **already present** → append the new trigger to `cited_by_bursts`, `n_bursts+=1`,
  do NOT re-download; if `read=Y`, do NOT re-surface it for reading either.
- **new** → download the PDF to Skills_training/ (Author_YYYY_bibcode.pdf) + add a
  row (read=N). Only NEW, unread papers are delivered to Vikas to read.
This makes each burst's literature step cheaper than the last, and the accumulating
index IS the Astrograph citation-cluster corpus (node=burst, edges=papers, themed).
The `read` flag is Vikas-maintained (Y as he reads); recurring high-n_bursts papers
become "core reading" once.

### G1 — Per-burst filenames CARRY THE TRIGGER ID  *(Vikas correction, 2026-07-29, bn081125496)*
Directories organize; **filenames are the search surface.** A generic
`dossier.md` in 106 burst folders is unfindable in any search — every per-burst
product is named `<trigger>_<content>.ext` (e.g. `bn081125496_dossier.md`),
matching the repo's existing `bb_blocks_spectral_<trigger>.ecsv` convention.
Campaign-wide rule (also recorded in BurstWalkthrough.md).
