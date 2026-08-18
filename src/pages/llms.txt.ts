import { getCollection } from 'astro:content';

// llms.txt (https://llmstxt.org): a plain-text index for AI crawlers and
// answer engines. Mirrors the sitemap's visibility rules — hidden and draft
// posts stay out.
export async function GET() {
  const posts = (await getCollection('blog', ({ data }) => !data.hidden && !data.draft)).sort(
    (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf(),
  );

  const site = 'https://pinglin.tw';
  const lines = [
    '# pinglin.tw',
    '',
    '> Personal site of Ping-Lin Chang (張秉霖) — entrepreneur working on AI and data. Essays on AI, engineering, and building things, in English and Traditional Chinese.',
    '',
    '## Pages',
    '',
    `- [About](${site}/about/): Who Ping-Lin Chang is`,
    `- [Blog](${site}/blog/): All posts`,
    `- [RSS feed](${site}/rss.xml)`,
    '',
    '## Blog posts',
    '',
    ...posts.map((post) => `- [${post.data.title}](${site}/blog/${post.slug}/): ${post.data.description}`),
    '',
  ];

  return new Response(lines.join('\n'), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
