from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

from .database import engine, Base
from .routes import rooms_router, bookings_router, equipment_router

# Создаём таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Сириус.Аренда API",
    description="Сервис бронирования пространств",
    version="1.0.0"
)

# CORS (для веб-интерфейса)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(rooms_router)
app.include_router(bookings_router)
app.include_router(equipment_router)

# Статика
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {
        "message": "Добро пожаловать в Сириус.Аренда API!",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)