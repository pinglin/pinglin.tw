import type { CollectionEntry } from 'astro:content';

type BlogPost = CollectionEntry<'blog'>;

// The folder decides the edition: src/content/blog/zh-tw/*.md publishes under
// /zh-tw/blog/ only. Every route and index partitions on this one test, so an
// entry can never surface under both prefixes; /blog/zh-tw/... once did, and
// vercel.json still 308s that old shape.
export function isZhTwPost(post: BlogPost): boolean {
  return post.id.startsWith('zh-tw/');
}

// The single public path of a post, in the trailing-slash form production
// canonicalizes to.
export function blogPostPath(post: BlogPost): string {
  return isZhTwPost(post) ? `/zh-tw/blog/${post.slug.split('/').slice(1).join('/')}/` : `/blog/${post.slug}/`;
}
