import { Resvg } from '@resvg/resvg-js';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import satori from 'satori';

const require = createRequire(import.meta.url);
const readFont = (specifier: string) => readFileSync(require.resolve(specifier));
const ibmPlex400 = readFont('@fontsource/ibm-plex-sans/files/ibm-plex-sans-latin-400-normal.woff');
const ibmPlex600 = readFont('@fontsource/ibm-plex-sans/files/ibm-plex-sans-latin-600-normal.woff');
const notoTc400 = readFont('@fontsource/noto-sans-tc/files/noto-sans-tc-chinese-traditional-400-normal.woff');
const notoTc600 = readFont('@fontsource/noto-sans-tc/files/noto-sans-tc-chinese-traditional-600-normal.woff');

const PAPER = '#fcfcfb';
const INK = '#0b0b0b';
const BODY = '#52514e';
const MUTED = '#898781';
const ORANGE = '#eb6834';
const BLUE = '#2a78d6';

const box = (style: Record<string, unknown>, children?: unknown) => ({
  type: 'div',
  props: { style: { display: 'flex', ...style }, children },
});

function excerptText(value: string, isCJK: boolean): string {
  const max = isCJK ? 108 : 250;
  if (value.length <= max) return value;
  const slice = value.slice(0, max);
  if (isCJK) {
    const cut = Math.max(slice.lastIndexOf('。'), slice.lastIndexOf('，'), slice.lastIndexOf('、'), slice.lastIndexOf('？'), slice.lastIndexOf('！'));
    return `${cut >= 42 ? value.slice(0, cut + 1) : slice}…`;
  }
  const sentenceEnd = Math.max(slice.lastIndexOf('. '), slice.lastIndexOf('? '), slice.lastIndexOf('! '));
  if (sentenceEnd >= 100) return value.slice(0, sentenceEnd + 1);
  const wordEnd = slice.lastIndexOf(' ');
  return `${value.slice(0, wordEnd > 0 ? wordEnd : max).trimEnd()}…`;
}

function sectionTitleSize(title: string, isCJK: boolean): number {
  if (isCJK) return title.length <= 20 ? 54 : title.length <= 32 ? 46 : 40;
  return title.length <= 40 ? 58 : title.length <= 70 ? 49 : 42;
}

export async function renderSectionOgImage({
  articleTitle,
  sectionTitle,
  excerpt,
  lang = 'en',
}: {
  articleTitle: string;
  sectionTitle: string;
  excerpt: string;
  lang?: string;
}): Promise<Uint8Array> {
  const isCJK = lang === 'zh-tw';
  const body = excerptText(excerpt, isCJK);
  const family = isCJK ? 'IBM Plex Sans, Noto Sans TC' : 'IBM Plex Sans';
  const fonts: Parameters<typeof satori>[1]['fonts'] = [
    { name: 'IBM Plex Sans', data: ibmPlex400, weight: 400, style: 'normal' },
    { name: 'IBM Plex Sans', data: ibmPlex600, weight: 600, style: 'normal' },
    ...(isCJK
      ? [
          { name: 'Noto Sans TC', data: notoTc400, weight: 400, style: 'normal' } as const,
          { name: 'Noto Sans TC', data: notoTc600, weight: 600, style: 'normal' } as const,
      ]
      : []),
  ];

  const tree = box(
    {
      flexDirection: 'column',
      width: '1200px',
      height: '630px',
      backgroundColor: PAPER,
      fontFamily: family,
    },
    [
      box(
        {
          flexDirection: 'column',
          justifyContent: 'space-between',
          flexGrow: 1,
          padding: '54px 72px 50px',
          borderTop: `14px solid ${ORANGE}`,
        },
        [
          box({ alignItems: 'center', justifyContent: 'space-between' }, [
            box({ fontSize: '30px', fontWeight: 600, color: INK }, 'pinglin.tw'),
            box(
              {
                fontSize: '18px',
                fontWeight: 600,
                color: BLUE,
                letterSpacing: isCJK ? '1.5px' : '2.4px',
              },
              isCJK ? '文章段落' : 'ARTICLE SECTION',
            ),
          ]),
          box({ flexDirection: 'column', marginTop: '28px' }, [
            box(
              {
                fontSize: isCJK ? '21px' : '23px',
                fontWeight: 400,
                color: MUTED,
                lineHeight: 1.25,
                marginBottom: '14px',
              },
              articleTitle,
            ),
            box(
              {
                fontSize: `${sectionTitleSize(sectionTitle, isCJK)}px`,
                fontWeight: 600,
                color: INK,
                lineHeight: isCJK ? 1.24 : 1.08,
                letterSpacing: isCJK ? '0px' : '-0.5px',
              },
              sectionTitle,
            ),
            ...(body
              ? [
                box(
                  {
                    fontSize: isCJK ? '24px' : '26px',
                    fontWeight: 400,
                    color: BODY,
                    lineHeight: isCJK ? 1.52 : 1.4,
                    marginTop: '20px',
                    maxWidth: '1040px',
                  },
                  body,
                ),
              ]
              : []),
          ]),
          box({ justifyContent: 'space-between', alignItems: 'center' }, [
            box({ fontSize: '18px', fontWeight: 600, color: ORANGE }, isCJK ? '閱讀這個段落' : 'Read this section'),
            box({ fontSize: '18px', fontWeight: 400, color: MUTED }, 'Ping-Lin Chang'),
          ]),
        ],
      ),
    ],
  );

  const svg = await satori(tree as Parameters<typeof satori>[0], {
    width: 1200,
    height: 630,
    fonts,
  });
  const resvg = new Resvg(svg, { fitTo: { mode: 'width', value: 1200 } });
  // resvg bundles a different @types/node revision than the app. Both sides
  // are the same Uint8Array at runtime; expose the portable byte type here so
  // the prerendered route does not couple to either Buffer declaration.
  return resvg.render().asPng() as unknown as Uint8Array;
}
