/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// YAML-frontmatter handling for the MD-canonical description body (description_md).
// The frontmatter block is agent-owned metadata; the human editor renders/edits only
// the body and must preserve the frontmatter verbatim across save round-trips.

export type TMarkdownFrontmatterSplit = {
  /** The raw frontmatter block INCLUDING the `---` fences, or null when absent. */
  frontmatter: string | null;
  /** The markdown body with the frontmatter block removed. */
  body: string;
};

const FRONTMATTER_REGEX = /^---\r?\n[\s\S]*?\r?\n---[ \t]*(?:\r?\n|$)/;

/**
 * @description Split a markdown document into its YAML frontmatter block (if any) and body.
 * Only a block that starts at the very first character is treated as frontmatter.
 */
export const splitMarkdownFrontmatter = (markdown: string | null | undefined): TMarkdownFrontmatterSplit => {
  if (!markdown) return { frontmatter: null, body: "" };
  const match = markdown.match(FRONTMATTER_REGEX);
  if (!match) return { frontmatter: null, body: markdown };
  return {
    frontmatter: match[0].replace(/\r?\n$/, ""),
    body: markdown.slice(match[0].length),
  };
};

/**
 * @description Re-compose a markdown document from a preserved frontmatter block and an
 * (edited) body. Inverse of splitMarkdownFrontmatter.
 */
export const composeMarkdownWithFrontmatter = (frontmatter: string | null | undefined, body: string): string => {
  if (!frontmatter) return body;
  return `${frontmatter}\n${body.startsWith("\n") ? body.slice(1) : body}`;
};
