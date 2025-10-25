from bson import ObjectId
from app.core.exceptions.types import BadRequestError

def ensure_object_id(id_str: str) -> ObjectId:
    """Valida e converte string em ObjectId."""
    if not ObjectId.is_valid(id_str):
        raise BadRequestError("ID inválido")
    return ObjectId(id_str) 
    