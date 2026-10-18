---
name: ram
description: Use Team RAM coding, architecture, recon and review roles in the current Hermes conversation.
---

Call `allura_team` with `team: "ram"`, the requested role (default `brooks`), and
the user's task. Apply the returned Hermes adapter, adaptive workflow and role
guidance under the host's instructions and permissions. Execute the task in the
current conversation. Guidance loading alone is not execution or verification.

Choose one owner and quick/standard/sensitive routing. Hydrate local context then
Brain with explicit `group_id: allura-system`; reuse a valid scoped receipt and
report unavailable memory honestly. Load only 1–3 relevant skills through
`skill_view(name="team-ram-durham:ram-<skill>")`. No automatic worker or model switch.
Read-only reviewers report findings; the producer makes changes. Persona guidance
does not establish enforced tool isolation. Preserve required human approval gates.

On Team RAM activation or an explicit `menu`, `help`, or `MH` request, load
`skill_view(name="team-ram-durham:ram-allura-menu")`, display that canonical menu
in chat, and recommend the next applicable step for the user's current task.
The menu entries route to skills; they do not create Hermes slash commands.
During ordinary work, give the result and next step without repeating the menu.

For **Setup** and **Doctor**, apply the returned Hermes adapter's installed-path
`python3 .../scripts/doctor.py` command. This overrides the canonical skill's
`bun run team-ram:doctor` source-checkout command for Hermes only. The local check
is read-only and needs neither source repositories nor Bun, network or secrets.
If the shell or Python is unavailable, show the command and report diagnosis
unavailable. Setup explains missing capabilities without changing configuration.
Brain health is separate and remains unverified without an actual scoped receipt.
