
import requests
from typing import Dict, List, Optional


class StructureFetcher:
    """
    Classe responsável por buscar estruturas de MCP e LangServe a partir de URLs.
    """

    @staticmethod
    def get_mcp_structure(url: str, headers: Optional[List[Dict[str, str]]] = None) -> Dict:
        """
        Obtém a estrutura de um MCP a partir da URL fornecida.
        
        :param url: URL base do serviço MCP
        :param headers: Lista de headers no formato [{"name": "...", "value": "..."}]
        :return: Estrutura MCP como dict
        """
        headers_dict = {h["name"]: h["value"] for h in (headers or [])}
        response = requests.get(url, headers=headers_dict, timeout=10)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_langserve_structure(url: str, headers: Optional[List[Dict[str, str]]] = None) -> Dict:
        """
        Obtém a estrutura de um LangServe a partir da URL fornecida.
        
        :param url: URL base do serviço LangServe
        :param headers: Lista de headers no formato [{"name": "...", "value": "..."}]
        :return: Estrutura LangServe como dict
        """
        headers_dict = {h["name"]: h["value"] for h in (headers or [])}
        response = requests.get(url, headers=headers_dict, timeout=10)
        response.raise_for_status()
        return response.json()
