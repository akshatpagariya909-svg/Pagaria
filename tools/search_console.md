# Getting the site into Google and Bing

Both services are free. Each needs you to sign in and prove you own the site once; after that, Claude can read
nothing from them, so the numbers live in your account.

## Google Search Console (10 minutes, once)

1. Go to https://search.google.com/search-console and sign in with a Google account you'll keep.
2. Choose **URL prefix** (not Domain) and enter exactly:
   `https://discoverarchitecture.github.io/`
3. Under verification methods pick **HTML tag**. Google shows a line like
   `<meta name="google-site-verification" content="abc123…">`.
   Paste that whole line into a chat with Claude: it goes into `site/index.html` just below `<meta name="viewport">`,
   and the change is deployed by merging to `main`. Then press **Verify** in Search Console.
4. In the left menu open **Sitemaps**, enter `sitemap.xml`, and press **Submit**. The sitemap already lists every
   building page (`site/sitemap.xml`, rebuilt by `tools/build_pages.py`).
5. Come back after two weeks. **Performance** shows which queries bring impressions and clicks, per page.
   **Pages** shows what is indexed and why anything was left out.

Optional, in the same place: **URL inspection → Request indexing** for the home page and ten of the most
looked-up buildings (the list is at the bottom of the home page) to get the first crawl started sooner.

## Bing Webmaster Tools (2 minutes, after Google)

1. Go to https://www.bing.com/webmasters and sign in (Microsoft or Google account).
2. Choose **Import from Google Search Console**. It copies the verified site and the sitemap; no code to add.
   Bing's index also feeds DuckDuckGo and Yahoo.

## What to watch

- Impressions for queries that contain a building's name plus *plan*, *section*, *case study* or the architect.
- Which of the "About" pages (the 100 most looked-up buildings and the South Asian ones) earn clicks.
- Indian buildings appearing for their own name without the architect's: Sangath, IIM Ahmedabad, CEPT.

## When the domain changes

If the site moves to discoverarchitecture.in, add the new address as a second property, submit the sitemap
again, and use **Settings → Change of address** on the old one. Keep the GitHub Pages address redirecting.
