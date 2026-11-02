"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langsmith.utils import LangSmithConflictError
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROMPT_NAME = "bug_to_user_story_v2"
PROMPT_FILE = PROJECT_ROOT / "prompts" / f"{PROMPT_NAME}.yml"

# Variável de entrada usada pelo dataset de avaliação
INPUT_VARIABLE = "bug_report"


def build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    """Monta o ChatPromptTemplate a partir do system prompt e do user prompt."""
    return ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("user", prompt_data["user_prompt"]),
    ])


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    username = os.getenv("USERNAME_LANGSMITH_HUB")
    prompt_identifier = f"{username}/{prompt_name}"
    techniques = prompt_data.get("techniques_applied", [])

    client = Client()
    prompt = build_chat_prompt(prompt_data)

    print(f"Fazendo push do prompt: {prompt_identifier}")

    try:
        url = client.push_prompt(
            prompt_identifier,
            object=prompt,
            is_public=True,
            description=prompt_data["description"],
            readme=f"Técnicas aplicadas: {', '.join(techniques)}",
            tags=prompt_data.get("tags", []),
            commit_description=f"{prompt_data['version']} - técnicas: {', '.join(techniques)}",
        )
    except LangSmithConflictError:
        # O LangSmith recusa um commit idêntico ao último: o prompt já está atualizado
        print("   ✓ Nenhuma alteração desde o último push, o Hub já está atualizado")
        return True
    except Exception as e:
        print(f"❌ Erro ao fazer push do prompt '{prompt_identifier}': {e}")
        return False

    print(f"   ✓ Push concluído (público)")
    print(f"   ✓ Técnicas: {', '.join(techniques)}")
    print(f"   ✓ {url}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    _, errors = validate_prompt_structure(prompt_data)

    user_prompt = prompt_data.get("user_prompt", "").strip()
    if not user_prompt:
        errors.append("user_prompt está vazio")

    if errors:
        return (False, errors)

    variables = set(build_chat_prompt(prompt_data).input_variables)
    if variables != {INPUT_VARIABLE}:
        errors.append(
            f"O template deve ter apenas a variável {{{INPUT_VARIABLE}}}, "
            f"encontradas: {sorted(variables)}"
        )

    if f"{{{INPUT_VARIABLE}}}" not in user_prompt:
        errors.append(f"user_prompt deve conter {{{INPUT_VARIABLE}}}")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(str(PROMPT_FILE))
    if not data or PROMPT_NAME not in data:
        print(f"❌ Prompt '{PROMPT_NAME}' não encontrado em {PROMPT_FILE.relative_to(PROJECT_ROOT)}")
        return 1

    prompt_data = data[PROMPT_NAME]

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    print("✓ Prompt validado\n")

    if not push_prompt_to_langsmith(PROMPT_NAME, prompt_data):
        return 1

    print("\n✅ Push concluído com sucesso!")
    print("\nPróximo passo: python src/evaluate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
