# `/vault-loop` Agent Skill

An installable Agent Skill (`vault-loop`) for Claude Code, Cursor, Codex, and other autonomous coding agents that exposes the **`/vault-loop` slash command** to turn any Obsidian or Markdown folder into a self-verifying state machine.

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

## Installation

Clone the repository first:

```bash
git clone https://github.com/yeyu2/my-skills.git
cd my-skills
```

Then install into your agent client:

### Claude Code (`cc`)

```bash
# Global (all projects)
mkdir -p ~/.claude/skills
cp -R vault-loop/vault-loop ~/.claude/skills/

# Project-scoped
mkdir -p .claude/skills
cp -R vault-loop/vault-loop .claude/skills/
```

### Cursor

```bash
# Global (all projects)
mkdir -p ~/.cursor/skills
cp -R vault-loop/vault-loop ~/.cursor/skills/

# Project-scoped
mkdir -p .cursor/skills
cp -R vault-loop/vault-loop .cursor/skills/
```

### OpenAI Codex

```bash
# Global (all projects)
mkdir -p ~/.codex/skills
cp -R vault-loop/vault-loop ~/.codex/skills/

# Project-scoped
mkdir -p .codex/skills
cp -R vault-loop/vault-loop .codex/skills/
```

### Other Agents (OpenCode, Kiro, Hermes)

```bash
# OpenCode
mkdir -p ~/.config/opencode/skills
cp -R vault-loop/vault-loop ~/.config/opencode/skills/

# Kiro
mkdir -p ~/.kiro/skills
cp -R vault-loop/vault-loop ~/.kiro/skills/

# Hermes
mkdir -p ~/.hermes/skills
cp -R vault-loop/vault-loop ~/.hermes/skills/
```

Or install via `skills.sh`:
```bash
npx skills add yeyu2/my-skills --skill vault-loop
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
