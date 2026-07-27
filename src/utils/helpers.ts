export function formatDate(date: Date): string {
  return new Date(date).toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export function slugify(text: string): string {
  return text
    .toString()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/-+/g, '-');
}

// Variantes WebP pregeneradas en public/images/avatars/ (node + sharp).
// 56 → render 28px (ArticleCard), 160 → render 80px (AuthorCard, sobre-nosotros),
// 400 → render ~300px (página de autor). Regenerar al cambiar los PNG originales.
export function avatarVariant(avatar: string, size: 56 | 160 | 400): string {
  return avatar.replace('/images/', '/images/avatars/').replace(/\.png$/i, `-${size}.webp`);
}

export function getUniqueCategories(posts: { data: { category: string } }[]): string[] {
  const categories = posts.map((post) => post.data.category);
  return [...new Set(categories)].sort();
}

export function getUniqueTags(posts: { data: { tags: string[] } }[]): string[] {
  const tags = posts.flatMap((post) => post.data.tags);
  const seenSlugs = new Set<string>();
  const unique: string[] = [];
  for (const tag of tags) {
    const slug = slugify(tag);
    if (!seenSlugs.has(slug)) {
      seenSlugs.add(slug);
      unique.push(tag);
    }
  }
  return unique.sort();
}
