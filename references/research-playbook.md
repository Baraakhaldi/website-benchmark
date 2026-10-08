# Research playbook

Every finding: one sentence, a cited URL, the year of the data, and "estimate" where it is one. Prefer primary sources. Run modules as parallel subagents (general-purpose, WebSearch + WebFetch); give each the country list, website type and the output format below.

## Output format for every finding
`- <finding> — <why it matters for the website> [source: <URL>, <year>] (estimate?)`

## Module A: Geography and local market (per country)

| Area | Questions | Good source types |
|---|---|---|
| Population and audience mix | Population, nationals vs expatriates, age profile, main nationalities, tourist arrivals and origin markets | National statistics office, World Bank, UN, tourism authority |
| Languages and script | Official and widely spoken languages; Arabic vs Latin digits; transliteration habits | Government portals, academic or industry studies |
| Internet and devices | Internet and mobile penetration, mobile vs desktop traffic share, connection speeds | Telecom regulator, DataReportal, ITU, Ookla, StatCounter |
| Social and messaging | Which platforms dominate (e.g. WhatsApp, Snapchat, Instagram, TikTok, X) | DataReportal, platform ad-reach figures |
| Calendar and seasons | Weekend days, public and religious holidays for the next 12 months (Ramadan, Eid, national days), school terms, Hijri dates | Government holiday announcements, ministry of education |
| Climate and daily rhythm | Seasonal climate, peak visiting hours, evening culture | National meteorology, tourism authority |
| Payments and commerce | Local card schemes and wallets (e.g. KNET, mada, BENEFIT), Apple Pay/Google Pay, BNPL (Tabby, Tamara), currency, gift-card habits | Central bank, payment providers, industry reports |
| Laws and rules | Data-protection law, cookie consent, accessibility requirements, rules on Arabic content, consumer protection | Official legal portals, regulator sites, reputable law-firm summaries |
| Maps and getting there | Map apps used, address conventions, public transport, ride-hailing | Transport authority, app store rankings |
| Nearby physical competitors | Same-type venues in the city, their positioning and websites | Maps, tourism sites, news |
| Tourism and cross-border | Visitors from neighbouring countries, seasonality, visa context | Tourism authority, airport statistics |
| Local search behaviour | Terms used in each language, "near me" habits, Google share | Google Trends, public keyword tools, competitors' visible SEO |

Deliverables: a market profile table per country and a 12-month seasonal calendar: month · event/season · visitor behaviour · what the website should do (hours banner, campaign page, event rail, content changes).

## Module B: Industry and audience
- Best practices for this website type: Baymard Institute (e-commerce and booking), Nielsen Norman Group, Google Search Central and web.dev, W3C WAI.
- Visitor needs ranked (what people look for first). Use surveys, studies and the user's analytics extras when given.
- Web trends among top sites in the industry (live status, predictive search, loyalty on web, AI assistants, virtual shopping).
- Standards: WCAG 2.1 AA, Core Web Vitals thresholds (LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1; verify current values on web.dev).

## Module C: Beyond the website (only when it affects the site)
App store presence and ratings, social channels and what they link to, review platforms (Google, TripAdvisor) and recurring complaints that the website could answer. Flag to the user before going deeper.

## Module D: Competitor discovery
Global best-in-class plus local rivals from Module A. Return name, URL, region, one-line reason. New candidates go back to the user for approval before benchmarking.

## Turning research into decisions
1. **Score weights:** raise the weight of rubric dimensions tied to top-ranked needs (e.g. mobile-heavy market → mobile checks count more; tourists → multi-language counts more).
2. **Audit checklist:** one yes/no line per actionable finding, e.g. "Ramadan hours shown?", "WhatsApp contact?", "Local payment method for gift cards?", "Arabic search matches Latin spellings?".
3. **Build prompt requirements:** languages, legal must-haves, payments, seasonal content, local platforms.
