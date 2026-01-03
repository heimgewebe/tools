"""FastAPI adapter that satisfies :mod:`http_contract` for the service layer."""

from __future__ import annotations

from fastapi import Body, BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from .http_contract import HTTPBindings


http = HTTPBindings(
    Request=Request,
    HTTPException=HTTPException,
    BackgroundTasks=BackgroundTasks,
    Query=Query,
    Depends=Depends,
    Body=Body,
    StaticFiles=StaticFiles,
    CORSMiddleware=CORSMiddleware,
    StreamingResponse=StreamingResponse,
    FileResponse=FileResponse,
    HTMLResponse=HTMLResponse,
    run_in_threadpool=run_in_threadpool,
)

app = FastAPI(title="rLens", version="1.0.0")

