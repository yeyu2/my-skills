# Agent harness engineering

Runnable code, benchmarks, and Agent Skills for the Agent Harness Engineering video series. Each episode lives in its own folder under `episodes/`.

## Episodes

| Episode | Topic | Folder | Takeaway / Command |
| :--- | :--- | :--- | :--- |
| 14 | Context-isolated maker-checker graph. Runs the generator and verifier in separate OS processes and passes state through files on disk. | [`episodes/14-context-isolation/`](episodes/14-context-isolation/) | `python3 episodes/14-context-isolation/orchestrator.py` |
| 15 | Folding subagents into progressive skills. Compares subagent sprawl, a flat single-loop fold, and progressive skills with `model_map` delegation across six tasks. | [`episodes/15-fold-subagents/`](episodes/15-fold-subagents/) | `python3 episodes/15-fold-subagents/skill_gate.py check` |
| 16 | The seven-subsystem coding harness. Unified harness policy across shell and typed tools with cache prefix locking, AST layer linter, and planted-defect gate. | [`episodes/16-seven-subsystem-harness/`](episodes/16-seven-subsystem-harness/) | `python3 episodes/16-seven-subsystem-harness/harness_check.py verify` |
| 17 | Markdown vault as agent state (`vault-loop` Skill). An installable Agent Skill that stages edits in a `.draft` copy and verifies them against a snapshot before promoting. | [`episodes/17-vault-loop-engineering/`](episodes/17-vault-loop-engineering/) | `cp -R episodes/17-vault-loop-engineering/vault-loop ~/.cursor/skills/` |
