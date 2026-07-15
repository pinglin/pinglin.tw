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
      // theme-paired hero. `url` stays the canonical (dark + OG) image.
      urlLight: z.string().optional(),
      alt: z.string(),
    }),
    tags: z.array(z.string()),
    lang: z.string().optional().default('en'),
    // Hidden posts stay reachable at their URL but are excluded from the
    // blog and tag listing pages.
    hidden: z.boolean().optional().default(false),
    pubDate: z.date(),
  }),
});

export const collections = {
  blog: blogCollection,
};
