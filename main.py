from fastapi import FastAPI
from api import auth, users, subscriptions, admin, main_screen
from core.database import Base, engine
from core.config import settings

# Создаем таблицы в БД
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    description="API для Box4Kids - сервис аренды игрушек для детей"
)

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(subscriptions.router)
app.include_router(admin.router)
app.include_router(main_screen.router)

@app.get("/")
async def root():
    return {"message": "Box4Kids API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "box4kids-api"} 