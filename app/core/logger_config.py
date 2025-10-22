import os
from dotenv import load_dotenv
from datetime import datetime

# --- Carregar variáveis ---
load_dotenv()
DEBUG = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")

def info(msg: str):
    """Imprime mensagem de info se DEBUG estiver ativo."""
    if DEBUG:
        print(f"[INFO {datetime.now().isoformat()}] {msg}")

def debug(msg: str):
    """Imprime mensagem de debug se DEBUG estiver ativo."""
    if DEBUG:
        print(f"[DEBUG {datetime.now().isoformat()}] {msg}")

def error(msg: str):
    """Imprime mensagem de error se DEBUG estiver ativo."""
    if DEBUG:
        print(f"[ERROR {datetime.now().isoformat()}] {msg}")