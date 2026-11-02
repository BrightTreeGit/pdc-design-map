# AI workflow and model strategy for Bright Tree and the permaculture platform (25 Oct 2026)

Brett's question: how to use the brighttreewellness Claude subscription (with Notion) and the personal Pro subscription (with Google), when Opus, Fable or a deeper tier makes sense, how to factor in a LiteLLM backend, and how to spend unused Gemini tokens without fragmenting the long-term understanding of the work. The bias requested: err toward the more capable model when it is likely to give a more refined answer and a system that is cheaper to extend later.

Companion pages: `tools/knowledge-engine-and-reports-2026-10-25.md` (the retrieval and caching design), `tools/strategy-and-pipeline-2026-10-24.md` (pipeline, gates, funding), `app/00-idea-register.md` (A85 knowledge engine).

---

## 0. The short version

1. **Knowledge lives in files, not chats.** The Permicuture project docs, the GitHub repo and Notion are the system of record. Both subscriptions and both AI vendors read from and write to those; nothing important is left in a chat history on either account.
2. **One owner per kind of fact.** Notion for people, dates, money and tasks; the design map and repo for anything with a location or code; project docs for knowledge and method; Drive for raw files. This is the existing rule from the pipeline paper and it is what stops the "split brain".
3. **Default to Opus 5.5 for design, synthesis and code. Escalate to Fable 5.1 for foundations and audits. Use Sonnet 5.5 for bulk, well-specified work.** Don't build on a model you can't name in the price list.
4. **Gemini is the ingestion and second-opinion engine**, not a second brain. It turns Google-held material (Gmail, Drive, photos, long PDFs) into structured, cited artefacts that go into the shared library, and it red-teams Claude's designs. It never edits the ontology, the schemas or the method.
5. **Precision comes from method more than from model**: structured facts, explicit constraint ledgers, generate-then-audit with a different model, citations on every claim, and an evaluation set. These make every model better and let you compare them honestly.

---

## 1. What Gemini got right, what to check, what to drop

| Gemini's point | Verdict | Why |
|---|---|---|
| Two layers: Google account for ingestion, Bright Tree account for operations with Notion as source of truth | **Keep** | Matches how the work already runs; Notion for state, map for location, files in Drive |
| Subscriptions don't power LiteLLM scripts; the API needs separate billed keys | **Keep** | Correct. Anthropic Console and Google AI Studio keys are billed per token, separate from the $20 plans |
| Ensemble mode (both vendors answer, a third pass synthesises) for foundational decisions | **Keep, with a change** | Good for architecture and design reviews. Make the synthesis step an *audit* (find contradictions, missing constraints, unverified claims) rather than a merge, so it doesn't average two answers into a softer one |
| "Argon tier (ultra-deep reasoning)" | **Drop until verified** | I know of no Anthropic model or tier called Argon. The current top public model is Claude Fable 5.1; Claude Mythos Preview exists above it but is not publicly available (Project Glasswing). Don't design routing around a name that may not exist; check docs.claude.com |
| Fable cache reads at $0.25/M vs Opus $0.50/M; "140K-token crossover" | **Verify before relying on it** | I can't confirm these prices. The principle (cache a large stable context and pick the model whose cached-read price is lowest for frontier quality) is right; the numbers must come from the live price list |
| Gemini 3.1 Pro with a 2M context | **Verify** | I can't confirm the version or window. Long context is Gemini's real strength either way; treat the exact figure as something to check |
| Drop Flash and Haiku entirely; Sonnet only as a worker | **Partly** | For design and architecture, yes. For tagging, extraction, translation drafts, classification and evaluation runs, a small model with a good prompt is more accurate per dollar and keeps the big models for what needs them. The knowledge-engine paper's routing stands |
| Master context compiled once and updated monthly | **Keep, but version it** | Store it in the repo with a hash, so cached prompts invalidate only when it changes, and every answer records which version it ran against |

---

## 2. Accounts and ecosystems

### 2.1 Roles

| | brighttreewellness@gmail.com (Claude, Notion) | bkotelko@gmail.com (Claude Pro, Google AI Pro) |
|---|---|---|
| **What it holds** | Bright Tree Pty Ltd, the PDC network, the platform: the Permicuture project, Notion HQ, the design map, Claude memory about the business | Personal history: Gmail, Drive, Photos, Maps, Calendar; personal Claude memory |
| **Use it for** | Design, knowledge base, reports, Notion operations, code, anything shared with the group or a client | Reading and extracting from personal Google data (quotes, invoices, contractor threads, old photos, calendar), personal matters, experiments |
| **Writes go to** | Project docs, repo, Notion, the shared Drive folder | The shared Drive folder only (as structured artefacts), never a private chat as the only copy |
| **Memory** | Business facts, preferences, project rules | Personal facts. Don't duplicate business decisions here; link to the doc instead |

Note that Claude on the business account already has Gmail and Drive connectors (this session has used both), so Google data is not out of reach from the business side. The personal account's advantage is that it *is* the Google identity: Gemini sits inside Gmail, Drive and Maps with the personal history behind it. Use that for discovery, then move the result across.

### 2.2 The shared Drive folder

Create one folder (for example `Bright Tree – shared library`) owned by the business account and shared with the personal account. Everything either side extracts lands there in a dated, structured file. Suggested layout:

```
shared-library/
  intake/        raw: PDFs, quotes, photos, exports (never edited)
  extracted/     structured markdown or JSON made from intake, with front matter
  context/       the versioned master context bundles (see 4.2)
  reports/       finished reports and decks
```

Every file in `extracted/` carries front matter: `source`, `date`, `model`, `account`, `confidence`, `verified_by`, `licence`. That line of provenance is what lets a later model trust or re-check it.

### 2.3 Notion and the privacy line

Notion stays the source of truth for people, dates, dollars and tasks. The map stays the source of truth for location. Project docs stay the source for knowledge and method. Raw site data and addresses stay in the private repo. These rules don't change because a second vendor is in the loop; Gemini outputs pass the same four gates (people and privacy, data rights, IP, reversible) before they enter the library.

---

## 3. Which model, when

Models change; the roles don't. Check names, prices and context windows on docs.claude.com and Google's model page before wiring anything in.

| Role | Model (today) | Use it for | Why not something cheaper |
|---|---|---|---|
| **Daily driver for design, synthesis, code** | Claude Opus 5.5 (high effort, extended thinking on) | Design reviews, species and guild logic, water and fire reasoning, Notion schemas, Python architecture, report drafting, this kind of planning | Mid-tier models write point solutions and drop secondary interactions (allelopathy, cold-air pooling, overflow paths) when several constraints couple |
| **Foundations and audits** | Claude Fable 5.1 | The master ontology and schemas ("write once, rely forever"); multi-constraint problems where ten or more variables interact (a ten-year guild, a water balance under 2050 rain, a staged earthworks plan); red-teaming an Opus design before it goes live; long sessions over a large stable context | Attention over long chains of interdependent constraints is where the extra capability shows. Fable 5.1 shares its base with Mythos 5.1 and adds safety limits on biology, cyber and LLM R&D, none of which touch this work |
| **Second opinion, ingestion, long documents, images** | Gemini Pro (current version) | Reading whole manuals, lab reports and surveys at once; drone and photo interpretation; Gmail and Drive discovery; cross-vendor critique | Different training, different blind spots. The value is independence, not cheapness |
| **Bulk, well-specified work** | Claude Sonnet 5.5 | Tagging and extraction against a fixed schema, translation drafts (Japanese tabs), table filling, running the evaluation set, first-pass transcript cleanup | Accurate when the task is tightly specified; keeps Opus and Fable for judgement |
| **Classification and routing** | Claude Haiku 5.5 or a local small model | Deciding which tier a request needs, deduplication, intent tags | Cheap enough to run on everything |
| **Above Fable** | Claude Mythos Preview | Not available to the public (Project Glasswing). Design nothing around it | |

### 3.1 Escalation triggers (when Opus is not enough)

Escalate to Fable, or to an ensemble, when any of these is true:

1. **Foundational:** the output will be reused by many later outputs (ontology, schema, core class design, the report template, the scoring method).
2. **Coupled:** more than about five variables interact non-linearly, or the answer must hold over years (succession, water balance, fire fuel, cash flow with a mortgage).
3. **Irreversible or costly:** earthworks, tree removal, a contract, a published report, a public claim about a site.
4. **The two vendors disagree** on a material point after a first pass.
5. **The constraint ledger (4.3) has an unresolved conflict** the daily driver couldn't settle.

Everything else runs on Opus or lower. The bias toward capability is spent where it changes outcomes, not on every message.

### 3.2 Effort settings matter as much as model choice

On Opus and Fable, turn effort up and allow long thinking for the triggers above. A high-effort Opus answer with a constraint ledger often beats a low-effort Fable answer without one. The reverse is also true: a bigger model fed a vague prompt gives a confident, vaguer answer.

---

## 4. Methods that produce precision (vendor-independent)

These are what make "the most intelligent selection of resources" real. They cost little and they compound.

### 4.1 Facts in tables, prose for reasoning
Plants, prices, sites, rainfall, sessions, ideas and threads live in tables with IDs. A model asked for a number reads the table; it does not read prose and guess. (Already the rule in the knowledge-engine paper.)

### 4.2 A versioned master context
Compile the bundle Gemini describes (site constants, infrastructure specs, species matrix, schemas, method rules, privacy rules) from the repo and project docs with a script, stamp it with a version and hash, and cache it. Rebuild on change, not monthly by habit. Every answer logs the context version it ran against, so a wrong recommendation can be traced to stale data rather than to the model.

### 4.3 Constraint ledger before design
For any design question, the first output is a list of every constraint and coupling in play (water, sun, fire, slope, soil, access, species limits, rules, budget, labour, time), each with its source. The design is produced against that ledger, and the audit checks the ledger, not the prose. This is the single biggest guard against a model simplifying the problem.

### 4.4 Generate, then audit with a different model
Opus designs; Fable or Gemini audits with a fixed brief: list contradictions, missing constraints, unverified numbers, privacy leaks, and anything that would break when a module is added. The audit returns findings, not a rewrite. The human decides. This is the ensemble mode, framed so it sharpens rather than averages.

### 4.5 Citations on every claim that can be checked
Session ID, document path, dataset and date, or "unverified". The check-notes practice in the lecture notes is the model for this.

### 4.6 An evaluation set
Fifty to a hundred real questions with known good answers (from the lecture check notes, the site reviews, the plant list, the water calculations). Run it whenever a model, a prompt, a context version or a vendor changes. Score accuracy, citation correctness and refusal to guess. This is how you learn where Gemini or Sonnet is good enough and where it isn't, instead of assuming.

### 4.7 Kill tests and "approve for live"
Nothing produced by a model reaches a shared map, a Notion database or a client report without the existing approve-for-live step, and every spike names what result would stop it.

---

## 5. Using Gemini's unused tokens well

The constraint is the same as for everything else: outputs must enter the shared library as structured, cited files, or they are wasted. Within that rule, Gemini has plenty of good work:

| Job | How it feeds the system | What it must not do |
|---|---|---|
| **Google-held data discovery** | Search Gmail and Drive for quotes, invoices, contractor threads, equipment specs; write each as an `extracted/` file with source email or file IDs | Decide what the data means for the design |
| **Long-document ingestion** | Read manuals, standards, council documents, lab reports whole; produce structured summaries with page references | Replace the primary source; the page reference is what makes it checkable |
| **Photo and drone cataloguing** | Date, location (from EXIF where present), what is visible, species guesses marked as guesses; a table per batch | Publish anything with GPS or addresses outside the private repo |
| **Transcript and handout cleanup** | First-pass cleanup of recordings and OCR of handouts before Claude writes the lecture note; cross-check against Kaz's Japanese notes | Write the final note or the check notes |
| **Red team** | Audit Claude's designs and reports with the 4.4 brief | Rewrite them |
| **Evaluation questions** | Draft candidate questions and answers for the evaluation set from the notes; Claude and Brett verify | Mark its own answers correct |
| **Maps and places** | Travel times, nearby suppliers, Landcare groups, tip shops for the nearby-resources ring (A45) | Store personal location history in the business library |

Two habits keep this from fragmenting understanding: give Gemini the same versioned master context Claude uses (so both reason from the same facts), and never let it be the only place a decision is recorded.

---

## 6. The LiteLLM backend

The router in Gemini's answer is a reasonable skeleton. Adjustments:

- **Tiers by job, not by vendor loyalty:** `ingest_multimodal` (Gemini), `design_synthesis` (Opus, high effort), `foundation_or_audit` (Fable), `bulk_extract` (Sonnet), `classify` (Haiku or local), `ensemble_audit` (Opus plus Gemini, Fable audits). Add `bulk_extract` and `classify`; the pure-frontier router spends money where it buys nothing.
- **Caching:** put the master context in a cached system block as shown; log cache hits and cost per call; rebuild the cache only when the context version changes.
- **Provenance on every call:** write model, context version, prompt version, cost and citations to a log table. This is also the audit trail a funder or client will ask for.
- **Fallbacks:** fine as written, but a fallback to a different vendor should mark the answer as "fallback" so an audit knows it came from the other model.
- **Keys and billing:** Anthropic Console and Google AI Studio or Vertex keys, separate from the subscriptions. Start pay-as-you-go with a monthly cap; the evaluation set tells you where to cut.
- **Local inference later:** the knowledge-engine paper's path (small open models on Bright Tree solar for classification, search and drafts) fits the data-sovereignty value; keep frontier models hosted until the evaluation set says otherwise.
- **Verify model strings** before use; the names in Gemini's code are illustrative.

---

## 7. Decision matrix

| Situation | Where | Model | Then |
|---|---|---|---|
| New lecture recording | Business account | Sonnet cleanup, Opus note, check notes verified | Project doc, Docs tab, laptop |
| Design review for a group site | Business account | Opus (high effort) with constraint ledger; Fable or Gemini audit | Review doc, trial map, peer-review checklist |
| Master ontology or schema change | Backend or business account | Fable, then ensemble audit | Versioned context bundle, repo, Notion |
| Water, fire or earthworks decision at Bright Tree | Business account | Opus design, Fable audit; the map's calculators for numbers | Design threads, A3 sheet, approve for live |
| Supplier quotes, invoices, old emails | Personal account (Gemini) | Gemini extraction to `extracted/` | Notion price book (A52), budgets (A53) |
| 300-page manual or standard | Personal account (Gemini) or Claude with the file | Gemini summary with page refs | Project doc, cited |
| Japanese tabs, glossary, tagging | Backend | Sonnet draft, Opus check | Docs tabs |
| Public or client-facing report | Business account | Opus draft, Fable audit, privacy-check skill | Published artefact, first names only |

---

## 8. A phased plan

**Now (this week)**
- Create the shared Drive folder with the four subfolders and the front-matter rule.
- Add front matter (session, date, presenter, topics, source, licence) to the lecture notes as they are written; backfill with a script.
- Write the constraint-ledger prompt and the audit brief as two short files in the repo so every session uses the same ones.
- Start the evaluation set with 30 questions from the check notes.

**Next (November)**
- Compile the first versioned master context bundle from the repo and project docs.
- Stand up the LiteLLM router with the six tiers, caching and the provenance log; API keys with a monthly cap.
- Run the evaluation set across Opus, Fable, Sonnet and Gemini; record the results in the repo.
- Use Gemini for the backlog of quotes, manuals and photos into `extracted/`.

**Later (2027)**
- Local small models for classification and search on Bright Tree hardware.
- Fine-tune a small adapter for house style only, once a few hundred approved reports exist.
- Revisit model roles each quarter against the evaluation set and the live price list.

---

## 9. Open questions for Brett

1. Which account should own the shared Drive folder and the API keys (business is the natural owner for both)?
2. Monthly API budget cap to start with?
3. Should the audit brief include a mandatory "what would break if we added IoT sensors / a second property / a client tier" question for every foundational change?
4. Is Gemini allowed to read the private repo's site data, or only the shared library? (Recommendation: shared library only, until the data-rights gate is applied to the Google terms.)
