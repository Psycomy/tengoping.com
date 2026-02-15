# Blog Content Skills Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create two Claude Code skills (`blog-plan` and `blog-write`) that automate the editorial planning and article creation pipeline for tengoping.com.

**Architecture:** Two independent skills in `~/.claude/skills/`. `blog-plan` handles monthly editorial calendar generation with gap analysis. `blog-write` handles research, article writing, and thumbnail generation. Both interact via plan documents in `docs/plans/`.

**Tech Stack:** Claude Code skills (SKILL.md), Astro content collections, `generate-images.py` script, WebSearch for research.

---

### Task 1: Write `blog-plan` SKILL.md

**Files:**
- Create: `~/.claude/skills/blog-plan/SKILL.md`

**Step 1: Create the skill directory**

```bash
mkdir -p ~/.claude/skills/blog-plan
```

**Step 2: Write the SKILL.md**

Write `~/.claude/skills/blog-plan/SKILL.md` with:

**Frontmatter:**
```yaml
---
name: blog-plan
description: Use when planning monthly blog content for tengoping.com — editorial calendar, gap analysis, topic selection for 4 weekly articles
---
```

**Body must include:**

1. **Overview** — One-sentence purpose: plan 4 articles/month with gap analysis
2. **When to Use** — Beginning of month, when needing content ideas, when asked to plan articles
3. **Process flowchart** (graphviz):
   - Scan existing posts (Glob `src/content/blog/*.md`, read frontmatter)
   - Analyze gaps (categories with few posts, underused tags)
   - Optionally WebSearch for trending topics
   - Present analysis + suggestions to user
   - Negotiate 4 topics one-by-one (ask category, author, brief for each)
   - Save plan to `docs/plans/YYYY-MM-blog-plan.md`
4. **Plan document template** — markdown template with fields: título, categoría, tags, autor, brief, fecha, estado (pendiente/completado)
5. **Available categories** — list the 8 existing categories with current post counts
6. **Available authors** — antonio, alois, eloculto (ask per article)
7. **Gap analysis instructions** — how to scan and count posts per category/tag
8. **Common mistakes** — don't suggest topics already covered, always check existing posts first

**Step 3: Verify skill is discoverable**

```bash
ls ~/.claude/skills/blog-plan/SKILL.md
```

**Step 4: Commit**

```bash
cd ~/.claude/skills && git init 2>/dev/null; git add blog-plan/SKILL.md && git commit -m "feat: add blog-plan skill for monthly editorial planning"
```

---

### Task 2: Test `blog-plan` skill with subagent (RED → GREEN)

**Step 1: Baseline test (RED) — without loading the skill**

Launch a subagent (Task tool, type general-purpose) with this prompt:
> "I need to plan 4 blog articles for March 2026 for the blog at /home/antonio/Documentos/blog. The blog is about Linux sysadmin topics in Spanish. Analyze what topics are already covered and suggest 4 new articles with categories, tags, and authors."

Document: Does the agent scan existing posts? Does it check for gaps? Does it produce a structured plan document? What does it miss?

**Step 2: Skill test (GREEN) — with the skill loaded**

Launch a subagent with:
> "Use the blog-plan skill at ~/.claude/skills/blog-plan/SKILL.md. Plan 4 blog articles for March 2026 for the blog at /home/antonio/Documentos/blog."

Verify: Agent follows the flowchart, scans posts, identifies gaps, asks about authors, produces properly formatted plan document.

**Step 3: Document findings**

Note any rationalizations or deviations. These feed into Task 5 (refactor).

---

### Task 3: Write `blog-write` SKILL.md

**Files:**
- Create: `~/.claude/skills/blog-write/SKILL.md`

**Step 1: Create the skill directory**

```bash
mkdir -p ~/.claude/skills/blog-write
```

**Step 2: Write the SKILL.md**

Write `~/.claude/skills/blog-write/SKILL.md` with:

**Frontmatter:**
```yaml
---
name: blog-write
description: Use when writing a blog article for tengoping.com — researches topic, writes markdown with frontmatter, generates terminal-style thumbnail
---
```

**Body must include:**

1. **Overview** — Research, write, and publish articles for tengoping.com
2. **When to Use** — When asked to write a blog article, when executing items from a blog-plan
3. **Process flowchart** (graphviz):
   - Receive topic (from plan or user)
   - Ask author (antonio/alois/eloculto)
   - Ask draft status (draft: true/false)
   - Research: WebSearch for current topics, own knowledge for stable tech
   - Write article with full frontmatter
   - Save to `src/content/blog/{slug}.md`
   - Run `python3 scripts/generate-images.py --auto`
   - Verify file + image exist
   - If from plan, mark as completed in plan doc
4. **Frontmatter template:**
   ```yaml
   ---
   title: ""
   description: ""
   author: ""
   pubDate: YYYY-MM-DD
   category: ""
   tags: []
   image: "/images/{slug}.jpg"
   draft: true/false
   ---
   ```
5. **Content style guide:**
   - Language: Spanish, professional tone
   - Structure: h2/h3 hierarchy
   - Code examples: always include practical bash/yaml/etc.
   - Audience: experienced sysadmins
   - Length: variable (guides 1500-2500 words, opinions 800-1200 words)
   - Slug: kebab-case, no accents, derived from title
6. **Research strategy:**
   - Current/trending topics → WebSearch first, then synthesize
   - Stable technical topics → Claude's knowledge, cite official docs
   - Mixed → combine both sources
7. **Available categories** — list the 8 categories
8. **Thumbnail generation** — exact command: `python3 scripts/generate-images.py --auto`
   - Script reads frontmatter from the new post
   - Generates 800x500 JPEG in `public/images/`
   - Requires: image field in frontmatter pointing to `/images/{filename}.jpg`
9. **Plan integration** — how to read `docs/plans/YYYY-MM-blog-plan.md` and mark articles as completed
10. **Common mistakes:**
    - Don't forget `image` field in frontmatter (needed for --auto)
    - Slug must match image filename
    - Don't generate content that duplicates existing posts
    - Always verify the article renders (check frontmatter valid)

**Step 3: Verify skill is discoverable**

```bash
ls ~/.claude/skills/blog-write/SKILL.md
```

**Step 4: Commit**

```bash
cd ~/.claude/skills && git add blog-write/SKILL.md && git commit -m "feat: add blog-write skill for article creation with thumbnail generation"
```

---

### Task 4: Test `blog-write` skill with subagent (RED → GREEN)

**Step 1: Baseline test (RED) — without loading the skill**

Launch a subagent with:
> "Write a blog article about setting up WireGuard VPN on Ubuntu for the blog at /home/antonio/Documentos/blog. The blog is in Spanish, uses Astro with markdown content in src/content/blog/. Save the article and generate a thumbnail."

Document: Does it get the frontmatter right? Does it run the image script? Does it match the blog's tone and style?

**Step 2: Skill test (GREEN) — with the skill loaded**

Launch a subagent with:
> "Use the blog-write skill at ~/.claude/skills/blog-write/SKILL.md. Write a blog article about configuring Nginx reverse proxy with SSL. Save it to the blog at /home/antonio/Documentos/blog."

Verify: Correct frontmatter, asks for author, asks for draft status, runs generate-images.py, verifies output.

**Step 3: Document findings**

Note deviations for refactoring.

---

### Task 5: Refactor both skills (close loopholes)

**Step 1: Review test findings from Tasks 2 and 4**

Identify:
- What rationalizations did agents use to skip steps?
- What parts of the flowchart were ignored?
- Were there formatting/content issues?

**Step 2: Update SKILL.md files**

Add:
- Explicit counters for observed rationalizations
- Red flags list
- Rationalization table (if discipline issues found)
- Any missing instructions

**Step 3: Re-test with subagent**

Run the GREEN tests again to verify fixes work.

**Step 4: Commit**

```bash
cd ~/.claude/skills && git add -A && git commit -m "refactor: close loopholes in blog skills based on testing"
```

---

### Task 6: Final verification

**Step 1: Test full workflow end-to-end**

1. Invoke `blog-plan` to plan March 2026
2. Pick one article from the plan
3. Invoke `blog-write` to write that article
4. Verify: article exists, image exists, plan updated

**Step 2: Clean up test artifacts**

Delete any test articles created during testing (unless user wants to keep them).

**Step 3: Final commit**

Commit any remaining changes.
