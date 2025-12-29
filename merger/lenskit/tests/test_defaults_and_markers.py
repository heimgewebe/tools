
import unittest
from pathlib import Path
from merger.lenskit.frontends.pythonista import repolens
from merger.lenskit.service.models import JobRequest
from merger.lenskit.core import merge

class TestDefaultsAndMarkers(unittest.TestCase):
    def test_default_extras_minimal(self):
        """
        Verify that DEFAULT_EXTRAS is set to minimal configuration:
        json_sidecar and augment_sidecar only.
        """
        defaults = repolens.DEFAULT_EXTRAS
        self.assertIn("json_sidecar", defaults)
        self.assertIn("augment_sidecar", defaults)
        self.assertNotIn("health", defaults)
        self.assertNotIn("organism_index", defaults)
        self.assertNotIn("fleet_panorama", defaults)
        self.assertNotIn("heatmap", defaults)
        self.assertNotIn("ai_heatmap", defaults)

    def test_service_defaults_match(self):
        """
        Verify that service defaults match frontend defaults.
        """
        req = JobRequest()
        def normalize(s):
            return sorted([x.strip() for x in (s or "").split(',') if x.strip()])

        service_defaults = normalize(req.extras)
        frontend_defaults = normalize(repolens.DEFAULT_EXTRAS)

        self.assertEqual(service_defaults, frontend_defaults,
                         f"Service defaults {service_defaults} do not match frontend {frontend_defaults}")

    def test_start_of_content_marker(self):
        """
        Verify that the generated report contains the <!-- START_OF_CONTENT --> marker
        before the first file content.
        """
        # Setup dummy file info
        fi = merge.FileInfo(
            root_label="test_repo",
            abs_path=Path("/tmp/test/foo.py"),
            rel_path=Path("foo.py"),
            size=100,
            is_text=True,
            md5="abc",
            category="source",
            tags=[],
            ext=".py"
        )
        # Manually compute roles as the scanner would
        fi.roles = []

        # Generate blocks
        iterator = merge.iter_report_blocks(
            files=[fi],
            level="max",
            max_file_bytes=0,
            sources=[Path("/tmp/test")],
            plan_only=False,
            code_only=False,
            debug=False
        )

        report_content = "".join(iterator)

        self.assertIn("<!-- START_OF_CONTENT -->", report_content)

        # Ensure it appears before the first file ID
        marker_pos = report_content.find("<!-- START_OF_CONTENT -->")
        file_id_pos = report_content.find("<!-- file:id=")

        # Note: if plan_only=False, we expect content.
        # But dummy file path /tmp/test/foo.py likely doesn't exist, so read_smart_content returns error msg.
        # The file block is still generated.

        self.assertNotEqual(marker_pos, -1, "Marker not found")
        # In case file block is skipped due to error or other logic, check if we at least have marker.
        # But we want to ensure it is BEFORE content.

        if file_id_pos != -1:
             self.assertLess(marker_pos, file_id_pos, "Marker should appear before file content")

if __name__ == "__main__":
    unittest.main()
