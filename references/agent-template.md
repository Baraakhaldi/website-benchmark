# Benchmark subagent prompt template

Fill the placeholders and launch one general-purpose subagent per region, in parallel, in the background.

---
You are doing UX/UI benchmark research on {WEBSITE_TYPE} websites, to compare against {TARGET_URL}. Load WebFetch and WebSearch via ToolSearch ("select:WebFetch,WebSearch"). If browser tools (mcp__Claude_Browser__*) are available, use them for pages that block plain fetching.

Look at the {PAGE_TYPES} of each site:
{SITE_LIST}

Rules: do not log in, create accounts or submit forms. Decline non-essential cookies; if only "Accept" exists, leave the banner. Never click CAPTCHAs or human checks: report the site as blocked. Report offline or blocked sites; never guess their content.

For EACH site report concisely:
- Homepage: above the fold (video / carousel / static / task tiles), visual style, typography, colour, modernity score 1-10 with justification
- Navigation and search: menu structure, mega menu, global or predictive search, language switching and RTL quality
- Listing: filters, A–Z, search, card design, paging, item count if shown
- Detail page: information shown, layout, links to map or booking
- Standout features
- Weaknesses
- Technical notes if visible: unique titles, meta descriptions, image formats, framework hints

Finish with a ranking by design modernity and the 10 best concrete UX patterns you saw (which site, how it works). Report only what you observed; mark inferences and anything not seen visually. About 1200-1800 words.
---

## Component search subagent (for the component kit)
Give each agent one group of sources (Tailwind kits / React-animated / CSS galleries) from `ui-sources.json` and the list of needs (one per issue). For each need: best component plus runner-up, EXACT URL, WHERE on the page (menu path and example position), why it fits and what to adapt, free or paid and licence, pure CSS vs JS, RTL notes. Every link must be opened and verified. Also flag components to avoid (too gimmicky for the brand).
