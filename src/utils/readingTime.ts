export function getReadingTime(content: string): number {
  const wordsPerMinute = 160;
  const words = content.trim().split(/\s+/).length;
  return Math.max(1, Math.ceil(words / wordsPerMinute));
}
