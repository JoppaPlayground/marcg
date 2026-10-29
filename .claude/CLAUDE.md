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
- Keep the current design and its energy: navy hero with the compass and waves, stats bar, work timeline, sunset band, advisory cards, scroll motion. Marc found a stripped-down minimal redesign too boring, so fix AI tells at the detail level instead of redesigning.
- Detail tells to avoid: ALL-CAPS tracked eyebrows or labels, a word or line in a headline set in another color, Title Case micro labels, arrows tacked onto links and buttons, middle-dot strings, thin light-gray body text.
- Product links use real destinations as their text (moneylion.com, Fast Company).
