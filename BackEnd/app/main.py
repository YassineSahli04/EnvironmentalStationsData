from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from BackEnd.app.stations_routes import router as stations_router
from BackEnd.app.user_routes import router as users_router
import logging
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://environmentalstationsdata.pages.dev"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(stations_router)
app.include_router(users_router)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

DEBUG = False

logger = logging.getLogger("app")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc, exc_info=DEBUG)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
