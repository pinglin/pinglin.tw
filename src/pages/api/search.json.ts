import type { APIRoute } from 'astro';
import { getCollection, type CollectionEntry } from 'astro:content';

export const GET: APIRoute = async ({ url }) => {
  const query = url.searchParams.get('q')?.toLowerCase() || '';

  if (query.length < 3) {
    return new Response(JSON.stringify({ results: [] }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  const allPosts = await getCollection('blog');
  const results = allPosts
    .filter(
      (post: CollectionEntry<'blog'>) =>
        post.data.title.toLowerCase().includes(query) ||
        post.body.toLowerCase().includes(query),
    )
    .map((post: CollectionEntry<'blog'>) => ({
      title: post.data.title,
      url: `/blog/${post.slug}`,
      excerpt: post.body.substring(0, 300) + '...',
    }));

  return new Response(JSON.stringify({ results }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
    },
  });
};
