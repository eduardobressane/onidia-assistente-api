import requests
from typing import Dict, Optional, Literal, Any
from app.core.exceptions.types import BadRequestError


class StructureFetcher:
    """
    Classe responsável por buscar estruturas como MCP e LangServe a partir de URLs.
    """

    @staticmethod
    def get_structure(
        structure_type: Literal["mcp", "ocp-m", "langserve"],
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict:
        """
        Busca a estrutura JSON de um servidor MCP ou LangServe.
        Adiciona automaticamente '/tools' à URL se o tipo for MCP.
        """

        # Normaliza headers no formato esperado pelo requests
        merged_headers: Dict[str, str] = {}

        if headers:
            if not isinstance(headers, dict):
                raise BadRequestError(
                    f"O campo 'headers' deve ser um objeto (dict) com chave e valor. Recebido: {type(headers)}"
                )
            merged_headers.update(headers)

        try:
            if structure_type == "mcp":
                return StructureFetcher._get_mcp_structure(url, merged_headers)
            elif structure_type == "ocp-m":
                return StructureFetcher._get_ocpm_structure(url, merged_headers)
            elif structure_type == "langserve":
                return StructureFetcher._get_langserve_structure(url, merged_headers)
            else:
                raise BadRequestError(f"Tipo de estrutura inválido: {structure_type}")

        except requests.exceptions.Timeout:
            raise BadRequestError(f"Timeout ao tentar acessar {url}")

        except requests.exceptions.ConnectionError:
            raise BadRequestError(f"Não foi possível conectar a {url}")

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else "?"
            reason = e.response.reason if e.response else ""
            raise BadRequestError(f"Erro HTTP ao acessar {url}: {status} {reason}")

        except requests.exceptions.RequestException as e:
            raise BadRequestError(f"Erro ao buscar estrutura em {url}: {e}")

        except Exception as e:
            raise BadRequestError(f"Erro inesperado ao buscar estrutura: {e}")

    # --- Métodos privados ---

    @staticmethod
    def _get_mcp_structure(url: str, headers: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Obtém a estrutura JSON padrão de um servidor MCP.
        Se a URL não terminar com '/tools', adiciona automaticamente.
        """
        url = url.rstrip("/")
        if not url.endswith("/tools"):
            url = f"{url}/tools"

        response = requests.get(url, headers=headers or {}, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, (dict, list)):
            raise BadRequestError("A resposta do MCP não está em formato JSON esperado.")

        return data

    @staticmethod
    def _get_ocpm_structure(url: str, headers: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Obtém apenas o conteúdo do campo 'data' de um servidor dinâmico OCP-M.
        Se a URL não terminar com '/tools', adiciona automaticamente.
        """
        url = url.rstrip("/")
        if not url.endswith("/tools"):
            url = f"{url}/tools"

        response = requests.get(url, headers=headers or {}, timeout=10)
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise BadRequestError("A resposta do MCP não está em formato JSON esperado.")

        # 🔹 Extrai apenas o campo 'data'
        if "data" not in data:
            raise BadRequestError("A resposta do MCP não contém o campo 'data'.")

        return data["data"]

    @staticmethod
    def _get_langserve_structure(url: str, headers: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Obtém a estrutura JSON padrão de um servidor LangServe.
        O endpoint raiz '/' já retorna o schema do agente.
        """
        url = url.rstrip("/")

        response = requests.get(url, headers=headers or {}, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict):
            raise BadRequestError("A resposta do LangServe não está em formato JSON esperado.")

        return data
