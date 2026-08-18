/* global console */
import { getCollection } from 'astro:content';

import { SitemapStream, streamToPromise } from 'sitemap';

export async function GET() {
  try {
    // Initialize the sitemap stream
    const sitemapStream = new SitemapStream({ hostname: 'https://pinglin.tw' });

    // Add static routes for each language
    const staticRoutes = ['', '/about', '/blog'];

    const languages = ['zh-tw'];

    // Production 308s the no-slash form to the slash form (trailingSlash in
    // vercel.json), so sitemap entries must carry the slash to be canonical.
    // No lastmod on static routes: stamping build time would claim a change
    // on every deploy and erode crawler trust in the field.
    const withSlash = (path: string) => `${path}/`;

    // Add URLs for each language
    languages.forEach((lang) => {
      staticRoutes.forEach((route) => {
        sitemapStream.write({
          url: withSlash(`/${lang}${route}`),
          changefreq: 'weekly',
          priority: route === '' ? 1.0 : 0.8,
        });
      });
    });

    // Add default language routes without prefix
    staticRoutes.forEach((route) => {
      sitemapStream.write({
        url: withSlash(route),
        changefreq: 'weekly',
        priority: route === '' ? 1.0 : 0.8,
      });
    });

    // Get all blog posts (excluding hidden ones)
    const blogPosts = await getCollection('blog', ({ data }) => !data.hidden && !data.draft);

    // Add blog posts for each language
    blogPosts.forEach((post) => {
      const postDate = post.data.pubDate.toISOString();

      // Check if the slug already contains a language prefix
      const slug = post.slug;
      const hasLanguagePrefix = languages.some((lang) => slug.startsWith(`${lang}/`));

      if (hasLanguagePrefix) {
        // If slug already has language prefix, just add it directly
        sitemapStream.write({
          url: withSlash(`/blog/${slug}`),
          lastmod: postDate,
          changefreq: 'monthly',
          priority: 0.7,
        });
      } else {
        // Add default language version
        sitemapStream.write({
          url: withSlash(`/blog/${slug}`),
          lastmod: postDate,
          changefreq: 'monthly',
          priority: 0.7,
        });
      }
    });

    // End the sitemap stream
    sitemapStream.end();

    // Convert the stream to a promise and return as XML
    const sitemap = await streamToPromise(sitemapStream);

    return new Response(sitemap, {
      headers: { 'Content-Type': 'application/xml' },
    });
  } catch (error) {
    console.error('Error generating sitemap:', error);
    return new Response('Error generating sitemap', { status: 500 });
  }
}
