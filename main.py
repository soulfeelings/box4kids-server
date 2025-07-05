from fastapi import FastAPI
from api import auth, users, subscriptions, admin, main_screen, children, interests, skills, toy_categories
from core.database import Base, engine, get_db
from core.config import settings
from core.data_initialization import initialize_all_data

# Создаем таблицы в БД
Base.metadata.create_all(bind=engine)

# Инициализируем данные
db = next(get_db())
initialize_all_data(db)
db.close()

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
app.include_router(children.router)
app.include_router(interests.router)
app.include_router(skills.router)
app.include_router(toy_categories.router)

@app.get("/")
async def root():
    return {"message": "Box4Kids API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "box4kids-api"} 