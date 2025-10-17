
import pytest
from structure_fetcher import StructureFetcher
from ocp_converter import mcp_to_ocp


def test_mcp_to_ocp_conversion():
    # URL de exemplo de MCP (ajuste se necessário)
    mcp_url = "http://localhost:4000/tools"

    # Buscar estrutura do MCP
    mcp_struct = StructureFetcher.get_mcp_structure(mcp_url)

    # Converter para OCP
    ocp_obj = mcp_to_ocp(mcp_struct, url=mcp_url)

    # Validar campos principais
    assert "metadata" in ocp_obj
    assert ocp_obj["metadata"]["protocol"] == "OCP"
    assert ocp_obj["metadata"]["version"] == "1.0.0"
    assert "tools" in ocp_obj["structure"]
    assert isinstance(ocp_obj["structure"]["tools"], list)

    print("Conversão MCP->OCP bem-sucedida:", ocp_obj)


if __name__ == "__main__":
    pytest.main([__file__])