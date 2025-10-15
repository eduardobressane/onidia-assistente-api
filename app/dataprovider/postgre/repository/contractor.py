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

def contractors_exists(db: Session, uuids: List[UUID]) -> bool:
    if not uuids:
        return True  # lista vazia não deve falhar

    sql = text("""
        SELECT uuid
        FROM hub.contratante
        WHERE uuid = ANY(:uuids)
          AND ativo = true
    """)

    rows = db.execute(sql, {"uuids": [str(u) for u in uuids]}).fetchall()
    encontrados = {str(r[0]) for r in rows}

    enviados = {str(u) for u in uuids}
    faltantes = enviados - encontrados

    if faltantes:
        raise NotFoundError(f"Contratante(s) não encontrado(s): {', '.join(faltantes)}")

    return True