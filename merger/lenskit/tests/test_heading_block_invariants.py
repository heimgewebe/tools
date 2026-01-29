import unittest
import re
from merger.lenskit.core import merge

class TestHeadingBlockInvariants(unittest.TestCase):
    """
    Tests for _heading_block invariants (Option A: Separate Anchor Line + Markdown Heading).
    Checks robustness of sanitization and anchor placement.
    """

    def test_heading_structure_invariant(self):
        """
        Invariant: Output must strictly follow the sequence:
        1. <a id="..."></a>
        2. ## Title (or Token)
        3. Blank line
        
        Note: Additional lines may appear before these (e.g., search markers),
        so we check the last 3 lines to ensure robustness.
        """
        lines = merge._heading_block(2, "my-token", "My Title")
        # Check the last 3 lines to handle optional search markers
        self.assertRegex(lines[-3], r'^<a id="[^"]+"></a>$')
        self.assertRegex(lines[-2], r'^## My Title$')
        self.assertEqual(lines[-1], "")

    def test_sanitization_invariant_safe_token(self):
        """
        Invariant: Safe tokens (alphanumeric + . _ : -) are preserved as-is.
        """
        token = "safe-token.123_test"
        lines = merge._heading_block(2, token)
        # Anchor should use token exactly
        self.assertIn(f'<a id="{token}"></a>', lines[0])
        # Heading should use token if no title provided
        self.assertIn(f"## {token}", lines[1])

    def test_sanitization_invariant_unsafe_token(self):
        """
        Invariant: Unsafe characters in token are sanitized for the ID.
        We do NOT assert the exact sanitized string (implementation detail),
        but we assert that the resulting ID is safe (contains only allowed chars).
        """
        unsafe_token = "unsafe/token with spaces & symbols!"
        lines = merge._heading_block(2, unsafe_token)

        # Extract the ID used
        match = re.search(r'id="([^"]+)"', lines[0])
        self.assertTrue(match, "Anchor tag with ID not found")
        generated_id = match.group(1)

        # Invariant: ID must be safe for HTML IDs.
        # When sanitized via _slug_token, it produces lowercase alphanumeric + hyphens.
        # When safe tokens pass through, they can include [A-Za-z0-9._:-]
        # Here we're testing an unsafe token, so it goes through _slug_token
        # which produces [a-z0-9-]+ output.
        self.assertRegex(generated_id, r'^[a-z0-9-]+$')

        # Invariant: unsafe chars should be gone
        self.assertNotIn("/", generated_id)
        self.assertNotIn(" ", generated_id)
        self.assertNotIn("&", generated_id)
        self.assertNotIn("!", generated_id)

    def test_title_priority_invariant(self):
        """
        Invariant: If title is provided, it is used in the Markdown heading.
        The token is still used for the anchor.
        """
        token = "token-123"
        title = "Display Title"
        lines = merge._heading_block(2, token, title)

        self.assertIn(f'<a id="{token}"></a>', lines[0])
        self.assertIn(f"## {title}", lines[1])
        self.assertNotIn(f"## {token}", lines[1]) # Token should not be in heading if title exists

    def test_no_inline_html_in_heading(self):
        """
        Invariant: The Markdown heading line MUST NOT contain the anchor tag.
        """
        token = "token"
        title = "Title"
        lines = merge._heading_block(2, token, title)
        heading_line = lines[1]

        self.assertNotIn("<a", heading_line)
        self.assertNotIn("</a>", heading_line)
        self.assertNotIn("id=", heading_line)

if __name__ == '__main__':
    unittest.main()
