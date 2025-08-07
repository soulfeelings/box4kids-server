import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api import auth, admin,users, subscriptions, payments, children, interests, skills, toy_categories, subscription_plans, delivery_addresses, toy_boxes
from core.database import Base, engine, get_db
from core.config import settings
from core.data_initialization import initialize_all_data
from core.i18n import translate

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global worker_task
    
    logger = logging.getLogger(__name__)
    
    # Startup
    logger.info("Starting Box4Kids API server...")
    
    # Создаем таблицы в БД
    Base.metadata.create_all(bind=engine)
    
    # Инициализируем данные
    db = next(get_db())
    initialize_all_data(db)
    db.close()
    
    # Инициализация завершена
    logger.info("Application initialization completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Box4Kids API server...")
    logger.info("Shutdown completed")

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    description="API для Box4Kids - сервис аренды игрушек для детей",
    lifespan=lifespan
)


if settings.DEBUG:
    origins = ["*"]  # Разрешаем все источники в режиме разработки
else:
    origins = [
        "http://localhost",
        "http://localhost:3000",  # для локального фронтенда
        "https://your-frontend-domain.com",
        "http://13.51.85.137:3000",
        "http://13.51.85.137",
        "https://13.51.85.137",
        "https://13.51.85.137:3000",
    ]

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(subscriptions.router)
app.include_router(payments.router)
app.include_router(admin.router)

app.include_router(children.router)
app.include_router(interests.router)
app.include_router(skills.router)
app.include_router(toy_categories.router)
app.include_router(subscription_plans.router)
app.include_router(delivery_addresses.router)
app.include_router(toy_boxes.router)

# Delivery dates public
from api.delivery_dates import router as delivery_dates_router
app.include_router(delivery_dates_router)

@app.middleware("http")
async def language_middleware(request: Request, call_next):
    lang = request.headers.get('accept-language', 'ru').split(',')[0][:2]
    request.state.lang = lang if lang in ['ru', 'uz'] else 'ru'
    response = await call_next(request)
    return response

@app.get("/")
async def root(request: Request):
    lang = getattr(request.state, 'lang', 'ru')
    return JSONResponse({
        "message": translate('greeting', lang),
        "version": "1.0.0"
    }) 
    
@app.get("/health")
async def health_check():
    """Health check endpoint для мониторинга"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z", "version": "1.0.0"} 

