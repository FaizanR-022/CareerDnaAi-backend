import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class SuccessEnvelopeMiddleware(BaseHTTPMiddleware):
    """Wraps every successful JSON response as {"success": true, "data": ...}.
    Error responses (status >= 400) are left untouched — they're already
    shaped by the exception handlers below, registered separately so this
    middleware never has to re-derive the error envelope itself."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if response.status_code >= 400:
            return response

        # FastAPI's own docs/schema routes (Swagger UI, ReDoc) expect the
        # raw OpenAPI document at the top level — wrapping it in
        # {"success": true, "data": ...} strips the "openapi" version field
        # Swagger UI looks for, breaking /docs entirely.
        app = request.scope.get("app")
        if app is not None and request.url.path in {app.openapi_url, app.docs_url, app.redoc_url}:
            return response

        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            data = json.loads(body)
        except ValueError:
            headers = dict(response.headers)
            return Response(content=body, status_code=response.status_code, headers=headers)

        wrapped = json.dumps({"success": True, "data": data}).encode("utf-8")
        headers = dict(response.headers)
        headers["content-length"] = str(len(wrapped))
        return Response(content=wrapped, status_code=response.status_code, headers=headers)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {"message": exc.detail, "status_code": exc.status_code},
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "message": "Validation error",
                "status_code": 422,
                "details": jsonable_encoder(exc.errors()),
            },
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {"message": "Internal server error", "status_code": 500},
        },
    )


def register_response_envelope(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.add_middleware(SuccessEnvelopeMiddleware)
