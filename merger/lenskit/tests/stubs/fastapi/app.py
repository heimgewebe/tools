import re
from .middleware import Middleware

class FastAPI:
    def __init__(self, **kwargs):
        self.routes = []
        self.user_middleware = []

    def add_middleware(self, middleware_cls, **options):
        self.user_middleware.append(Middleware(middleware_cls))

    def _register(self, method, path, dependencies=None, **kwargs):
        dependencies = dependencies or []
        def decorator(func):
            pattern = re.sub(r"{([^}]+)}", r"(?P<\1>[^/]+)", path)
            regex = re.compile(f"^{pattern}$")
            self.routes.append({
                "method": method,
                "path": path,
                "func": func,
                "dependencies": dependencies,
                "regex": regex,
            })
            return func
        return decorator

    def get(self, path, dependencies=None, **kwargs):
        return self._register("GET", path, dependencies, **kwargs)

    def post(self, path, dependencies=None, **kwargs):
        return self._register("POST", path, dependencies, **kwargs)

    def mount(self, *args, **kwargs):
        # No-op for stub
        return None
