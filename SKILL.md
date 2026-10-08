---
name: website-benchmark
description: Research, audit and benchmark a website against the best competitors, then produce a cited research brief, a benchmark report with screenshot evidence, a component kit, a vetted CSS/UI resource directory and a ready-to-paste build prompt. Use when the user gives a website URL and asks to benchmark it, compare it with competitors, audit its UX/UI, research its market, find what to fix, plan a redesign, or find components/resources to rebuild it. Also triggers on "benchmark this site", "compare with competitors", "UX audit", "how does our website compare", "redesign research".
---

# Website Benchmark

Turn one URL (plus any extras the user has) into research, a benchmark against the best competitors, and a concrete plan to rebuild the site. The website is the main subject. Research may reach anything that affects it (apps, social channels, physical locations, the local market, laws), but anything outside the website is flagged to the user before going deeper.

Follow the phases in order. Never skip the two scope confirmations.

## Phase 0: Intake

1. Take the URL. Ask whether the user has extras that could help. Accept anything: a crawled folder, screenshots, PDFs, brand guidelines, analytics or Search Console exports, survey results, reviews, competitor lists, previous reports, notes. Read every extra before asking more questions.
2. Do a quick look at the site (homepage plus one or two inner pages, text only) to detect: website type, countries served, language versions (check for `/ar`, `lang`, `dir="rtl"`), main page types, and the tech stack hints.

## Phase 1: Questions (multiple choice)

Ask with the AskUserQuestion tool, at most 4 questions per call, in 2-3 calls. Pre-fill options from Phase 0 and the extras. Every question gets a "Skip / you decide" option (the tool adds "Other" automatically). Use `references/questions.md` for the full bank and per-type presets. Core questions:

1. Website type · 2. Goal · 3. Main visitors · 4. Countries served · 5. Competitor markets · 6. Competitors (suggest / user names / mix) · 7. Languages · 8. Key pages · 9. Research depth (Light / Standard / Deep) · 10. Benchmark depth (Quick ~8 / Standard ~15 / Deep ~20+) · 11. Outputs · 12. Browsing permissions

Also ask where to save the outputs (a folder path).

## Phase 2: Scope confirmation, twice

- **2A. Proposal.** Show the full plan: research topics, competitor list grouped by region (with URLs), pages to check on each site, languages, outputs, browsing permissions, estimated time and number of agents. Invite edits.
- **2B. Final recap.** After edits, show a 3-4 line recap and ask **Start · Edit again · Cancel** with AskUserQuestion. Nothing heavy (research, crawling, benchmark, screenshots) runs before the user picks Start.

## Phase 3: Research

Use `references/research-playbook.md`. Run research agents in parallel (general-purpose subagents with WebSearch/WebFetch). Every finding needs a cited URL; label estimates and give the year of each figure.

- **A. Geography and local market** for each country served: population and audience mix, languages and script, internet and devices, social and messaging platforms, calendar and seasons, climate and daily rhythm, payments, laws, maps and getting there, nearby physical competitors, tourism and cross-border visitors, local search behaviour. Start from `references/markets/<country>.md` but re-verify everything.
- **B. Industry and audience:** best practices for this website type, visitor needs ranked, web trends, standards (WCAG 2.1 AA, Core Web Vitals).
- **C. Beyond the website** (only where it affects the site): app, social channels, reviews, on-site experience. Flag to the user before going deeper.
- **D. Competitor discovery:** global and local candidates. New ones go back to the user for approval.

Turn the research into: (1) score weights for the rubric, (2) an audit checklist, (3) requirements for the build prompt.

## Phase 4: Audit the target

1. Technical: run `scripts/audit_html.py` on a crawled folder or a URL list. If deeper data is needed and the user allowed crawling, run `scripts/mirror.py` with the limits the user set (ask first).
2. Screenshots: `scripts/screenshots.py pages` at 1440px desktop and 390px mobile for every key page and language.
3. Visual review: read the screenshots (split tall captures into chunks). Look for content errors (wrong names, typos, conflicting facts such as two different opening hours), contrast, empty fields, broken RTL (mixed-direction strings), mistranslations, layout issues.
4. Check the site against the research checklist and the user's extras.

## Phase 5: Benchmark competitors

Launch one subagent per region in parallel, each with the template in `references/agent-template.md` (homepage, navigation and search, listing and filters, detail page, languages, standout features, weaknesses, technical notes; ranking plus 10 best patterns). Blocked, offline or bot-protected sites are reported, never guessed. Capture first-screen screenshots of competitor homepages where possible.

## Phase 6: Score

Use `references/rubric.md` (8 dimensions with anchors), weighted by the research. Mark anything judged from text only as "inferred".

## Phase 7: Outputs (only the ones chosen)

Build each as an HTML page (load the `artifact-design` skill first if publishing artifacts), publish as a private artifact, and also write a standalone copy to the user's folder with `scripts/export_standalone.py`.

- **Research brief** (`templates/research-brief.html`): market profile per country, 12-month seasonal calendar with what the site should do in each period, ranked audience needs, best practices, trends, search terms per language, standards. Every point cited.
- **Benchmark report** (`templates/benchmark-report.html`): verdict and score, key numbers, scorecard, design ranking, issues by severity in the format Problem → Screenshot → Who does it better → Research reason → Fix, component comparison, how competitors present listings, strengths, roadmap (week 1 / months 1-2 / months 3-6), method and limits.
- **Component kit** (`templates/component-kit.html`): for each issue, a before screenshot, a real-world reference, and verified components for HTML, React and CSS stacks. Each component: exact URL, where on the page (menu path and example position), screenshot captured with `scripts/screenshots.py components`, licence, pure CSS vs JS. Use subagents to find and verify components; start from `references/ui-sources.json`.
- **CSS resource directory** (`templates/resource-directory.html`): vetted sites only (include any site the user named), what each provides, best use for this project, licence, stack, RTL support, GitHub stars, and Copy buttons for verified hooks (GitHub repo, agent skill, MCP server, npm, llms.txt). Run `scripts/check_sources.py` first so every link and command is re-verified. List dropped sites with the reason.
- **Build prompt** (markdown): tells another Claude session to read the outputs and build the site. Include stack default plus alternative, hard requirements (languages and RTL, single source of truth for facts like hours, pages, navigation, SEO, performance, accessibility, motion limits, brand), the market profile and seasonal calendar, the fix list, data sources, licence notes and deliverables.

Finish with a short summary in chat: links, files saved, the top findings, and anything unverified.

## Rules

**Scope and input**
1. The website is the main subject. Research may extend to anything that affects it. Flag anything outside the website before going deeper.
2. Input is a URL plus any extras. Read extras first and use them throughout.

**Asking before acting**
3. Questions are multiple choice, pre-filled, with Skip and Other.
4. Confirm scope twice (proposal, then Start · Edit again · Cancel).
5. Nothing heavy runs before Start.
6. Stop at the build prompt. Never build or publish a website unless the user asks separately.

**Evidence and honesty**
7. Every claim has evidence (screenshot, measured number, observed text) or a cited source.
8. Label inferences and estimates.
9. Report gaps; never fill them with guesses.
10. Refresh market data and re-verify resource links and commands on every run.

**Browsing: ask first**
11. Logins: ask; the user signs in themselves in the browser, then continue. Never type passwords or create accounts.
12. Forms: ask before submitting any form.
13. Cookies: ask which choice to make; without an answer, decline non-essential cookies.
14. CAPTCHAs and human checks: ask the user to complete them; never solve them.
15. Crawling: ask for limits (pages, speed, sections) first; follow robots.txt; skip trackers.
16. Downloads: ask first, stating file name, source and size.

**Content and licences**
17. Copy commands come only from a resource's own repo or docs, never from memory.
18. Show every component's licence; mark paid tiers.
19. Never invent brand logos, trademarks or content; mark placeholders.
20. Never translate Arabic or other languages literally; flag uncertain wording for native review.
21. Never copy competitors' branding, text or images.

**Tools, data and outputs**
22. Use paid SEO or analytics tools only if connected; otherwise public data plus the user's extras.
23. Collect no personal data from target or competitor sites; keep the user's extras local.
24. Outputs are private, saved to the user's folder, and never sent or shared without an explicit yes.

## Files

- `scripts/audit_html.py`: SEO, accessibility and asset audit of a folder or URL list.
- `scripts/screenshots.py`: page captures, component captures at an anchor, crops and contact sheets.
- `scripts/check_sources.py`: verifies UI resource sites, llms.txt, GitHub repos, skills and MCP hints.
- `scripts/export_standalone.py`: embeds images into HTML for standalone files.
- `scripts/mirror.py`: polite Playwright crawler (only when permitted).
- `references/questions.md`, `research-playbook.md`, `markets/`, `rubric.md`, `agent-template.md`, `ui-sources.json`, `mall-benchmarks.md`.
- `templates/`: research brief, benchmark report, component kit, resource directory.
