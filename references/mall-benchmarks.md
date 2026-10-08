# Preset: shopping-mall benchmark set

Observed in October 2026. Scores are design-modernity judgments (0-10); re-check before reuse, since sites change. "Inferred" means the site was read as text, not seen visually.

| Mall | Region | URL | Design | Notes |
|---|---|---|---|---|
| Mall of the Emirates | Dubai | https://www.malloftheemirates.com/en | 8 | Task-tile hero, predictive header search, "View on Map" deep link with Find My Car (Proximi.io), WebP, Vue/Tailwind on Sitefinity. Blocks headless browsers; cookie banner has no Reject. |
| The Dubai Mall | Dubai | https://thedubaimall.com/en/ | 7 | Luxury editorial, two-tier nav with districts, mega menu with gift occasions, offers toggle in directory, Abuzz map. Times out for headless browsers. |
| Dubai Hills Mall | Dubai | https://www.dubaihillsmall.ae/ | 7.5 | Immersive full-screen photo hero, photo cards, offers in directory, Pointr map, WhatsApp. WordPress; weak titles. |
| Mall of Qatar | Doha | https://www.mallofqatar.com.qa/en | 5 | Next.js with optimised images; plain design; kiosk and gift-card filters; thin store pages. |
| Yas Mall | Abu Dhabi | https://www.yasmall.ae/en | 4 | Template-era layout, error page on /en, logo cards with category counts. Access Denied to headless browsers. |
| ICONSIAM | Bangkok | https://www.iconsiam.com/en | 8 (inferred) | Video hero, events rail with Happening/Upcoming tabs, zone branding, Next.js. Homepage title is "Homepage". Customer-type popup. |
| Azabudai Hills | Tokyo | https://www.azabudai-hills.com/en/ | 8 (inferred) | Editorial place-making, usage-scene filters, rich store info tables, Webflow. |
| Bicester Village | UK | https://www.thebicestercollection.com/bicester-village/en | 8 (inferred) | Campaign-led editorial, virtual shopping per brand, Arabic/Chinese/Korean, chip filters. |
| Westfield London | UK | https://www.westfield.com/en/united-kingdom/london | 7 (inferred) | Live open status on cards, store count, level and zone, WebP image CDN, skip links. Large consent popup. |
| K11 MUSEA | Hong Kong | https://www.k11musea.com/ | 7 (inferred) | Art identity, shop/product browse toggle, floor plan with pin on store pages. Directory loads client-side. |
| Jewel Changi Airport | Singapore | https://www.jewelchangiairport.com/ | 7 (inferred) | Looping video hero, attractions and ticketing, thin brand pages, AEM. |
| ION Orchard | Singapore | https://www.ionorchard.com/ | 7 (inferred) | Best filter set (level, rewards, status, URL params), scoped search tabs. |
| Yorkdale | Toronto | https://yorkdale.com/ | 7 (inferred) | Next.js, similar-shops carousel; directory not visible to crawlers. |
| GINZA SIX | Tokyo | https://ginza6.tokyo/ | 6 (inferred) | Floor tabs with plans, category counts, tax-free/parking/points badges, podcast and magazine. |
| Hudson Yards | New York | https://www.hudsonyardsnewyork.com/ | 6 (inferred) | Directions on cards, price level and booking on store pages; carousel plus signup popup. |
| Bal Harbour Shops | Miami | https://www.balharbourshops.com/ | 6 (inferred) | Fashion-magazine feel, online shopping; no wayfinding. |
| Harbour City | Hong Kong | https://www.harbourcity.com.hk/ | 5 (inferred) | Huge text directory with building-coded units; PDF map; broken /en/en/ paths. |
| Mall of America | Minneapolis | https://www.mallofamerica.com/ | 5 (inferred) | Live parking by ramp, best parking per store, 9 languages, list/map views; cluttered. |
| The Grove | Los Angeles | https://www.thegrovela.com/ | 5 (inferred) | Hours strip, status tags; very basic text directory. |
| Riyadh Park / Via Riyadh | Riyadh | riyadhpark.com / viariyadh.com | n/a | Unreachable in Oct 2026 (SSL errors, 502). Retry. |

## Patterns worth recommending
Predictive grouped search (Mall of the Emirates, ION Orchard) · live open status on cards (Westfield) · offers toggle and gift-card badges in the directory (The Dubai Mall) · store page deep-linked to the map with Find My Car (Mall of the Emirates) · events rail with tabs and date pills (ICONSIAM) · usage-scene filters (Azabudai Hills) · virtual shopping per brand (Bicester Village) · live parking and best parking per store (Mall of America) · service badges such as tax-free and points (GINZA SIX).

## Gaps seen across all of them
No mall had an "open now" directory filter. Few embed an interactive map on the store page. WebP/AVIF is still rare. Weak `<title>` tags are common.
