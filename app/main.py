from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import status

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

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Кастомная обработка ошибок валидации"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        
        # Проверяем, что это ошибка парсинга целого числа
        if "int_parsing" in error["type"] and "capacity" in field:
            msg = "Вместимость должна быть целым числом (например: 1, 5, 10). Дробные числа (2.5, 3.7) не допускаются."
        
        errors.append({
            "field": field,
            "message": msg
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": errors,
            "hint": "Пожалуйста, проверьте правильность введённых данных. capacity должен быть целым числом ≥ 1."
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
