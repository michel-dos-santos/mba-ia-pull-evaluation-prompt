"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    """Dados do prompt otimizado (v2)."""
    data = load_prompts(PROMPT_FILE)
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada em {PROMPT_FILE.name}"
    return data[PROMPT_KEY]


@pytest.fixture(scope="module")
def system_prompt(prompt_data):
    return prompt_data.get("system_prompt", "")


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data, system_prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data
        assert isinstance(system_prompt, str)
        assert system_prompt.strip(), "system_prompt está vazio"

    def test_prompt_has_role_definition(self, system_prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        assert re.search(r"\bVocê é (um|uma)\b", system_prompt), \
            "O system_prompt deve definir uma persona começando com 'Você é um/uma'"
        assert "product manager" in system_prompt.lower()

    def test_prompt_mentions_format(self, system_prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        text = system_prompt.lower()
        assert "user story" in text or "markdown" in text
        assert "formato de saída" in text, "O prompt deve ter uma seção de formato de saída"
        # Estrutura padrão de User Story e critérios em Dado/Quando/Então
        assert "Como um" in system_prompt
        assert "eu quero" in system_prompt
        assert "para que" in system_prompt
        assert "Critérios de Aceitação" in system_prompt
        for keyword in ("Dado que", "Quando", "Então"):
            assert keyword in system_prompt

    def test_prompt_has_few_shot_examples(self, system_prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        examples = re.findall(r"^#+ Exemplo \d+", system_prompt, flags=re.MULTILINE)
        assert len(examples) >= 2, f"Mínimo de 2 exemplos, encontrados: {len(examples)}"

        # Cada exemplo precisa ter uma entrada (relato) e uma saída (user story)
        inputs = system_prompt.count("Relato de bug:")
        outputs = system_prompt.count("User Story:")
        assert inputs >= len(examples), "Há exemplos sem o relato de bug de entrada"
        assert outputs >= len(examples), "Há exemplos sem a User Story de saída"

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        for field in ("description", "system_prompt", "user_prompt"):
            text = prompt_data.get(field, "")
            assert "[TODO]" not in text, f"'{field}' ainda contém [TODO]"
            assert "TODO" not in text, f"'{field}' ainda contém TODO"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        assert isinstance(techniques, list)
        assert len(techniques) >= 2, f"Mínimo de 2 técnicas, encontradas: {len(techniques)}"
        # Few-shot é obrigatório no desafio
        assert any("few-shot" in t.lower() for t in techniques)

    def test_prompt_structure_is_valid(self, prompt_data):
        """Valida a estrutura completa com a função auxiliar do projeto."""
        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, errors

    def test_bug_report_only_in_user_prompt(self, prompt_data, system_prompt):
        """A variável {bug_report} deve estar só no user prompt (na v1 estava duplicada)."""
        assert "{bug_report}" in prompt_data.get("user_prompt", "")
        assert "{bug_report}" not in system_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])