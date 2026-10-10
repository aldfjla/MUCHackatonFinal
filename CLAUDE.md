# Team workflow

The main session is the manager. Subagents live in `.claude/agents/` and are shared via git.

- Plan first, then delegate. Do not write code yourself.
- Code changes go to `coder`.
- After every code change, run `reviewer` and fix Critical issues before finishing.
- Use `teacher` only when asked to explain something.
- Subagents cannot spawn other subagents; give each one the full context it needs.

To add or change an agent, edit its file in `.claude/agents/` and commit it so the team gets it.
