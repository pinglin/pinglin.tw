import type { CollectionEntry } from 'astro:content';
import { getCollection } from 'astro:content';

// Union listing: every visible post appears exactly once, in the page's
// preferred language when a translation exists, otherwise in whichever
// language the post was written.
export async function getListingPosts(preferred: 'en' | 'zh-tw'): Promise<CollectionEntry<'blog'>[]> {
  const all = await getCollection('blog', ({ data }) => !data.hidden);

  const baseSlug = (entry: CollectionEntry<'blog'>) => (entry.id.startsWith('zh-tw/') ? entry.slug.split('/').slice(1).join('/') : entry.slug);

  const byBase = new Map<string, CollectionEntry<'blog'>[]>();
  for (const entry of all) {
    const base = baseSlug(entry);
    const variants = byBase.get(base);
    if (variants) variants.push(entry);
    else byBase.set(base, [entry]);
  }

  return [...byBase.values()]
    .map((variants) => variants.find((entry) => entry.data.lang === preferred) ?? variants[0])
    .sort((a, b) => new Date(b.data.pubDate).valueOf() - new Date(a.data.pubDate).valueOf());
}
