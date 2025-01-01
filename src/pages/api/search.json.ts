import type { APIRoute } from 'astro';
import { getCollection, type CollectionEntry } from 'astro:content';

export const GET: APIRoute = async ({ url }) => {
  const query = url.searchParams.get('q') || '';

  if (query.length < 1) {
    return new Response(JSON.stringify({ results: [] }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  const allPosts = await getCollection('blog');

  const results = allPosts
    .filter((post: CollectionEntry<'blog'>) => {
      const searchText = query.toLowerCase().trim();
      const title = post.data.title.toLowerCase();
      const body = post.body.toLowerCase();

      return title.includes(searchText) || body.includes(searchText);
    })
    .map((post: CollectionEntry<'blog'>) => ({
      title: post.data.title,
      url: `/blog/${post.slug}`,
      excerpt: post.body.substring(0, 100) + '...',
    }));

  return new Response(JSON.stringify({ results }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
    },
  });
};
