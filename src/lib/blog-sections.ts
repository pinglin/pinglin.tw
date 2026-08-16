import type { CollectionEntry } from 'astro:content';
import { createHash } from 'node:crypto';
import { fromMarkdown } from 'mdast-util-from-markdown';
import { toString } from 'mdast-util-to-string';
import type { Heading, RootContent } from 'mdast';

export interface BlogSection {
  depth: number;
  slug: string;
  title: string;
  excerpt: string;
}

type BlogPost = CollectionEntry<'blog'>;

const sectionCache = new Map<string, Promise<BlogSection[]>>();

function compactText(value: string): string {
  return value.replace(/\s+/g, ' ').trim();
}

function excerptNodeText(node: RootContent): string {
  // Raw HTML is predominantly figures on this site. Excluding it keeps image
  // tags and long alt attributes out of social-card prose while allowing the
  // following paragraph to become the section excerpt.
  if (node.type === 'html' || node.type === 'code' || node.type === 'definition' || node.type === 'heading') {
    return '';
  }
  return toString(node);
}

async function collectBlogSections(post: BlogPost): Promise<BlogSection[]> {
  const [{ headings }, tree] = await Promise.all([post.render(), Promise.resolve(fromMarkdown(post.body ?? ''))]);
  const markdownHeadings: { node: Heading; index: number }[] = [];
  tree.children.forEach((node, index) => {
    if (node.type === 'heading') markdownHeadings.push({ node, index });
  });

  // Astro is the authority for heading slugs. Pair its rendered heading list
  // with the Markdown AST so routes, controls, and rendered ids stay aligned,
  // including duplicate-heading suffixes.
  return markdownHeadings.flatMap(({ node, index }, headingIndex) => {
    const rendered = headings[headingIndex];
    if (!rendered || (node.depth !== 2 && node.depth !== 3)) return [];

    let end = tree.children.length;
    for (let i = index + 1; i < tree.children.length; i += 1) {
      const candidate = tree.children[i];
      if (candidate.type === 'heading' && candidate.depth <= node.depth) {
        end = i;
        break;
      }
    }

    const excerpt = compactText(
      tree.children
        .slice(index + 1, end)
        .map(excerptNodeText)
        .filter(Boolean)
        .join(' '),
    );

    return [
      {
        depth: node.depth,
        slug: rendered.slug,
        title: rendered.text,
        excerpt,
      },
    ];
  });
}

export function getBlogSections(post: BlogPost): Promise<BlogSection[]> {
  const contentHash = createHash('sha1')
    .update(post.body ?? '')
    .digest('hex')
    .slice(0, 10);
  const key = `${post.id}|${contentHash}`;
  let sections = sectionCache.get(key);
  if (!sections) {
    sections = collectBlogSections(post);
    sectionCache.set(key, sections);
  }
  return sections;
}

export function blogSectionPath(articlePath: string, sectionSlug: string): string {
  const path = articlePath.endsWith('/') ? articlePath : `${articlePath}/`;
  return `${path}sections/${sectionSlug}/`;
}

export function blogSectionOgImagePath(articlePath: string, sectionSlug: string): string {
  return `/og${blogSectionPath(articlePath, sectionSlug).replace(/\/$/, '.png')}`;
}

export function blogSectionOgVersion(post: BlogPost['data'], section: BlogSection): string {
  return createHash('sha256')
    .update([post.title, post.pubDate.toISOString(), section.slug, section.title, section.excerpt].join('\n'))
    .digest('hex')
    .slice(0, 10);
}
