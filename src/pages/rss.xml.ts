import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { getCollection } from 'astro:content';
import { stat } from 'node:fs/promises';
import { resolve } from 'node:path';
import site from '@data/site.json';

async function getFileSize(publicPath: string): Promise<number> {
  try {
    const filePath = resolve(`public${publicPath}`);
    const stats = await stat(filePath);
    return stats.size;
  } catch {
    return 0;
  }
}

export async function GET(context: APIContext) {
  const posts = (await getCollection('blog', ({ data }) => !data.draft)).sort(
    (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf()
  );

  const siteUrl = context.site!.toString();

  const items = await Promise.all(
    posts.map(async (post) => {
      const imagePath = post.data.image?.src || `/og/${post.id}.png`;
      const isJpeg = imagePath.endsWith('.jpg') || imagePath.endsWith('.jpeg');
      const length = isJpeg ? 0 : await getFileSize(imagePath);

      return {
        title: post.data.title,
        pubDate: post.data.pubDate,
        description: post.data.description,
        link: `/blog/${post.id}`,
        enclosure: {
          url: new URL(imagePath, siteUrl).toString(),
          length,
          type: isJpeg ? 'image/jpeg' : 'image/png',
        },
      };
    })
  );

  return rss({
    title: site.title,
    description: site.description,
    site: siteUrl,
    items,
  });
}
