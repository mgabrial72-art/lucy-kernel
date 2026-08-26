"""Middleware global de tratamento de erros."""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
import traceback


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Tratador global de exceções não capturadas."""
    logger.error(
        f"❌ Erro em {request.method} {request.url}\n"
        f"   {type(exc).__name__}: {exc}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Erro interno do servidor",
            "type": type(exc).__name__
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Tratador de erros de validação Pydantic."""
    logger.warning(f"⚠️ Validação falhou: {request.url}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Dados inválidos",
            "details": exc.errors()
        }
    )
