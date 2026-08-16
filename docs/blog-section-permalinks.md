# Blog section permalinks

Every Markdown `##` or `###` heading is a shareable social object. Astro emits these artifacts at build time:

```text
/blog/<article>/
/blog/<article>/sections/<heading-slug>/
/og/blog/<article>/sections/<heading-slug>.png
```

Traditional Chinese posts use the same shape beneath `/zh-tw/`.

## Contract

- Astro's rendered heading id is the section identifier used by route generation, the copy control, scrolling, and the OpenGraph image.
- The heading icon copies the absolute `/sections/<id>/` permalink, never a fragment. URL fragments are not sent to Facebook, LinkedIn, or other
  social crawlers.
- Table-of-contents and same-page links to an `h2` or `h3` replace the address-bar URL with that section permalink. The Markdown copy control is the
  only chain icon; client-side navigation must not add a second fragment-only heading link.
- A section permalink renders the complete article and scrolls to its heading in the browser. Its `og:url`, title, description, and 1200×630 PNG
  identify the section, while `rel=canonical` continues to identify the article.
- Section permalinks are excluded from the generated sitemap because they are sharing entry points, not separate search documents.
- The image query contains a content-derived version so section edits produce a new URL instead of reusing a stale social-network cache entry.
- Legacy `#heading-slug` links remain valid and are upgraded in-browser with `history.replaceState`. Existing links to figures, equations, and tables
  are left unchanged.
- A legacy fragment submitted directly to a social crawler cannot be upgraded because browsers never send fragments to servers. Share the
  `/sections/<id>/` URL shown after opening the link instead.
- Vercel permanently redirects extensionless URLs without a trailing slash to their slash-form canonical URL, preventing crawlers from caching two
  identities for the same section.

Run `pnpm test:site` to build the site and verify the section pages, metadata, localized path, PNG signatures and dimensions, hash upgrade, and
sitemap.
