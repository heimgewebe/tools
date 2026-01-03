# Testing without external dependencies

The test suite can run without installing FastAPI, Pydantic, or Starlette by
using lightweight stubs that live under `merger/lenskit/tests/stubs`. These
modules intentionally stay out of the repository root to avoid shadowing the
real packages in development or production environments.

The stubs are enabled only during pytest collection via
`merger/lenskit/tests/conftest.py`, which prepends its sibling `stubs`
directory (`merger/lenskit/tests/stubs`) to `sys.path` when pytest is running. They are on by default
(`RLENS_TEST_STUBS=1`); set `RLENS_TEST_STUBS=0` to run the tests against real
dependencies when they are installed. Outside of pytest the application will
import the real dependencies, so production semantics (including streaming
responses) remain intact.

**Never** place stub packages such as `fastapi/`, `pydantic/`, or `starlette/`
at the repository root. Doing so can mask the genuine libraries and alter
runtime behavior unexpectedly.
