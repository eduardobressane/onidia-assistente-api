from fastapi import HTTPException, status

class DomainError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(DomainError):
    def __init__(self, detail: str = "Registro não encontrado"):
        super().__init__(detail, status.HTTP_404_NOT_FOUND)


class BadRequestError(DomainError):
    def __init__(self, detail: str = "Requisição inválida"):
        super().__init__(detail, status.HTTP_400_BAD_REQUEST)


class DuplicateKeyDomainError(DomainError):
    def __init__(self, detail: str = "Já existe um registro com este valor único"):
        super().__init__(detail, status.HTTP_400_BAD_REQUEST)

class ForbiddenError(DomainError):
    def __init__(self, detail: str = "Acesso negado"):
        super().__init__(detail, status.HTTP_403_FORBIDDEN)

class BusinessDomainError(DomainError):
    def __init__(self, detail: str):
        super().__init__(detail, status.HTTP_400_BAD_REQUEST)
