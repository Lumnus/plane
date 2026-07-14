# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# Lumnus singular-store body helpers.
#
# The MD+YAML-frontmatter body (description_md / comment_md) is the SINGLE canonical
# store; HTML (+stripped) are server-derived projections regenerated on every save —
# a deterministic function of the markdown, never independently writable. An HTML-only
# writer at any API boundary gets converted html→md so markdown stays the source.
#
# Renderer is markdown-it-py — the Python port of markdown-it, the SAME parser family
# the web editor uses (tiptap-markdown → markdown-it, html:true, breaks:true) — so the
# server projection and the editor render agree.

import re

from markdown_it import MarkdownIt
from markdownify import markdownify
from mdit_py_plugins.tasklists import tasklists_plugin

# Only a block starting at the very first character is frontmatter (mirrors the
# TS splitMarkdownFrontmatter in @plane/utils).
FRONTMATTER_RE = re.compile(r"^---\r?\n[\s\S]*?\r?\n---[ \t]*(?:\r?\n|$)")

_md_renderer = (
    MarkdownIt("gfm-like", {"html": True, "breaks": True, "linkify": True})
    .use(tasklists_plugin)
)


def split_markdown_frontmatter(markdown_text):
    """Return (frontmatter_block_or_None, body). Frontmatter keeps its --- fences."""
    if not markdown_text:
        return None, ""
    match = FRONTMATTER_RE.match(markdown_text)
    if not match:
        return None, markdown_text
    return match.group(0).rstrip("\n"), markdown_text[match.end():]


def render_markdown_to_html(markdown_text):
    """Render a markdown BODY (no frontmatter) to display HTML."""
    if not markdown_text or not markdown_text.strip():
        return "<p></p>"
    return _md_renderer.render(markdown_text)


def derive_html_from_markdown(markdown_text):
    """Full derivation: strip the agent-owned YAML frontmatter, render the body."""
    _, body = split_markdown_frontmatter(markdown_text)
    return render_markdown_to_html(body)


def convert_html_to_markdown(html_text):
    """Boundary conversion for html-only writers: editor/legacy HTML → markdown.

    ATX headings + '-' bullets to match the editor-side serializer's register.
    """
    if not html_text:
        return ""
    md = markdownify(
        html_text,
        heading_style="ATX",
        bullets="-",
        # AI-native store: don't backslash-escape prose that merely resembles markdown
        escape_asterisks=False,
        escape_underscores=False,
        escape_misc=False,
    )
    # collapse the >2 blank lines markdownify tends to leave around block elements
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return md + "\n" if md else ""
