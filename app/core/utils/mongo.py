from bson import ObjectId
from fastapi import HTTPException

def ensure_object_id(id_str: str) -> ObjectId:
    """Valida e converte string em ObjectId."""
    if not ObjectId.is_valid(id_str):
        raise HTTPException(status_code=400, detail="ID inválido")
    return ObjectId(id_str)