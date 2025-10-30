from sqlalchemy import text
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

def get_by_id(db: Session, uuid: UUID):
    sql = text("""
        SELECT id, nome_apresentacao, nome_completo, inscricao_nacional, ativo
        FROM hub.contratante
        WHERE uuid = :uuid
        """)
    result = db.execute(sql, {"uuid": str(uuid)}).one_or_none()
    return result

def get_id_by_uuid(db: Session, uuid: UUID):
    sql = text("""
        SELECT id 
        FROM hub.contratante 
        WHERE uuid = :uuid
        """)
    result = db.execute(sql, {"uuid": str(uuid)}).scalar_one_or_none()
    return result

def contractor_exists(db: Session, uuid: UUID) -> bool:
    sql = text("""
        SELECT ativo
        FROM hub.contratante
        WHERE uuid = :uuid
        """)
    row = db.execute(sql, {"uuid": str(uuid)}).one_or_none()
    
    # Se não encontrou, retorna False
    if row is None:
        return False
    
    # row é uma tupla, mas como só selecionamos "ativo", o valor está na posição 0
    return bool(row[0])