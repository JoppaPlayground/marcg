# marcgigliotti.com

Marc's personal site: one page (index.html) plus llms.txt, served by GitHub Pages from main. Main is protected (no force pushes, no deletion).

## How changes ship

Marc doesn't review or merge. Claude does:

1. Branch off main, make the change, open a PR.
2. Run `python3 .github/scripts/check_site.py` until it passes. CI runs the same checks on every PR.
3. Have a fresh agent review the diff for facts, voice and broken markup.
4. Squash-merge once checks and review are clean, then confirm the change is live on https://www.marcgigliotti.com/.
5. Tell Marc in a line or two what changed.

Only stop and ask him when a change adds a fact about him that can't be verified from the page, his notes or a public source.

## Writing on the site

- First person, warm, direct, with contractions. It should sound like Marc talking, not a résumé or a template.
- No em dashes. No "not just X", "intersection of", "Whether X or Y", "AI-powered", "transforming", "seasoned", "curated".
- Specific numbers, consistent across sections. Plain words over acronyms.
- The Q&A on the page and the FAQPage data in the head match word for word. llms.txt keeps the fuller third-person version.
- Keep the nautical design (navy, teal, the compass and the waves) with Lora for headings and Plus Jakarta Sans for text.
- Skip what makes a site look generated: ALL-CAPS labels above headings, one word in a headline set in another color, big-number-small-label stat blocks, fade-in on scroll, icon cards with status dots, arrows on links, hover lifts, gradient washes, middle-dot meta strings.
- Links use real destinations as their text (moneylion.com, Fast Company), underlined.
