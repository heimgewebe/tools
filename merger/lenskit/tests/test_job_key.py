import unittest
from merger.lenskit.service.models import JobRequest, Job
from merger.lenskit.service.app import compute_job_key
from merger.lenskit.core.merge import SPEC_VERSION

class TestServiceReuse(unittest.TestCase):
    def test_compute_job_key_determinism(self):
        """Same request should produce same job_key."""
        req1 = JobRequest(
            repos=["repo1", "repo2"],
            extras="json_sidecar,augment_sidecar",
            path_filter=None,
            extensions=["py", "js"]
        )
        req2 = JobRequest(
            repos=["repo1", "repo2"],
            extras="json_sidecar,augment_sidecar",
            path_filter=None,
            extensions=["py", "js"]
        )
        key1 = compute_job_key(req1, "/path/to/hub", "v1")
        key2 = compute_job_key(req2, "/path/to/hub", "v1")
        self.assertEqual(key1, key2)

    def test_compute_job_key_permutations(self):
        """Permuted lists should produce same job_key (sorted canonicalization)."""
        # Permuted repos
        req1 = JobRequest(repos=["repo1", "repo2"])
        req2 = JobRequest(repos=["repo2", "repo1"])
        key1 = compute_job_key(req1, "/hub", "v1")
        key2 = compute_job_key(req2, "/hub", "v1")
        self.assertEqual(key1, key2)

        # Permuted extras (comma string)
        req3 = JobRequest(extras="a,b,c")
        req4 = JobRequest(extras=" c, b , a ")
        key3 = compute_job_key(req3, "/hub", "v1")
        key4 = compute_job_key(req4, "/hub", "v1")
        self.assertEqual(key3, key4)

        # Permuted extensions
        req5 = JobRequest(extensions=["py", "md"])
        req6 = JobRequest(extensions=["md", "py"])
        key5 = compute_job_key(req5, "/hub", "v1")
        key6 = compute_job_key(req6, "/hub", "v1")
        self.assertEqual(key5, key6)

    def test_compute_job_key_variance(self):
        """Different inputs should produce different keys."""
        req1 = JobRequest(repos=["repo1"])
        req2 = JobRequest(repos=["repo2"])
        self.assertNotEqual(
            compute_job_key(req1, "/hub", "v1"),
            compute_job_key(req2, "/hub", "v1")
        )

        # Hub path matters
        self.assertNotEqual(
            compute_job_key(req1, "/hub1", "v1"),
            compute_job_key(req1, "/hub2", "v1")
        )

        # Version matters
        self.assertNotEqual(
            compute_job_key(req1, "/hub", "v1"),
            compute_job_key(req1, "/hub", "v2")
        )

    def test_create_job_populates_job_key(self):
        """Job.create should now accept and store job_key."""
        req = JobRequest(repos=["repo1"])
        key = "test_key_123"
        job = Job.create(request=req, job_key=key, content_hash=key)
        self.assertEqual(job.job_key, key)
        self.assertEqual(job.content_hash, key)

if __name__ == '__main__':
    unittest.main()
