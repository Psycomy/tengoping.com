import type { APIRoute, GetStaticPaths } from 'astro';
import { getCollection } from 'astro:content';
import satori from 'satori';
import { Resvg } from '@resvg/resvg-js';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

let fontData: ArrayBuffer | null = null;

async function loadFont(): Promise<ArrayBuffer> {
  if (fontData) return fontData;
  const fontPath = resolve('public/fonts/JetBrainsMono-Regular.ttf');
  const buffer = await readFile(fontPath);
  fontData = buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
  return fontData;
}

export const getStaticPaths = (async () => {
  const posts = await getCollection('blog', ({ data }) => !data.draft);
  return posts.map((post) => ({
    params: { id: post.id },
    props: { title: post.data.title, category: post.data.category },
  }));
}) satisfies GetStaticPaths;

export const GET: APIRoute = async ({ props }) => {
  const { title, category } = props as { title: string; category: string };
  const font = await loadFont();

  const svg = await satori(
    {
      type: 'div',
      props: {
        style: {
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          width: '100%',
          height: '100%',
          padding: '60px',
          backgroundColor: '#0D1117',
          fontFamily: 'JetBrains Mono',
          color: '#E6EDF3',
        },
        children: [
          {
            type: 'div',
            props: {
              style: { display: 'flex', flexDirection: 'column', gap: '20px' },
              children: [
                {
                  type: 'div',
                  props: {
                    style: {
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      fontSize: '18px',
                      color: '#8B949E',
                    },
                    children: [
                      {
                        type: 'span',
                        props: { style: { color: '#58D5A2' }, children: '$' },
                      },
                      {
                        type: 'span',
                        props: { children: `cat ./blog/${category.toLowerCase()}/` },
                      },
                    ],
                  },
                },
                {
                  type: 'div',
                  props: {
                    style: {
                      display: 'flex',
                      padding: '8px 16px',
                      border: '1px solid #30363D',
                      backgroundColor: '#161B22',
                      color: '#FF6D00',
                      fontSize: '16px',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                    },
                    children: category,
                  },
                },
                {
                  type: 'h1',
                  props: {
                    style: {
                      fontSize: title.length > 60 ? '36px' : '44px',
                      fontWeight: 700,
                      lineHeight: 1.2,
                      color: '#E6EDF3',
                      marginTop: '12px',
                    },
                    children: title,
                  },
                },
              ],
            },
          },
          {
            type: 'div',
            props: {
              style: {
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderTop: '1px solid #30363D',
                paddingTop: '24px',
              },
              children: [
                {
                  type: 'span',
                  props: {
                    style: { fontSize: '22px', fontWeight: 700, color: '#58D5A2' },
                    children: 'root@tengoping:~$_',
                  },
                },
                {
                  type: 'span',
                  props: {
                    style: { fontSize: '18px', color: '#8B949E' },
                    children: 'tengoping.com',
                  },
                },
              ],
            },
          },
        ],
      },
    },
    {
      width: 1200,
      height: 630,
      fonts: [
        {
          name: 'JetBrains Mono',
          data: font,
          weight: 400,
          style: 'normal',
        },
      ],
    }
  );

  const resvg = new Resvg(svg, {
    fitTo: { mode: 'width', value: 1200 },
  });
  const png = resvg.render().asPng();

  return new Response(png, {
    headers: { 'Content-Type': 'image/png' },
  });
};
