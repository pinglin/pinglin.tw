import { defineCollection, z } from 'astro:content';

const blogCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    author: z.string(),
    description: z.string(),
    image: z.object({
      url: z.string(),
      alt: z.string(),
    }),
    tags: z.array(z.string()),
    lang: z.string().optional().default('en'),
    pubDate: z.date(),
  }),
});

export const collections = {
  blog: blogCollection,
};
