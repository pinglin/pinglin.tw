import { getCollection } from 'astro:content';
import rss from '@astrojs/rss';

export async function GET(context) {
  const posts = await getCollection('blog', ({ data }) => data.lang === 'en');
  return rss({
    title: 'pinglin.io',
    description: 'Pinglin\'s notes.',
    site: context.site,
    items: posts.map((post) => ({
      title: post.data.title,
      pubDate: post.data.pubDate,
      description: post.data.description,
      link: `/blog/${post.slug}/`,
    })),
    customData: '<language>en-us</language>',
    stylesheet: '/rss-styles.xsl',
  });
}
