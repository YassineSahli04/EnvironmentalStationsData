"""Root test conftest.

Patches PostgreSQL and ClerkAuthentication __init__ at module level so that
importing BackEnd.app.* never attempts real DB / Clerk connections.
These patches MUST be active before any BackEnd.app module is imported.
"""

import sys
from unittest.mock import MagicMock, patch
import pytest

# rq uses multiprocessing 'fork' context which is unavailable on Windows;
# redis also requires a running server.  Both are only used by CfTableCreator
# at runtime, never in tests, so a mock is safe.
for _mod in ("rq", "rq.Queue", "redis", "redis.Redis"):
    sys.modules.setdefault(_mod, MagicMock())

from BackEnd.PostgreSQL.PostgreSQL import PostgreSQL
from BackEnd.app.ClerkAuthentication import ClerkAuthentication

mock_engine = MagicMock()


def _fake_pg_init(self):
    self.engine = mock_engine
    self.SECRETJSONPATH = "fake"
    self.CHUNK_SIZE = 25


def _fake_clerk_init(self, engine):
    self.engine = engine
    self.clerkSecretKey = "fake_key"
    self.logger = MagicMock()


_pg_patcher = patch.object(PostgreSQL, "__init__", _fake_pg_init)
_clerk_patcher = patch.object(ClerkAuthentication, "__init__", _fake_clerk_init)

_pg_patcher.start()
_clerk_patcher.start()


@pytest.fixture()
def engine():
    """Provides the shared mock engine used by all patched singletons."""
    return mock_engine
