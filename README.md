# My Skills

Production-grade Agent Skills and hands-on engineering tutorials for Claude Code, Cursor, Codex, and other autonomous coding agents.

## Skills

| # | Skill | Description | Folder | Slash Command |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **vault-loop** | Verified Markdown vault state machine for Obsidian & compounding agent memory. Stages edits in `.draft`, blocks note deletions and human prose edits, and verifies against snapshot before promoting. | [`vault-loop/`](vault-loop/) | `/vault-loop` |

## Installation

Clone this repository first:

```bash
git clone https://github.com/yeyu2/my-skills.git
cd my-skills
```

Then install the skill into your agent of choice:

### Claude Code (`cc`)

- **Global (all projects):**
  ```bash
  mkdir -p ~/.claude/skills
  cp -R vault-loop/vault-loop ~/.claude/skills/
  ```
- **Project-scoped (current project only):**
  ```bash
  mkdir -p .claude/skills
  cp -R vault-loop/vault-loop .claude/skills/
  ```

### Cursor

- **Global (all projects):**
  ```bash
  mkdir -p ~/.cursor/skills
  cp -R vault-loop/vault-loop ~/.cursor/skills/
  ```
- **Project-scoped (current project only):**
  ```bash
  mkdir -p .cursor/skills
  cp -R vault-loop/vault-loop .cursor/skills/
  ```

### OpenAI Codex

- **Global (all projects):**
  ```bash
  mkdir -p ~/.codex/skills
  cp -R vault-loop/vault-loop ~/.codex/skills/
  ```
- **Project-scoped (current project only):**
  ```bash
  mkdir -p .codex/skills
  cp -R vault-loop/vault-loop .codex/skills/
  ```

### Other Agents (OpenCode, Kiro, Hermes, Windsurf)

- **OpenCode:**
  ```bash
  mkdir -p ~/.config/opencode/skills
  cp -R vault-loop/vault-loop ~/.config/opencode/skills/
  ```
- **Kiro:**
  ```bash
  mkdir -p ~/.kiro/skills
  cp -R vault-loop/vault-loop ~/.kiro/skills/
  ```
- **Hermes:**
  ```bash
  mkdir -p ~/.hermes/skills
  cp -R vault-loop/vault-loop ~/.hermes/skills/
  ```

Or install across all supported agents via `skills.sh`:
```bash
npx skills add yeyu2/my-skills --global --agent '*'
```
