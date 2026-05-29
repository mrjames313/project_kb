---
name: ingest
description: Add new raw materials (papers, datasets, transcripts, notes) to an area and create source pages that point at them. Raw files are immutable once added; source pages live in kb and can be edited.
---

# /ingest

Brings external materials into the framework as immutable raw files plus source pages that reference them.

## When to use

- User wants to add a paper, dataset, transcript, set of notes, or any other reference material.
- The material can be a file path on disk, a URL the user wants to save locally, or content the user is pasting/dictating.

## Steps

1. **Confirm the area.** Default to the adopted role's area. If the user names a different area, refuse — they need to switch roles via `/start` first (writes outside a role's area are not allowed).

2. **Categorize and locate.** Pick the right subdirectory under `areas/<area>/raw/`:
   - `papers/` — academic papers, preprints, articles.
   - `transcripts/` — meeting notes, interview transcripts.
   - `datasets/` — small data files. (For large datasets, put a manifest in `areas/<area>/data/manifests/` instead and point at external storage.)
   - `notes/` — informal notes, screenshots, anything else.

   Create the subdirectory if it doesn't exist.

3. **Place the raw file.** Copy or write the material to `areas/<area>/raw/<subdir>/<filename>`. Use a descriptive filename (e.g. `2024-shot-noise-photodetectors.pdf`, not `paper.pdf`). After this step, the file is immutable — never edit, rename, or delete it. (Lint rule 17 enforces this.)

4. **Create a source page.** Under `areas/<area>/kb/sources/`, create `s-YYYY-MM-DD-<slug>.md`:
   ```yaml
   ---
   id: s-2026-05-15-shot-noise-paper
   title: Shot noise in photodetectors (Smith et al., 2024)
   type: source
   status: active
   area: <area>
   created: 2026-05-15
   updated: 2026-05-15
   summary: One-sentence description of what this is and why it's relevant.
   relevant_to:
     - <tag1>
     - <tag2>
   when_to_load: |
     <optional. when should an agent load THIS body vs. cite a derived finding?
     skip the field if there's no useful "don't load" signal.>
   provenance:
     kind: external | internal-experiment | internal-notes
     retrieved: 2026-05-15
     raw_path: areas/<area>/raw/papers/<filename>
   ---

   Brief description of the source: what it contains, who produced it, where it came
   from. Optionally a few bullet points of what's interesting about it. Keep this
   short — the kb is for derived concepts/findings/decisions, not for transcribing
   sources.
   ```

5. **Record in pulse.log.** Append an entry to `areas/<area>/_journal/pulse.log`:
   ```
   ## [YYYY-MM-DD HH:MM] ingest <role>
   Ingested <slug>: <one-line description>.
   → to be filed: sources/s-YYYY-MM-DD-<slug>
   ```

6. **Verify.** Run:
   ```
   python _framework/tools/lint.py --rule 02
   python _framework/tools/lint.py --rule 17
   ```
   Rule 02 catches broken `raw_path`; rule 17 catches accidental modifications to other raw files.

## Notes

- For multi-file ingests (e.g. a series of related papers), create one source page per file. Each gets its own id and own raw_path.
- For large datasets (> ~10 MB or external storage): create a manifest in `areas/<area>/data/manifests/<id>.md` with `storage_uri` pointing at the external location, instead of putting the data file under `raw/`.
- If the user wants to ingest the same source into multiple areas, only ingest it once into the most relevant area. Other areas reference it via cross-area links once `multi_area` is enabled (lint rule 9 will surface heavy cross-area linking).
- Don't paraphrase or summarize the source's main content into the source page body. Source pages are pointers; analysis lives in concept/finding pages that cite them.
