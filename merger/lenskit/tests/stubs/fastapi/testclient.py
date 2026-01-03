import inspect
import json
from .exceptions import HTTPException
from .responses import Response
from .depend import Depends, Query

class _Request:
    def __init__(self, headers=None, query=None, body=None):
        self.headers = headers or {}
        self.query_params = query or {}
        self._body = body

class _Result(Response):
    def __init__(self, *, status_code=200, content=b"", json_data=None, media_type="application/json"):
        if json_data is not None:
            def _convert(obj):
                if hasattr(obj, "model_dump"):
                    return obj.model_dump()
                if isinstance(obj, list):
                    return [_convert(o) for o in obj]
                if isinstance(obj, dict):
                    return {k: _convert(v) for k, v in obj.items()}
                return obj

            content = json.dumps(_convert(json_data)).encode()
        super().__init__(content=content, status_code=status_code, media_type=media_type)

class TestClient:
    def __init__(self, app):
        self.app = app

    def _find_route(self, method, path):
        for r in self.app.routes:
            if r["method"] != method:
                continue
            match = r["regex"].match(path)
            if match:
                return r, match.groupdict()
        return None, None

    def request(self, method, url, json=None, headers=None, params=None):
        path = url.split("?")[0]
        params = params or {}
        route, path_vars = self._find_route(method.upper(), path)
        if not route:
            return _Result(status_code=404, json_data={"detail": "Not Found"})

        query = params.copy()
        if "?" in url:
            from urllib.parse import parse_qs, urlsplit
            q = parse_qs(urlsplit(url).query)
            for k, v in q.items():
                query[k] = v[-1]

        req = _Request(headers=headers or {}, query=query, body=json)

        try:
            # run top-level dependencies
            for dep in route.get("dependencies", []) or []:
                self._resolve_dependency(dep.dependency if hasattr(dep, "dependency") else dep, req)

            result = self._call_handler(route, req, path_vars or {}, json)
            import inspect, asyncio
            if inspect.iscoroutine(result):
                result = asyncio.get_event_loop().run_until_complete(result)
            if isinstance(result, Response):
                return result
            return _Result(json_data=result)
        except HTTPException as exc:
            return _Result(status_code=exc.status_code, json_data={"detail": exc.detail})

    def _resolve_dependency(self, dep, request):
        from .depend import Depends, Query

        if isinstance(dep, Depends):
            dep = dep.dependency

        sig = inspect.signature(dep)
        kwargs = {}
        for name, param in sig.parameters.items():
            default = param.default
            if isinstance(default, Depends):
                kwargs[name] = self._resolve_dependency(default, request)
            elif isinstance(default, Query):
                kwargs[name] = request.query_params.get(name, default.default)
            elif name == "request":
                kwargs[name] = request
            else:
                kwargs[name] = None

        return dep(**kwargs)

    def _call_handler(self, route, request, path_vars, body):
        func = route["func"]
        sig = inspect.signature(func)
        kwargs = {}
        for name, param in sig.parameters.items():
            default = param.default
            if name in path_vars:
                kwargs[name] = path_vars[name]
            elif isinstance(default, Depends):
                kwargs[name] = self._resolve_dependency(default.dependency, request)
            elif isinstance(default, Query):
                kwargs[name] = request.query_params.get(name, default.default)
            elif body is not None and param.annotation is not inspect._empty and isinstance(body, dict):
                try:
                    kwargs[name] = param.annotation(**body)
                    continue
                except Exception:
                    # If the body cannot be coerced into the annotated type, ignore the error
                    # and fall back to the other parameter-handling branches below.
                    pass
            elif name == "request":
                kwargs[name] = request
            elif body is not None and name in ("payload",):
                kwargs[name] = body
            elif body is not None and len(sig.parameters) == 1:
                kwargs[name] = body
            else:
                kwargs[name] = request.query_params.get(name, body.get(name) if isinstance(body, dict) else body if name == "body" else None)
        return func(**kwargs)

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, json=None, **kwargs):
        return self.request("POST", url, json=json, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False
