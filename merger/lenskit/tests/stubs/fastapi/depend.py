class Depends:
    def __init__(self, dependency):
        self.dependency = dependency

class Query:
    def __init__(self, default=None):
        self.default = default

class Body:
    def __init__(self, default=None, default_factory=None):
        self.default = default
        self.default_factory = default_factory
