"""
Test invariants for _heading_block function.

These tests ensure:
1. Anchors are placed immediately before headings (no blank line)
2. No inline HTML in heading text
3. Token sanitization for HTML id attributes
"""
import pytest
import re
from merger.lenskit.core import merge


def test_anchor_immediately_before_heading_no_blank_line():
    """
    Test that the anchor appears on the line immediately before the heading
    with no blank line in between.
    
    This is critical for maintaining the association between anchor and heading
    across different Markdown renderers.
    """
    result = merge._heading_block(2, "test-token", "Test Title")
    
    # Find the anchor line and heading line
    anchor_idx = None
    heading_idx = None
    
    for i, line in enumerate(result):
        if '<a id="test-token"></a>' in line:
            anchor_idx = i
        if line.startswith("## ") and "Test Title" in line:
            heading_idx = i
    
    assert anchor_idx is not None, "Anchor not found in output"
    assert heading_idx is not None, "Heading not found in output"
    
    # Critical invariant: heading must be exactly 1 line after anchor (no blank line)
    assert heading_idx == anchor_idx + 1, (
        f"Heading must immediately follow anchor (no blank line). "
        f"Anchor at index {anchor_idx}, heading at {heading_idx}"
    )
    
    # Verify the line between them is the heading, not blank
    assert result[heading_idx].strip() != "", "Line after anchor must not be blank"


def test_no_inline_html_in_heading_text():
    """
    Test that HTML anchor tags are NOT embedded inside the heading text.
    
    This prevents rendering issues where the HTML would be visible in the
    rendered heading or break TOC generation.
    """
    result = merge._heading_block(2, "test-token", "Test Title")
    
    # Find the heading line
    heading_line = None
    for line in result:
        if line.startswith("## "):
            heading_line = line
            break
    
    assert heading_line is not None, "Heading not found in output"
    
    # Critical invariant: no HTML tags in the heading text itself
    assert "<a " not in heading_line, (
        f"Heading text must not contain inline HTML anchor. Found: {heading_line}"
    )
    assert "</a>" not in heading_line, (
        f"Heading text must not contain closing anchor tag. Found: {heading_line}"
    )
    
    # Heading should be clean markdown
    assert heading_line == "## Test Title", f"Expected '## Test Title', got '{heading_line}'"


def test_anchor_structure_without_title():
    """
    Test anchor placement when no title is provided (token is used as heading text).
    """
    result = merge._heading_block(3, "manifest")
    
    anchor_idx = None
    heading_idx = None
    
    for i, line in enumerate(result):
        if '<a id="manifest"></a>' in line:
            anchor_idx = i
        if line.startswith("### ") and "manifest" in line:
            heading_idx = i
    
    assert anchor_idx is not None
    assert heading_idx is not None
    assert heading_idx == anchor_idx + 1


def test_token_sanitization_for_html_id():
    """
    Test that tokens are sanitized to prevent invalid HTML id attributes.
    
    This is a defense-in-depth measure even though tokens should already
    be sanitized by _slug_token() before reaching _heading_block.
    """
    # Test with various potentially unsafe characters
    unsafe_tokens = [
        ('test"token', 'test-token'),  # Double quote
        ('test<script>', 'test-script-'),  # HTML tags
        ('test token', 'test-token'),  # Space
        ('test&token', 'test-token'),  # Ampersand
        ('test/token', 'test-token'),  # Slash
    ]
    
    for unsafe, expected_pattern in unsafe_tokens:
        result = merge._heading_block(2, unsafe, "Title")
        
        # Find the anchor line
        anchor_line = None
        for line in result:
            if '<a id="' in line:
                anchor_line = line
                break
        
        assert anchor_line is not None, f"Anchor not found for token '{unsafe}'"
        
        # Extract the id value
        match = re.search(r'<a id="([^"]+)"></a>', anchor_line)
        assert match is not None, f"Could not parse anchor from: {anchor_line}"
        
        sanitized_id = match.group(1)
        
        # Verify no unsafe characters remain
        assert '"' not in sanitized_id, f"Double quote not sanitized in: {sanitized_id}"
        assert '<' not in sanitized_id, f"Less-than not sanitized in: {sanitized_id}"
        assert '>' not in sanitized_id, f"Greater-than not sanitized in: {sanitized_id}"
        assert ' ' not in sanitized_id, f"Space not sanitized in: {sanitized_id}"
        assert '&' not in sanitized_id, f"Ampersand not sanitized in: {sanitized_id}"


def test_heading_block_structure():
    """
    Test the overall structure of _heading_block output.
    
    Expected structure:
    1. Anchor line: <a id="token"></a>
    2. Heading line: ## Title
    3. Blank line: ""
    """
    result = merge._heading_block(2, "test-id", "Test Heading")
    
    assert len(result) >= 3, f"Expected at least 3 lines, got {len(result)}"
    
    # Line 0: anchor
    assert result[0] == '<a id="test-id"></a>', f"Expected anchor, got: {result[0]}"
    
    # Line 1: heading
    assert result[1] == "## Test Heading", f"Expected heading, got: {result[1]}"
    
    # Line 2: blank
    assert result[2] == "", f"Expected blank line, got: {result[2]}"


def test_different_heading_levels():
    """
    Test that heading levels are correctly applied.
    """
    for level in [1, 2, 3, 4, 5, 6]:
        result = merge._heading_block(level, "test", "Title")
        
        heading_line = None
        for line in result:
            if "Title" in line and line.startswith("#"):
                heading_line = line
                break
        
        assert heading_line is not None
        expected_prefix = "#" * level + " "
        assert heading_line.startswith(expected_prefix), (
            f"Level {level} should start with '{expected_prefix}', got: {heading_line}"
        )


def test_already_sanitized_tokens_unchanged():
    """
    Test that already-clean tokens pass through unchanged.
    """
    clean_tokens = [
        "manifest",
        "file-repo-path",
        "test_id",
        "item.123",
        "ns:element",
    ]
    
    for token in clean_tokens:
        result = merge._heading_block(2, token, "Title")
        
        # Extract id from anchor
        anchor_line = result[0]
        match = re.search(r'<a id="([^"]+)"></a>', anchor_line)
        assert match is not None
        
        sanitized = match.group(1)
        # Should be unchanged (or minimally changed for valid HTML id chars)
        # The sanitization regex allows: [a-zA-Z0-9._:-]
        # So these should all pass through
        assert all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-' for c in sanitized), (
            f"Token '{token}' was over-sanitized to '{sanitized}'"
        )
