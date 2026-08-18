import { defineCollection, z } from 'astro:content';

const blogCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    author: z.string(),
    description: z.string(),
    image: z.object({
      url: z.string(),
      // Optional light-theme variant; when present the post layout renders a
      // theme-paired hero and social cards use this one, since previews sit on
      // light chrome. `url` stays the canonical (dark) image.
      urlLight: z.string().optional(),
      alt: z.string(),
    }),
    tags: z.array(z.string()),
    lang: z.string().optional().default('en'),
    // Hidden posts stay reachable at their URL but are excluded from the
    // blog and tag listing pages.
    hidden: z.boolean().optional().default(false),
    // Draft posts render in `astro dev` for preview but are never built for
    // production, so an unfinished post cannot reach the site by being
    // committed. They are also excluded from every enumeration — listing,
    // tags, search, RSS, sitemap — in dev as well as production: the built
    // page does not exist, so an entry pointing at it is a dead link.
    // Publish by removing the flag.
    draft: z.boolean().optional().default(false),
    pubDate: z.date(),
    // Set when a post gets a substantive revision. Surfaces as the visible
    // "Updated" date, schema.org dateModified, and the sitemap lastmod, so
    // crawlers re-fetch the page instead of trusting a stale copy.
    updatedDate: z.date().optional(),
  }),
});

export const collections = {
  blog: blogCollection,
};
