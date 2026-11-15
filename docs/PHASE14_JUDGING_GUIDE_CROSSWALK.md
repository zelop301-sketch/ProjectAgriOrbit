# AgriORBIT NASA — 2026 NASA Space Apps Judging Guide Crosswalk

**Basis:** User-provided 11-page *Judging & Awards Guide*, dated November 13, 2026. A copy is under `docs/reference_guide/`. This is a research and portfolio project; this guide companion does **not** submit a project or certify eligibility.

The NASA Space Apps guide emphasizes collaboration, learning, growth and sharing rather than prizes alone (p. 1).

## Official judging rubric — 1–5 per criterion

| Criterion | Source | Demonstrable AgriORBIT evidence | Current limitation / immediate next action |
|---|---|---|---|
| Impact | p. 5 | Botolan pilot context and farmer-centered workflow | Consult farmers, record need, create a real-world usability observation; don't claim field validation if not done |
| Creativity | p. 5 | Holographic farm, visual rover mission, multi-source decision-support concept | Show novelty through understandability and actionable comparisons, not just effects |
| Validity | p. 6 | Quality-gated historical rainfall benchmark, API, reproducible tests | Agronomic rules are exploratory; seek soil lab results, agronomist review, measured validation |
| Relevance | p. 6 | NASA POWER historical data influence the experimental water-exposure view | Link a real, source-cited NASA sample and explicitly show before/after comparison; reject synthetic as evidence |
| Presentation | p. 7 | Mission Control walkthrough plus 30-second timer and 7-slide outline | Rehearse and obey the maximum; verify facts and all source credits |

The guide explicitly expects NASA data to be a **core** part of the solution, not a superficial decoration (p. 6). In the app, the Precision Climate Lab is the preferred demonstration because it shows source, calendar period, data coverage, provenance and limitations. NASA POWER is gridded historical meteorology, **not** a plot-scale measurement or future forecast.

## Global Judging minimum requirements (guide p. 3)

- Respond to an official challenge.
- All team members registered for the same Local Event (not waitlisted) or Universal Event; all listed in the Members tab. Local Event minimum 1, Universal Event minimum 2, maximum 6.
- Complete every required Project Submission field.
- Provide either **up to 7 slides, including the title/intro**, or a **video up to 30 seconds**.
- Project page and linked materials in English. A demo video may be spoken in another language **with English subtitles**.
- Submit from **Team page → Project tab → edit → submit** before **Sunday November 15, 2026 at 11:59 PM**, based on the Local Event's local time, or the team owner's local time for a Universal Event. Confirm the local event's specific schedule.
- Review and affirm the required Terms, Privacy, original-work and external-resource/copyright declarations.
- The guide discusses NASA's China funding-restriction eligibility review on p. 4; determinations are NASA's, not the project's.

The **Project Submission Guide**, Participant Terms & Conditions, privacy policy, and event lead's rules are separate authoritative sources. This uploaded document is not a substitute for them. The guide does **not** resolve whether portfolio code developed before the event is eligible for reuse: **ask your Local Lead or organizers and disclose its origin accurately.**

## Guide-aligned demo plan

This is an editorial suggestion, not a NASA-prescribed storyline. For a video, rehearse 0–5s problem, 5–11s NASA observation and source, 11–19s local soil and three scenarios, 19–26s evidence/uncertainty, 26–30s farmer impact/limits.

For slides: (1) Title and problem, (2) Farmer context, (3) NASA data with metadata, (4) Soil and farmer priorities, (5) Three rotations, (6) Evidence/uncertainty and simulated rover disclaimer, (7) Impact, future validation and references. **Seven slides total**.

## Required scientific honesty

- Do not label synthetic numbers or artistic landscape imagery as live NASA data.
- The current crop-rotation scores are transparent but *unvalidated*. Do not present them as validated yields, profit forecasts or agronomic prescriptions.
- Rover telemetry and LiDAR are **simulated**, unless a future verified measured hardware system is actually connected.
- NASA POWER spatial representativeness, timestamps, units and missing-value quality checks must remain visible.
- Reference every external code library, dataset, photograph, AI-generated image, sound, music, text snippet, and other external resource as required by the guide. Complete the asset register before a real submission.

## Scope of Phase 14 implementation

`GET /api/spaceapps/guide` exposes rubric/limits and guide scope. `POST /api/spaceapps/audit` validates format and team size and assembles a checklist of **manually attested facts**. Its `self_reported_checklist_only` status is intentionally **not NASA eligibility**. The frontend offers a 30s rehearsal timer, 7-slide outline, 5-criterion self-assessment, references textarea, draft JSON export, and source-status overview; all checklist entries remain manually verified. Existing NASA data and scene modules are preserved.

## Awards mentioned in the guide (p. 11)

Best Use of Science; Best Use of Data; Best Use of Technology; Galactic Impact; Best Mission Concept; Most Inspirational; Best Storytelling Award; Global Connection Award; Art & Technology Award; Local Impact Award. These are **award descriptions, not promised outcomes**.

Official sites (current pages should be checked by the user):

- NASA Space Apps 2026 — https://www.spaceappschallenge.org/2026/
- Field Shift official challenge — https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/
- NASA POWER Daily API — https://power.larc.nasa.gov/docs/services/api/temporal/daily/
