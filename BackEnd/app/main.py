from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .stations_routes import router as stations_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(stations_router)

if __name__ == "__main__":
    uvicorn.run("BackEnd.app.main:app", host="127.0.0.1", port=8000, reload=True)