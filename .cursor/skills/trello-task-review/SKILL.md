---
name: trello-task-review
description: >-
  Performs a read-only Career AI intake from an open Trello card. Use when the
  user provides a Trello card link, asks to start or review work from a Trello
  ticket, or invokes /trello-task-review. The card defines the task. Do not
  implement, commit, push, or edit during this review.
---

# Trello task review

Canonical copy: `.cursor/skills/trello-task-review/SKILL.md`. `.claude/skills/trello-task-review` is a symlink to that directory. Edit the canonical file only.

The user supplies the Trello card URL. Substitute that URL for `[Link to the Trello card]` below. Attempt to read the card before asking the user to paste it. Then follow the procedure in order.

## Procedure

I’m joining the Career AI project and will be working alongside another developer. My task is described in this open Trello card:
[Link to the Trello card]
If you cannot access the card, ask me to paste its description, checklists, and relevant comments. Do not assume what it says.
Read AGENTS.md and follow .cursor/skills/career-ai-workflow/SKILL.md. The Trello card defines the task; the repository is the source of truth for implemented behavior and accepted technical decisions. Read the relevant documentation and feature handoff as directed by the project workflow.
Start with read-only work:
Summarize the card’s goal, scope, and acceptance criteria. Distinguish what the card states from your own suggestions.
Check the current branch and working-tree changes without modifying them.
Identify what is implemented, what has been decided, and what remains open for this task.
Identify dependencies or overlap with the other developer’s work, especially shared contracts, models, and migrations. If ownership is unclear, ask before changing shared areas.
Recommend the next step based on the task’s current stage and the project workflow.
Do not treat an open card as approval to implement or as evidence that its design has been accepted. Surface conflicts with existing decisions and unresolved questions.
Do not change files or branches during this initial review. Do not commit, push, open a PR, or update Trello without an explicit request. For later implementation work, keep changes small and follow the project’s review, testing, and documentation requirements.
Communicate with me in Hebrew. Write code, repository documentation, and repository instructions in English.
