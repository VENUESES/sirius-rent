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

# CORS
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


# ============================================
# УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК ОШИБОК ВАЛИДАЦИИ
# ============================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Кастомная обработка всех ошибок валидации"""
    errors = []
    
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        error_type = error["type"]
        
        # === ОБРАБОТКА ЧИСЛОВЫХ ПОЛЕЙ ===
        
        # 1. Ошибка парсинга числа (дробное вместо целого)
        if "int_parsing" in error_type:
            if "capacity" in field:
                msg = "❌ Вместимость должна быть целым числом. Примеры: 1, 5, 10, 20. Дробные числа (2.5, 3.7) не допускаются."
            elif "room_id" in field:
                msg = "❌ ID комнаты должен быть целым числом. Примеры: 1, 2, 3."
            elif "equipment_id" in field:
                msg = "❌ ID оборудования должен быть целым числом. Примеры: 1, 2, 3."
            elif "count" in field:
                msg = "❌ Количество должно быть целым числом. Примеры: 1, 2, 3."
            elif "skip" in field:
                msg = "❌ Смещение (skip) должно быть целым числом. Примеры: 0, 10, 20."
            elif "limit" in field:
                msg = "❌ Лимит (limit) должен быть целым числом. Примеры: 10, 20, 50."
            else:
                msg = f"❌ Поле '{field}' должно быть целым числом."
        
        # 2. Ошибка "больше или равно" (ge)
        elif "greater_than_equal" in error_type:
            if "capacity" in field:
                msg = "❌ Вместимость должна быть ≥ 1."
            elif "skip" in field:
                msg = "❌ Смещение (skip) должно быть ≥ 0."
            elif "limit" in field:
                msg = "❌ Лимит (limit) должен быть ≥ 1."
            elif "count" in field:
                msg = "❌ Количество должно быть ≥ 1."
            else:
                msg = f"❌ Поле '{field}' должно быть ≥ {error.get('ctx', {}).get('ge', 'указанного значения')}."
        
        # 3. Ошибка "больше" (gt)
        elif "greater_than" in error_type:
            if "room_id" in field or "equipment_id" in field:
                msg = "❌ ID должен быть больше 0."
            else:
                msg = f"❌ Поле '{field}' должно быть > {error.get('ctx', {}).get('gt', 'указанного значения')}."
        
        # 4. Ошибка "меньше или равно" (le)
        elif "less_than_equal" in error_type:
            if "capacity" in field:
                msg = "❌ Вместимость не может быть больше 1000."
            elif "limit" in field:
                msg = "❌ Лимит (limit) не может быть больше 100."
            else:
                msg = f"❌ Поле '{field}' должно быть ≤ {error.get('ctx', {}).get('le', 'указанного значения')}."
        
        # 5. Ошибка "обязательное поле"
        elif "missing" in error_type:
            msg = f"❌ Поле '{field}' обязательно для заполнения."
        
        # 6. Другие ошибки валидации
        else:
            # Преобразуем техническое сообщение в понятное
            if "value is not a valid" in msg:
                msg = f"❌ Неверный формат данных в поле '{field}'."
        
        errors.append({
            "field": field,
            "message": msg,
            "input": error.get("input")
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Ошибка валидации данных",
            "detail": errors,
            "hint": "📝 Проверьте правильность введённых данных. Все числовые поля должны содержать только целые числа."
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)