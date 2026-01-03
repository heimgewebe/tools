"""Test stub for Pydantic's BaseModel (no validation/coercion)."""


class BaseModel:
    def __init__(self, **data):
        for k, v in data.items():
            setattr(self, k, v)

    def dict(self):
        return self.model_dump()

    def model_dump(self):
        def _convert(val):
            if isinstance(val, BaseModel):
                return val.model_dump()
            if isinstance(val, list):
                return [_convert(v) for v in val]
            if isinstance(val, dict):
                return {k: _convert(v) for k, v in val.items()}
            return val

        return {k: _convert(v) for k, v in self.__dict__.items()}

    def json(self):
        import json
        return json.dumps(self.dict())

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, cls):
            return obj
        return cls(**obj)
