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

    // Add URLs for each language
    languages.forEach((lang) => {
      staticRoutes.forEach((route) => {
        sitemapStream.write({
          url: `/${lang}${route}`,
          changefreq: 'weekly',
          priority: route === '' ? 1.0 : 0.8,
          lastmod: new Date().toISOString(),
        });
      });
    });

    // Add default language routes without prefix
    staticRoutes.forEach((route) => {
      sitemapStream.write({
        url: route,
        changefreq: 'weekly',
        priority: route === '' ? 1.0 : 0.8,
        lastmod: new Date().toISOString(),
      });
    });

    // Get all blog posts
    const blogPosts = await getCollection('blog');

    // Add blog posts for each language
    blogPosts.forEach((post) => {
      const postDate = post.data.pubDate.toISOString();

      // Check if the slug already contains a language prefix
      const slug = post.slug;
      const hasLanguagePrefix = languages.some((lang) => slug.startsWith(`${lang}/`));

      if (hasLanguagePrefix) {
        // If slug already has language prefix, just add it directly
        sitemapStream.write({
          url: `/blog/${slug}`,
          lastmod: postDate,
          changefreq: 'monthly',
          priority: 0.7,
        });
      } else {
        // Add default language version
        sitemapStream.write({
          url: `/blog/${slug}`,
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
