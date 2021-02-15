from functools import partial, wraps
from typing import Type, Union

from flask import jsonify, request
from flask.wrappers import Response
from marshmallow import Schema
from marshmallow.class_registry import get_class as get_schema

from ...core.schema import PaginationDataSchema
from ...models import Pagination, PaginationData

__all__ = ("serialize_with",)

SCHEMA_LOOKUP_TYPE = Union[Type[Schema], Schema, str]


def serialize_with(f=None, *, schema: SCHEMA_LOOKUP_TYPE, **kwargs):
    if f is None:
        return partial(serialize_with, schema=schema, **kwargs)

    schema = _get_schema(schema=schema, **kwargs)

    @wraps(f)
    def wrapper(*a, **k):
        result = f(*a, **k)

        if isinstance(result, Response):
            return result

        result, code, headers = _unpack_for_serialization(result)
        return jsonify(schema.dump(result).data), code, headers

    return wrapper


def serialize_paginated(f=None, *, schema: SCHEMA_LOOKUP_TYPE, **kwargs):
    if f is None:
        return partial(serialize_paginated, schema=schema, **kwargs)

    items_schema = _get_schema(schema=schema, **kwargs)
    meta_schema = PaginationDataSchema()

    def dump_pagination(paginated: Pagination):
        return {
            "items": items_schema.dump(paginated.items).data,
            "meta": meta_schema.dump(paginated.meta).data,
        }

    @wraps(f)
    def wrapper(*a, **k):
        result = f(*a, **k)

        if isinstance(result, Response):
            return result

        result, code, headers = _unpack_for_serialization(result)
        return jsonify(dump_pagination(result)), code, headers


def read_from_body(
    f=None, *, input_arg_name: str, schema: SCHEMA_LOOKUP_TYPE, **kwargs
):
    """
    Uses the provided schema to read JSON from the request body and passes
    the raw marshmallow output to the wrapped function. The receiver is
    responsible for determining how to handle any errors from parsing.
    """
    if f is None:
        return partial(
            read_from_body, input_arg_name=input_arg_name, schema=schema, **kwargs
        )

    schema = _get_schema(schema=schema, **kwargs)

    @wraps(f)
    def wrapper(*a, **k):
        from_body = schema.load(request.get_json(cache=True))
        k[input_arg_name] = from_body
        return f(*a, **k)

    return wrapper


def _get_schema(*, schema: SCHEMA_LOOKUP_TYPE, **kwargs) -> Schema:
    if isinstance(schema, str):
        schema = get_schema(schema)

    if callable(schema) or issubclass(schema, Schema):
        schema = schema(**kwargs)

    if not isinstance(schema, Schema):
        raise Exception(f"Expected an instance of {Schema!r} but got {schema!r}")

    return schema


def _unpack_for_serialization(resp):
    if not isinstance(resp, tuple):
        return (resp, None, None)
    return (resp + (None, None))[:3]
