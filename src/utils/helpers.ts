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

export function getUniqueCategories(posts: { data: { category: string } }[]): string[] {
  const categories = posts.map((post) => post.data.category);
  return [...new Set(categories)].sort();
}

export function getUniqueTags(posts: { data: { tags: string[] } }[]): string[] {
  const tags = posts.flatMap((post) => post.data.tags);
  return [...new Set(tags)].sort();
}
