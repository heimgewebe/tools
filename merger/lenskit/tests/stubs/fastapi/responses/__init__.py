class Response:
    def __init__(self, content=b"", status_code=200, media_type="application/json"):
        self.content = content if isinstance(content, (bytes, bytearray)) else str(content).encode()
        self.status_code = status_code
        self.media_type = media_type

    @property
    def text(self):
        try:
            return self.content.decode()
        except Exception:
            return str(self.content)

    def json(self):
        import json
        return json.loads(self.text or "null")

class FileResponse(Response):
    def __init__(self, path, status_code=200):
        import pathlib
        data = pathlib.Path(path).read_bytes()
        super().__init__(data, status_code=status_code, media_type="application/octet-stream")

class HTMLResponse(Response):
    def __init__(self, content="", status_code=200):
        super().__init__(content.encode() if isinstance(content, str) else content, status_code=status_code, media_type="text/html")

class StreamingResponse(Response):
    def __init__(self, content_iterable, status_code=200, media_type="text/plain"):
        import asyncio
        import inspect

        async def _consume_async(gen):
            chunks = []
            async for item in gen:
                chunks.append(item)
            return b"".join(bytes(c, "utf-8") if isinstance(c, str) else c for c in chunks)

        def _run_async(coro):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    new_loop = asyncio.new_event_loop()
                    try:
                        return new_loop.run_until_complete(coro)
                    finally:
                        new_loop.close()
                return loop.run_until_complete(coro)
            except RuntimeError:
                return asyncio.run(coro)

        if inspect.iscoroutine(content_iterable):
            data = _run_async(content_iterable)
            if inspect.isasyncgen(data):
                data = _run_async(_consume_async(data))
        elif inspect.isasyncgen(content_iterable):
            data = _run_async(_consume_async(content_iterable))
        else:
            data = b"".join(bytes(chunk, "utf-8") if isinstance(chunk, str) else chunk for chunk in content_iterable)

        super().__init__(data, status_code=status_code, media_type=media_type)
