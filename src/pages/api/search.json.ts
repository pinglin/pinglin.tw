import type { APIRoute } from 'astro';
import { getCollection, type CollectionEntry } from 'astro:content';
import { blogPostPath } from '../../lib/blog-paths';

export const prerender = false;

export const GET: APIRoute = async ({ url }) => {
  const query = url.searchParams.get('q') || '';
  const lang = url.searchParams.get('lang') || 'en';

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

      return post.data.lang === lang && !post.data.draft && (title.includes(searchText) || body.includes(searchText));
    })
    .map((post: CollectionEntry<'blog'>) => ({
      title: post.data.title,
      url: blogPostPath(post),
      excerpt: post.body.substring(0, 100) + '...',
    }));

  return new Response(JSON.stringify({ results }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
    },
  });
};
