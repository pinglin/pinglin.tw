import { getCollection } from 'astro:content';
import rss from '@astrojs/rss';

export async function GET(context) {
  const posts = await getCollection('blog', ({ data }) => data.lang === 'en');

  // Generate the RSS feed
  const rssResponse = await rss({
    title: 'Ping-Lin Chang',
    description: 'A space where my thoughts take flight.',
    site: context.site,
    items: posts.map((post) => ({
      title: post.data.title,
      pubDate: post.data.pubDate,
      description: post.data.description,
      link: `${context.site}blog/${post.slug}/`,
    })),
    customData: '<language>en-us</language>',
    stylesheet: '/rss-styles.xsl',
  });

  // Get the RSS content as text
  const rssString = await rssResponse.text();

  return new Response(rssString, {
    status: 200,
    headers: {
      'Content-Type': 'application/xml;charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
}
