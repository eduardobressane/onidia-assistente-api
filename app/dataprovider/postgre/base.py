import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base

# Carrega variáveis de ambiente do .env
load_dotenv()

# Monta a URL do banco de forma segura
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME]):
    raise ValueError("Variáveis de ambiente do banco de dados estão incompletas")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configura engine e sessão
engine = create_engine(DATABASE_URL, echo=False)  # echo desligado, vamos logar via event

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

Base_assistente = declarative_base(metadata=MetaData(schema="assistente"))
Base_hub = declarative_base(metadata=MetaData(schema="hub"))

# Logger do FastAPI/Uvicorn
logger = logging.getLogger("uvicorn")

# Listener para logar queries antes de executar
ENABLE_SQL_LOG = os.getenv("ENABLE_SQL_LOG", "0").lower() in ("1", "true", "yes")

if ENABLE_SQL_LOG:
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        logger.info("➡️ SQL QUERY: %s", statement)
        logger.info("➡️ PARAMS: %s", parameters)

# Função para injeção de dependência no FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
