import GithubSlugger from 'github-slugger';

interface HastNode {
  type: string;
  tagName?: string;
  value?: string;
  properties?: Record<string, unknown>;
  children?: HastNode[];
}

function textContent(node: HastNode): string {
  if (node.type === 'text') return node.value ?? '';
  return (node.children ?? []).map(textContent).join('');
}

function sectionCopyButton(id: string, title: string): HastNode {
  const label = `Copy permalink to “${title}”`;
  return {
    type: 'element',
    tagName: 'button',
    properties: {
      type: 'button',
      className: ['section-copy'],
      dataSectionCopy: true,
      dataSectionId: id,
      dataCopyLabel: label,
      ariaLabel: label,
      title: 'Copy section link',
    },
    children: [
      {
        type: 'element',
        tagName: 'svg',
        properties: {
          viewBox: '0 0 24 24',
          fill: 'none',
          stroke: 'currentColor',
          strokeWidth: 2,
          strokeLinecap: 'round',
          strokeLinejoin: 'round',
          ariaHidden: 'true',
        },
        children: [
          {
            type: 'element',
            tagName: 'path',
            properties: {
              d: 'M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71',
            },
            children: [],
          },
          {
            type: 'element',
            tagName: 'path',
            properties: {
              d: 'M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71',
            },
            children: [],
          },
        ],
      },
    ],
  };
}

export function rehypeSectionLinks() {
  return function transform(tree: HastNode) {
    const slugger = new GithubSlugger();

    function visit(node: HastNode) {
      if (node.type === 'element' && /^h[1-6]$/.test(node.tagName ?? '')) {
        const title = textContent(node).trim();
        // Astro assigns ids after user rehype plugins. Generating the same
        // GitHub-compatible id here lets us inject the copy control without a
        // second client-side slugging implementation.
        const generatedId = slugger.slug(title);
        node.properties ??= {};
        const id = typeof node.properties.id === 'string' ? node.properties.id : generatedId;
        node.properties.id = id;

        if (node.tagName === 'h2' || node.tagName === 'h3') {
          node.children = [...(node.children ?? []), sectionCopyButton(id, title)];
        }
      }
      node.children?.forEach(visit);
    }

    visit(tree);
  };
}
