"""Test stub for FastAPI APIs (minimal surface used by service tests)."""

from .exceptions import HTTPException
from .depend import Depends, Query, Body
from .app import FastAPI
from .background import BackgroundTasks
from .requests import Request
