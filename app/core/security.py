import os, base64, time
from dotenv import load_dotenv
from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Set
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.cache import cache_get_json, cache_set_json, cache_ping

from app.dataprovider.postgre.session import SessionLocal
from app.dataprovider.postgre.repository.contractor import contractor_exists
from sqlalchemy import text
from app.core.exceptions.types import ForbiddenError

# Carrega variáveis de ambiente do .env
load_dotenv()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

JWT_SECRET_B64 = os.getenv("SECRET_KEY")
if not JWT_SECRET_B64:
    # Ajuste a mensagem para refletir o nome da env var usada
    raise RuntimeError("Defina SECRET_KEY (Base64) igual ao jwt.secret do Spring.")
SECRET_KEY_BYTES = base64.b64decode(JWT_SECRET_B64)

bearer_scheme = HTTPBearer(auto_error=True)

def create_access_token(
    subject: str,
    uid: str,
    integracao: bool = False,
    extra: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    claims: Dict[str, Any] = {
        "sub": subject,
        "uid": uid,
        "integracao": bool(integracao),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra:
        claims.update(extra)
    return jwt.encode(claims, SECRET_KEY_BYTES, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY_BYTES, algorithms=[ALGORITHM], options={"leeway": 30})
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTClaimsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Claims inválidos: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assinatura inválida",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    token = credentials.credentials  # já vem sem o prefixo "Bearer"
    payload = decode_token(token)
    if not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem 'sub'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    uid = payload["uid"]
    sub = payload["sub"]
    iat = payload["iat"]
    exp = payload["exp"]

    # --- CACHE: tenta pegar do Redis pelo (uid, iat)
    cache_key = f"userctx:{uid}:{iat}"
    cached = cache_get_json(cache_key)
    if cached:
        return cached

    # Monta o objeto completo (consulta perfis no DB)
    dados = get_usuario_e_perfis(uid)
    resp = {
        "uid": uid,
        "cid": dados["uuid_contratante"],
        "integracao": payload.get("integracao", False),
        "sub": sub,
        "iat": iat,
        "exp": exp,
        "rules": dados["perfis"],
    }

    # Calcula TTL = exp - now
    now = int(time.time())
    ttl = exp - now
    if ttl > 0:
        cache_set_json(cache_key, resp, ttl)

    return resp

from typing import List, Set
from fastapi import Depends, HTTPException, status

def require_permissions(required: List[str]):
    def _checker(current_user: dict = Depends(get_current_user)):
        user_rules: Set[str] = set(current_user.get("rules", []))
        req_set: Set[str] = set(required)

        # Se não exigir nada, libera
        if not req_set:
            return True

        # Atalho para superadmin
        if "*" in user_rules:
            return True

        # OR: precisa ter pelo menos UMA permissão exigida
        if user_rules & req_set:
            return True

        # Caso contrário, nega
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Acesso negado",
        )

    return _checker


def get_usuario_e_perfis(uid: str) -> Dict[str, Any]:
    """
    Retorna dados do usuário + contratante + lista de permissões.
    Inclui "*" se o usuário for super admin.
    """
    perfis: List[str] = []

    with SessionLocal() as session:
        # Busca uuid_usuario, perfil e flag de super admin
        query_user = text("""
            SELECT 
                u.uuid AS uuid_usuario, 
                c.uuid AS uuid_contratante, 
                u.id_perfil AS id_perfil, 
                (sp.id_acesso IS NOT NULL) AS is_super_admin
            FROM hub.usuario u
            INNER JOIN hub.acesso a
                ON a.id = u.id_acesso
            INNER JOIN hub.contratante c
                ON c.id = u.id_contratante
            LEFT JOIN hub.acesso_super_admin sp
                ON sp.id_acesso = a.id
            WHERE u.ativo = true 
                AND u.convite_aceito = true
                AND a.uuid = :uuid 
                AND a.ativo = true
            ORDER BY u.dt_hr_selecionado DESC
            LIMIT 1
        """)

        row_user = session.execute(query_user, {"uuid": uid}).mappings().fetchone()

        if not row_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado ou não autorizado"
            )

        uuid_usuario = row_user["uuid_usuario"]
        uuid_contratante = row_user["uuid_contratante"]
        is_super_admin = bool(row_user["is_super_admin"])
        id_perfil = row_user["id_perfil"]

        if is_super_admin:
            perfis.append("*")
        else:
            # Busca códigos de funcionalidades do perfil
            query_perfis = text("""
                SELECT 
                    f.codigo 
                FROM hub.perfil_x_funcionalidade pxf
                INNER JOIN hub.perfil p
                    ON p.id = pxf.id_perfil
                INNER JOIN hub.funcionalidade f
                    ON f.id = pxf.id_funcionalidade
                WHERE pxf.id_perfil = :id_perfil
                    AND p.ativo = true
                    AND f.ativo = true
            """)

            codigos: List[str] = session.execute(
                query_perfis, {"id_perfil": id_perfil}
            ).scalars().all()

            perfis.extend(codigos)

    return {
        "uuid_usuario": uuid_usuario,
        "uuid_contratante": uuid_contratante,
        "perfis": perfis
    }

def validate_and_alter_contractor(current_user: dict, contractor_id: UUID | None):
    if contractor_id is None and "*" in current_user.get("rules", []):
        contractor_id = current_user.get("cid")
        return contractor_id
    elif contractor_id is None:
        raise ForbiddenError("Acesso negado")
    return contractor_id
