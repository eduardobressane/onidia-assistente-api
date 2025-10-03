from fastapi import FastAPI
from app.controllers import modelo_ai as modelo_ai_ctrl
from app.controllers import tool as tool_ctrl

app = FastAPI(title="Assistente Onidia API")

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(modelo_ai_ctrl.router)
app.include_router(tool_ctrl.router)