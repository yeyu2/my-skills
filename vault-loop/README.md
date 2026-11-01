# `/vault-loop` Agent Skill

An installable Agent Skill (`vault-loop`) for Cursor and Claude Code that exposes the **`/vault-loop` slash command** to turn any Obsidian or Markdown folder into a self-verifying state machine.

Instead of running Python scripts by hand or hoping the agent remembers your rules, you type:

```text
/vault-loop vault-loop/example-vault compile raw/2026-10-22-rfc-worker-lease-timeout.md
```

Because `SKILL.md` sets `disable-model-invocation: true`, the skill only runs when you explicitly force it with `/vault-loop`. When invoked, the agent automatically:

1. Snapshots the live vault and creates an isolated `.draft` copy (`scripts/vault_check.py draft`).
2. Compiles the new source inside `.draft`, using `supersedes` edges rather than deleting contradicted notes.
3. Runs `scripts/vault_check.py verify` against the snapshot until all 7 checks pass.
4. Promotes the verified changes back into the live vault (`scripts/vault_check.py promote`).

## Folder Structure

- `vault-loop/SKILL.md`: The `/vault-loop` slash command skill definition (`disable-model-invocation: true`) and 4-step loop contract.
- `vault-loop/scripts/vault_check.py`: Standard-library snapshot verifier invoked automatically by the agent.
- `example-vault/`: Minimal 6-file Markdown vault (`raw/`, `concepts/webhook-backpressure.md`, `decisions/adr-001-queue-retry.md`, `index.md`, `log.md`).

## Install the `/vault-loop` Slash Command

Clone the repository and copy the skill into your project or user skills directory:

```bash
git clone https://github.com/yeyu2/my-skills.git
cd my-skills

# Project-scoped
cp -R vault-loop/vault-loop .cursor/skills/

# Or personal global skill (available across all repos)
cp -R vault-loop/vault-loop ~/.cursor/skills/
```

## Running the Manual Verification Test

To verify that the snapshot checker rejects note deletions:

```bash
cd vault-loop
python3 vault-loop/scripts/vault_check.py draft example-vault
rm example-vault.draft/decisions/adr-001-queue-retry.md
python3 vault-loop/scripts/vault_check.py verify example-vault.draft
rm -rf example-vault.draft example-vault/.vault-check
```
