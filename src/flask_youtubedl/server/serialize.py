from functools import wraps
from typing import Type, Union

from flask import jsonify
from flask.wrappers import Response
from marshmallow import Schema
from marshmallow.class_registry import get_class as get_schema

SCHEMA_LOOKUP_TYPE = Union[Type[Schema], Schema, str]


def serialize_with(f=None, *, schema: SCHEMA_LOOKUP_TYPE, **kwargs):
    if f is None:
        return lambda f: serialize_with(f, schema=schema, **kwargs)

    if isinstance(schema, str):
        schema = get_schema(schema)

    if not isinstance(schema, Schema):
        schema = schema(**kwargs)

    @wraps(f)
    def wrapper(*a, **k):
        result = f(*a, **k)

        if isinstance(result, Response):
            return result

        result, code, headers = _unpack_for_serialization(result)
        return jsonify(schema.dump(result).data), code, headers

    return wrapper


def _unpack_for_serialization(resp):
    if not isinstance(resp, tuple):
        return (resp, None, None)
    return (resp + (None, None))[:3]
