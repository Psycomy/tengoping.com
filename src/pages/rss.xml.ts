import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { getCollection } from 'astro:content';
import site from '@data/site.json';

export async function GET(context: APIContext) {
  const posts = (await getCollection('blog', ({ data }) => !data.draft)).sort(
    (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf()
  );

  const siteUrl = context.site!.toString();

  const items = posts.map((post) => ({
    title: post.data.title,
    pubDate: post.data.pubDate,
    description: post.data.description,
    link: `/blog/${post.id}`,
    enclosure: {
      url: new URL(`/og/${post.id}.png`, siteUrl).toString(),
      length: 0,
      type: 'image/png',
    },
  }));

  return rss({
    title: site.title,
    description: site.description,
    site: siteUrl,
    items,
  });
}
