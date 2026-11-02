"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _str_representer(dumper, value):
    """Grava textos com várias linhas em bloco literal (|), legível no .yml."""
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


yaml.add_representer(str, _str_representer)

SOURCE_PROMPT = "leonanluppi/bug_to_user_story_v1"
PROMPT_KEY = "bug_to_user_story_v1"
OUTPUT_FILE = PROJECT_ROOT / "prompts" / f"{PROMPT_KEY}.yml"


def extract_messages(prompt) -> dict:
    """
    Extrai o texto do system prompt e do user prompt de um ChatPromptTemplate.

    Args:
        prompt: ChatPromptTemplate retornado pelo LangSmith

    Returns:
        Dicionário com as chaves system_prompt e user_prompt
    """
    messages = {"system_prompt": "", "user_prompt": ""}

    for message in prompt.messages:
        template = message.prompt.template
        message_type = type(message).__name__

        if message_type.startswith("System"):
            messages["system_prompt"] = template
        elif message_type.startswith("Human"):
            messages["user_prompt"] = template

    return messages


def pull_prompts_from_langsmith() -> bool:
    """
    Faz pull do prompt semente do LangSmith Hub e salva localmente em YAML.

    Returns:
        True se sucesso, False caso contrário
    """
    client = Client()

    print(f"Puxando prompt do LangSmith Hub: {SOURCE_PROMPT}")

    try:
        prompt = client.pull_prompt(
            SOURCE_PROMPT,
            dangerously_pull_public_prompt=True,
        )
    except Exception as e:
        print(f"❌ Erro ao fazer pull do prompt '{SOURCE_PROMPT}': {e}")
        return False

    messages = extract_messages(prompt)

    if not messages["system_prompt"]:
        print("❌ O prompt baixado não contém system prompt")
        return False

    data = {
        PROMPT_KEY: {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": messages["system_prompt"],
            "user_prompt": messages["user_prompt"],
            "version": "v1",
            "source": SOURCE_PROMPT,
            "input_variables": list(prompt.input_variables),
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    if not save_yaml(data, str(OUTPUT_FILE)):
        return False

    print(f"   ✓ Variáveis do template: {', '.join(prompt.input_variables)}")
    print(f"   ✓ Prompt salvo em: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")
    return True


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    if not pull_prompts_from_langsmith():
        return 1

    print("\n✅ Pull concluído com sucesso!")
    print("\nPróximo passo: otimize o prompt em prompts/bug_to_user_story_v2.yml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
