from fastapi import APIRouter, Depends
from app.core.security import get_current_user, create_access_token

from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/who_am_i")
def who_am_i(current_user: dict = Depends(get_current_user)):
    return {
        "uid": current_user["uid"],
        "cid": current_user["cid"],
        "integracao": current_user["integracao"],
        "sub": current_user["sub"],
        "iat": current_user["iat"],
        "exp": current_user["exp"],
        "rules": current_user["rules"]
    }

@router.get("/token_test")
def token_test():
        token = create_access_token(
            subject="eduardobressane@gmail.com",
            uid="f45f66e4-992d-4734-b53f-3f4f6371f837",
            integracao=False
        )

        now = datetime.now(timezone.utc)
        expire = now + timedelta(60);

        return {
            "access_token": token,
            "token_type": "bearer",
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }
