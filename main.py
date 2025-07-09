import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import auth, users, subscriptions, payments, admin, main_screen, children, interests, skills, toy_categories, subscription_plans, delivery_addresses, toy_boxes
from core.database import Base, engine, get_db
from core.config import settings
from core.data_initialization import initialize_all_data
from workers.toybox_worker import ToyBoxWorker

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Глобальная переменная для воркера
worker_task = None

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
    
    # Запускаем ToyBox воркер в background
    try:
        worker = ToyBoxWorker()
        worker_task = asyncio.create_task(worker.start_async())
        logger.info("ToyBox worker started successfully")
    except Exception as e:
        logger.error(f"Failed to start ToyBox worker: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Box4Kids API server...")
    
    # Останавливаем воркер
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            logger.info("ToyBox worker stopped")

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    description="API для Box4Kids - сервис аренды игрушек для детей",
    lifespan=lifespan
)


origins = [
    "http://localhost",
    "http://localhost:3000",  # для React/Vite
    "https://your-frontend-domain.com",
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
app.include_router(main_screen.router)
app.include_router(children.router)
app.include_router(interests.router)
app.include_router(skills.router)
app.include_router(toy_categories.router)
app.include_router(subscription_plans.router)
app.include_router(delivery_addresses.router)
app.include_router(toy_boxes.router)

@app.get("/")
async def root():
    return {"message": "Box4Kids API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "box4kids-api"} 