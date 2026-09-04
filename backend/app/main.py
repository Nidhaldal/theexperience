from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.albums import router as albums_router
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(albums_router)
@app.get("/health")
def health_check():
    return {"status": "ok"}