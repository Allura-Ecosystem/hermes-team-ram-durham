---
name: ram
description: Use Team RAM coding, architecture, recon and review roles in the current Hermes conversation.
---

Call `allura_team` with `team: "ram"`, the requested role (default `brooks`), and
the user's task. Apply the returned Hermes adapter, adaptive workflow and role
guidance under the host's instructions and permissions. Execute the task in the
current conversation. Guidance loading alone is not execution or verification.

Choose one owner and quick/standard/sensitive routing. Hydrate local context then
Brain with the validated authenticated project/task group_id (`allura-system`
is the RAM default only when project and credentials confirm it). Council role
selection preserves the parent's validated scope and receipt; reuse that scoped receipt and
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

On activation or an explicit menu/help/MH request, load the shared protocol with
`skill_view(name="team-ram-durham:cowork-allura-menu")`. Show Next steps, Help
with a prompt, Council, Work, Loop, Validate, More; recommend one relevant next
action with a reason and owner. Clear tasks proceed directly and ordinary work
does not repeat the menu. More retains available domain routes.

Council requires two to four actual host-supported specialist invocations.
`allura_team` loads guidance into this conversation and does not invoke a
Council. If the host offers no real delegation, report Council unavailable and
return a proposed brief. Participant selection never grants another tenant or
permission to share client material. Loop establishes goal, permitted actions,
completion evidence and an explicit bound, then stops honestly on blockers,
stagnation or exhaustion. No implicit Ralph, background process or model change.
