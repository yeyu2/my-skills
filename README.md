# My Skills

Production-grade Agent Skills and hands-on engineering tutorials for Cursor, Claude Code, and autonomous coding agents.

## Skills

| # | Skill | Description | Folder | Install Command |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **vault-loop** | Verified Markdown vault state machine for Obsidian and compounding agent memory. Stages edits in `.draft`, blocks note deletions and human prose edits, and verifies against a snapshot before promoting. | [`vault-loop/`](vault-loop/) | `cp -R vault-loop/vault-loop ~/.cursor/skills/` |

## How to Install Skills

Clone this repository and copy the target skill folder into your project's `.cursor/skills/` (for project-scoped skills) or `~/.cursor/skills/` (for personal global skills across all repos):

```bash
git clone https://github.com/yeyu2/my-skills.git
cd my-skills

# Install vault-loop globally
cp -R vault-loop/vault-loop ~/.cursor/skills/
```
