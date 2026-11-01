---
name: vault-loop
description: Compile raw sources (RFCs, incident reports, meeting notes) into an Obsidian or Markdown knowledge vault using draft isolation and snapshot verification. Invoke via `/vault-loop <vault-path> [source-file]` to force the 4-step draft -> edit -> verify -> promote loop.
disable-model-invocation: true
---

# `/vault-loop` — Verified Markdown Vault Compiler

Maintain an Obsidian or Markdown knowledge vault as a verified state machine. When the user invokes `/vault-loop` (for example: `/vault-loop example-vault compile raw/2026-10-22-rfc-worker-lease-timeout.md`), **you** run the draft, verification, and promotion commands automatically. Never ask the human to run Python scripts by hand.

---

## 1. Vault Ownership & Schema Rules

1. **`raw/` is Read-Only:**
   - Read source files in `raw/`. Never edit, rename, or delete any file inside `raw/`.
2. **Required Note Frontmatter:**
   - Every note in `concepts/`, `decisions/`, or `entities/` must start with YAML frontmatter:
     ```yaml
     ---
     type: concept | decision | entity
     status: active | superseded | draft
     sources: [raw/<filename>.md]
     ---
     ```
   - Use typed relational edges in frontmatter where applicable: `supports: [...]`, `contradicts: [...]`, `supersedes: [...]`.
3. **Human Prose Protection (`owner: human` & `agent:auto` markers):**
   - If a note has `owner: human` in frontmatter, never modify its prose.
   - Only update links inside `<!-- agent:auto:start -->` ... `<!-- agent:auto:end -->` HTML comment blocks.
4. **Supersede, Never Delete (Anti-Goodhart Rule):**
   - When a new source in `raw/` contradicts an existing decision (ADR), **never delete the old ADR**.
   - Create a new ADR with `supersedes: [<old-adr-slug>]`.
   - In the old ADR, change `status: active` to `status: superseded` and add a pointer line to the new ADR.

---

## 2. Automated 4-Step Execution Loop

Locate the bundled verifier script at `scripts/vault_check.py` (relative to this `SKILL.md` file). Execute these four steps automatically whenever `/vault-loop` is invoked on a `<vault>` directory:

### Step 1: Create Isolated Draft & Snapshot
Before touching any file in `<vault>`, run:
```bash
python3 <skill-dir>/scripts/vault_check.py draft <vault>
```
This saves a cryptographic baseline snapshot (`<vault>/.vault-check/snapshot.json`) and creates a working copy at `<vault>.draft`.

### Step 2: Edit Only Inside `<vault>.draft`
1. Read `<vault>.draft/index.md` first to orient yourself without grepping the entire vault.
2. Perform all note creations and updates strictly inside `<vault>.draft/`.
3. Link every new note in `<vault>.draft/index.md` and inside the `agent:auto` markers of related notes.
4. Append one audit line to `<vault>.draft/log.md`:
   `YYYY-MM-DDTHH:MM:SSZ | ingest | raw/<file>.md -> <notes-touched>`

### Step 3: Run Deterministic Verification
Verify your draft against the baseline snapshot:
```bash
python3 <skill-dir>/scripts/vault_check.py verify <vault>.draft
```
- If `verify` outputs `REJECT`, read the `FAIL` lines and fix the real issue inside `<vault>.draft` (never delete a baseline note or edit `raw/` to pass). Re-run `verify` until it outputs `PASS`.

### Step 4: Promote Verified Changes to Live Vault
Once `verify` outputs `PASS`, promote the changes atomically and remove the temporary draft directory:
```bash
python3 <skill-dir>/scripts/vault_check.py promote <vault>.draft <vault>
rm -rf <vault>.draft
```
Report the promoted files to the user.
