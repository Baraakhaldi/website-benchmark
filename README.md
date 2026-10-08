# website-benchmark

A [Claude Code](https://claude.com/claude-code) skill that turns **one website URL** into:

1. **Research brief:** audience, ranked visitor needs, a market profile for each country (population mix, languages, devices, social platforms, holidays, climate, payments, laws, maps, local competitors, search behaviour), a 12-month seasonal calendar, best practices and trends. Every point is cited.
2. **Benchmark report:** the site scored against 8–20+ best-in-class competitors on 8 dimensions. Each issue is laid out as *Problem → Screenshot → Who does it better → Research reason → Fix*, followed by a roadmap.
3. **Component kit:** ready-made UI components (HTML, React, copy-paste CSS) for each issue. Each one has a screenshot, the exact location on its source page, the licence and a real-world reference.
4. **CSS / UI resource directory:** vetted component sites with verified copy buttons for GitHub repos, agent skills, MCP servers, npm packages and llms.txt files.
5. **Build prompt:** a ready-to-paste prompt for another Claude session to build the new site from all of the above.

## How it works

1. **Intake:** you give a URL plus any extras (crawl folder, analytics exports, brand guidelines, notes).
2. **Questions:** multiple choice and pre-filled from the site: website type, goal, visitors, countries, competitor markets, languages, key pages, research and benchmark depth, outputs, browsing permissions.
3. **Scope check, twice:** a full proposal you can edit, then *Start · Edit again · Cancel*. Nothing heavy runs before you choose Start.
4. **Research:** parallel agents cover geography and local market, industry and audience, beyond-the-website signals, and competitor discovery.
5. **Audit:** a technical script, desktop and mobile screenshots in every language, a visual review and the research checklist.
6. **Benchmark:** parallel agents by region, all using the same template.
7. **Scoring:** an 8-dimension rubric weighted by the research.
8. **Outputs:** private artifacts plus standalone HTML files saved to your folder.

Browsing is careful by design. The skill **asks before** logins (you sign in yourself), form submissions, cookie choices, crawling, downloads and human checks (you complete them yourself). It never types passwords or solves CAPTCHAs. Every claim needs evidence, and gaps are reported, never guessed.

## Install

```bash
git clone https://github.com/Baraakhaldi/website-benchmark.git ~/.claude/skills/website-benchmark
```

The scripts need Python 3.10+ and:

```bash
pip install playwright pillow requests beautifulsoup4 lxml
```

```bash
python -m playwright install chromium
```

`check_sources.py` uses the GitHub CLI (`gh`) when logged in, and the public GitHub API otherwise.

## Use

In Claude Code:

> Benchmark https://www.example.com against the best competitors

or invoke `/website-benchmark`.

## Contents

| Path | What it is |
|---|---|
| `SKILL.md` | Workflow and the 24 rules |
| `scripts/audit_html.py` | SEO, accessibility and asset audit of a crawl folder or URL list |
| `scripts/screenshots.py` | Page captures, component captures at an anchor, crops and contact sheets |
| `scripts/check_sources.py` | Re-verifies UI resource sites, llms.txt files, GitHub repos, skills and MCP hints |
| `scripts/export_standalone.py` | Embeds images into HTML for standalone files |
| `scripts/mirror.py` | Polite Playwright crawler for one site section (run only with permission) |
| `references/questions.md` | Question bank and presets for each website type |
| `references/research-playbook.md` | Research modules, trusted source types, how findings become weights and checks |
| `references/markets/` | Starter profiles for Gulf countries (always re-verified) |
| `references/rubric.md` | 8-dimension scoring anchors and issue severity |
| `references/agent-template.md` | Prompts for the benchmark and component-search subagents |
| `references/ui-sources.json` | Vetted UI and CSS resources with verified hooks |
| `references/mall-benchmarks.md` | Preset benchmark set for shopping-mall websites |
| `templates/` | Research brief, benchmark report, component kit and resource directory layouts |

## Notes

- Scores are judgments, labelled as such. Market figures are always refreshed and cited, never reused from the starter profiles.
- Component licences are reported per item. Check paid tiers before use.
- The mall preset was observed in October 2026, and websites change.

## License

MIT
