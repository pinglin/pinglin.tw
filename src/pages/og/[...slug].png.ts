import type { APIRoute } from 'astro';
import type { CollectionEntry } from 'astro:content';
import { getCollection } from 'astro:content';
import { getBlogSections, type BlogSection } from '../../lib/blog-sections';
import { blogPostPath } from '../../lib/blog-paths';
import { renderSectionOgImage } from '../../lib/section-og';

export const prerender = true;

interface SectionImageProps {
  entry: CollectionEntry<'blog'>;
  section: BlogSection;
}

export async function getStaticPaths() {
  const entries = await getCollection('blog', ({ data }) => (import.meta.env.PROD ? !data.draft : true));
  const paths = await Promise.all(
    entries.map(async (entry) => {
      const sections = await getBlogSections(entry);
      // One image per section, under the article's only public path.
      const imageRoot = blogPostPath(entry).replace(/^\/|\/$/g, '');
      return sections.map((section) => ({
        params: { slug: `${imageRoot}/sections/${section.slug}` },
        props: { entry, section } satisfies SectionImageProps,
      }));
    }),
  );
  return paths.flat();
}

export const GET: APIRoute = async ({ props }) => {
  const { entry, section } = props as SectionImageProps;
  const png = await renderSectionOgImage({
    articleTitle: entry.data.title,
    sectionTitle: section.title,
    excerpt: section.excerpt || entry.data.description,
    lang: entry.data.lang,
  });
  return new Response(new Uint8Array(png), {
    headers: {
      'Content-Type': 'image/png',
      'Cache-Control': 'public, max-age=31536000, immutable',
    },
  });
};
