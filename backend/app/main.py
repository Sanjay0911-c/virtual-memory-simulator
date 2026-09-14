"""
FastAPI application entry point.

Wires together the two routers (/api/simulate, /api/compare) and three
exception handlers, which are what make EVERY endpoint — including
ones added later — return the same {success, data, error} envelope
shape, whether the request succeeded, failed validation, or hit an
unexpected bug:

  APIError               -> a semantic validation failure we raised
                             on purpose (bad frame count, unknown
                             algorithm, ...). Status from the error itself.
  RequestValidationError -> FastAPI/Pydantic rejected the request
                             shape (missing field, wrong type). 422,
                             code INVALID_INPUT.
  Exception (catch-all)  -> anything we didn't anticipate. 500, code
                             INTERNAL_ERROR. Prevents a raw Python
                             traceback ever reaching the client.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.compare import router as compare_router
from app.api.frame_analysis import router as frame_analysis_router
from app.api.simulate import router as simulate_router
from app.models.envelope import error_response
from app.services.validation import APIError

app = FastAPI(title="Virtual Memory Simulator & Page Replacement Analysis API")

app.include_router(simulate_router)
app.include_router(compare_router)
app.include_router(frame_analysis_router)


@app.exception_handler(APIError)
async def handle_api_error(request: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=error_response(exc.code, exc.message))


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(part) for part in first.get("loc", []) if part != "body")
    detail = first.get("msg", "Invalid request")
    message = f"{field}: {detail}" if field else detail

    return JSONResponse(status_code=422, content=error_response("INVALID_INPUT", message))


@app.exception_handler(Exception)
async def handle_internal_error(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_response("INTERNAL_ERROR", "An unexpected error occurred"),
    )


@app.get("/")
def health_check():
    return {"status": "ok", "service": "vm-simulator-api"}
