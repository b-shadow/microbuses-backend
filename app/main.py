import logging
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.exceptions import AppException
from app.core.settings import get_settings

settings = get_settings()
logger = logging.getLogger('uvicorn.error')


@asynccontextmanager
async def lifespan(_: FastAPI):
    from app.modules.routing_engine.router import service as routing_engine_service

    started = perf_counter()
    try:
        preloaded = routing_engine_service.preload_walking_graph()
    except Exception:
        logger.exception('Walking graph preload failed')
    else:
        elapsed_seconds = perf_counter() - started
        if preloaded:
            logger.info('Walking graph preloaded in %.2fs', elapsed_seconds)
        else:
            logger.warning('Walking graph preload skipped: graph unavailable')
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    openapi_url=f"{settings.api_prefix}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'success': False,
            'message': exc.message,
            'error_code': exc.error_code,
            'details': exc.details or {},
        },
    )


@app.get('/health', tags=['health'])
def healthcheck() -> dict[str, str]:
    return {'status': 'ok'}


app.include_router(api_router, prefix=settings.api_prefix)
