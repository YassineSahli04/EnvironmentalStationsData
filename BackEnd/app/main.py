from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from BackEnd.app.stations_routes import router as stations_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(stations_router)