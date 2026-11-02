# Histórico de iterações do prompt v2

Modelos: `gpt-4.1-mini` para gerar as respostas (`LLM_MODEL`) e para avaliar (`EVAL_MODEL`), ambos com `temperature=0`.
Dataset: `mba-ia-pull-evaluation-prompt-eval` (15 exemplos: 5 simples, 7 médios, 3 complexos).

| Iteração | Helpfulness | Correctness | F1-Score | Clarity | Precision | Média | Status |
|---|---|---|---|---|---|---|---|
| 1 | 0.87 | 0.90 | 0.87 | 0.82 | 0.93 | 0.8777 | Aprovado (margem pequena em Clarity) |
| 2 | 0.87 | 0.91 | 0.88 | 0.81 | 0.93 | 0.8813 | Aprovado (sem ganho real) |
| 3 | 0.90 | 0.94 | 0.93 | 0.86 | 0.94 | 0.9128 | Aprovado |
| 4 | 0.88 | 0.92 | 0.91 | 0.84 | 0.93 | 0.8943 | Aprovado (regressão leve em relação à 3) |
| **5 (final)** | **0.91** | **0.94** | **0.91** | **0.86** | **0.96** | **0.9152** | **Aprovado — versão final** |

## Experimentos no LangSmith × iterações

O dataset mostra 7 experimentos. Os dois primeiros são tentativas interrompidas com `gpt-5-nano`, feitas
com o mesmo prompt da iteração 1, antes de fixar os modelos; as iterações 1 a 5 correspondem aos
experimentos #3 a #7.

| # no LangSmith | Experimento | Geração | Avaliação | Exemplos avaliados | Situação |
|---|---|---|---|---|---|
| #1 | `...-de6b34f6` | `gpt-5-nano` | `gpt-5-nano` | 3 de 15 | Interrompido |
| #2 | `...-ba2b5a88` | `gpt-5-nano` | `gpt-4.1-mini` | 4 de 15 | Interrompido |
| #3 | `...-34a0cd20` | `gpt-4.1-mini` | `gpt-4.1-mini` | 15 de 15 | Iteração 1 |
| #4 | `...-9178688b` | `gpt-4.1-mini` | `gpt-4.1-mini` | 15 de 15 | Iteração 2 |
| #5 | `...-345b5d67` | `gpt-4.1-mini` | `gpt-4.1-mini` | 15 de 15 | Iteração 3 |
| #6 | `...-622437b0` | `gpt-4.1-mini` | `gpt-4.1-mini` | 15 de 15 | Iteração 4 |
| #7 | `...-039e8fd7` | `gpt-4.1-mini` | `gpt-4.1-mini` | 15 de 15 | Iteração 5 (final) |

Por que #1 e #2 foram interrompidos: o `gpt-5-nano` é um modelo de raciocínio, e o `evaluate.py` roda os
exemplos em sequência. No #1, gerar as 15 respostas e avaliar só 3 delas levou cerca de 8 minutos
(cada exemplo precisa de 1 geração e 3 chamadas de avaliação). O #2 trocou só o avaliador para
`gpt-4.1-mini` e continuou lento por causa da geração. A partir do #3 os dois modelos passaram a ser
`gpt-4.1-mini`, e cada rodada completa caiu para cerca de 1 minuto.

As médias que o painel mostra para #1 e #2 cobrem apenas os exemplos avaliados antes da interrupção
(3 e 4, respectivamente), por isso não são comparáveis com as iterações.

## Iteração 1 — prompt inicial

Prompt com persona (Product Manager sênior), análise passo a passo interna, formato por complexidade
(simples / médio / complexo), regras anti-alucinação, casos especiais e 3 exemplos few-shot.

Experimento: `selectedSessions=9154789b-7913-4223-be5c-39d4eb8ee7d8`

Problemas apontados pelo avaliador:
- Relatos médios tratados como simples: faltaram as seções que a referência espera
  (acessibilidade no modal, exemplo de cálculo no desconto, critérios técnicos nas notificações,
  critérios de prevenção no estoque). F1 de 0.69 nesses casos.
- Meta de performance usando o próprio valor do bug ("gerar em até 120 segundos").
- Critérios genéricos ("não deve ocorrer erro") e fora do escopo (voltar ao modo retrato), que derrubam Clarity.
- Persona "Como um sistema de processamento de pedidos" vista como personificação confusa.

## Iteração 2 — regras e tabela de gatilhos

Mudanças:
- Na dúvida entre simples e médio, classificar como médio.
- Tabela de gatilhos para seções extras (valores → Exemplo de Cálculo; interface → Acessibilidade;
  performance → Critérios Técnicos; estoque/concorrência → Prevenção; segurança → HTTP correto + auditoria).
- Metas numéricas bem melhores que a situação atual; nunca o valor do bug.
- Proibição de critérios genéricos, repetidos ou fora do escopo; explicitar subconjuntos ("status ativo").
- Persona sistêmica padronizada como "Como o sistema de <domínio>".
- Novo exemplo few-shot de relato médio de performance.

Experimento: `selectedSessions=c323a5ab-efc5-493a-8d05-fef70a0d98a2`

Resultado: o modelo seguiu as regras de meta e de escopo, mas ignorou a tabela de gatilhos — modal,
estoque e desconto continuaram sem seções extras. Conclusão: o modelo imita o formato dos exemplos
few-shot mais do que segue instruções descritivas.

## Iteração 3 — padrões nos exemplos e checklist final

Mudanças:
- Exemplo 2 trocado por um bug de interface que demonstra "Critérios de Acessibilidade".
- Exemplo 3 passou a demonstrar "Critérios de Prevenção" além de "Critérios Técnicos".
- Checklist no fim do system prompt (última coisa lida pelo modelo) repetindo os gatilhos.

Experimento: `selectedSessions=0f7a533b-3579-4ec0-9a8c-97b79fa91e1d`

Resultado: F1 do modal subiu de 0.69 para 0.92, do estoque de 0.69 para 0.87 e do desconto de 0.90 para 1.00.
Clarity média subiu de 0.81 para 0.86. As notas mais baixas restantes (Clarity 0.70 no webhook e no
botão do carrinho) vêm do avaliador estranhar o formato de User Story em si, não de falhas do conteúdo.

## Iteração 4 — precisão nos relatos simples

Problemas restantes na iteração 3: relatos simples recebiam "Contexto Técnico" sem necessidade (Safari,
dashboard), critérios fora do escopo ("qualquer filtro aplicado", "versões suportadas"), ID do produto
na frase da user story, critério de estoque atuando na adição ao carrinho em vez da finalização e
ausência de "Critérios Adicionais" para administradores no caso de segurança.

Mudanças:
- Definição mais rígida de relato SIMPLES: números dentro de uma frase curta não tornam o relato MÉDIO.
- Relatos simples com exatamente 5 critérios e sem seção técnica.
- Frase da user story descreve a capacidade de forma geral; IDs e valores ficam nos critérios.
- Primeiro bloco de critérios deve reproduzir o ponto exato em que o bug acontece.
- Checklist: "Critérios Adicionais para <perfil>" quando há perfis com permissões diferentes;
  proibição explícita de filtros, versões e "tempo real" não citados no relato.

Experimento: `selectedSessions=998189b2-e36c-42e4-b2bf-889f1200ad46`

Resultado: aprovado, mas com média menor que a iteração 3 (0.894 contra 0.913).
- Melhorou: a frase da user story ficou geral ("eu quero adicionar produtos ao carrinho"), segurança
  passou de Precision 0.90 para 1.00 e o dashboard chegou a F1 1.00.
- Piorou: a regra "exatamente 5 critérios" vazou para relatos médios e o webhook perdeu o critério
  "responder HTTP 200 ao gateway" (Precision 0.90 → 0.70). A regra do ponto exato do bug foi ignorada
  no caso do estoque (F1 0.87 → 0.77), e o Safari continuou recebendo "Contexto Técnico".
- Lição: regras de quantidade fixa ("exatamente N") têm efeito colateral fora do caso a que se destinam,
  e parte da variação entre rodadas (em geral uns 0.05 por exemplo, às vezes até 0.15) é ruído do avaliador.

## Iteração 5 — correção da regressão (versão final)

Mudanças (apenas o necessário para desfazer o efeito colateral da iteração 4):
- Removida a regra "exatamente 5 critérios". Relatos simples continuam sem seção técnica, mas sem contagem fixa.
- Checklist: relatos de integração (webhook, API, gateway) devem trazer o código HTTP de sucesso,
  a atualização de status e a consequência para o cliente (ex.: email de confirmação).
- Mantidas as melhorias da iteração 4 (frase da user story genérica, critérios para administradores,
  controle de escopo).

Experimento: `selectedSessions=4805830b-34b4-4f75-abf2-9e7320cae686`

Resultado: melhor média de todas as rodadas (0.9152) e maior Precision (0.96).
- Webhook recuperado: F1 0.87 → 1.00, Precision 0.70 → 0.90.
- Estoque: F1 0.77 → 0.87. Endpoint de segurança: F1 0.87 → 1.00.
- Limitação conhecida: o relato do Safari (duas frases curtas) ainda recebe "Contexto Técnico" com o
  `gpt-4.1-mini`, apesar da regra explícita. Não derrubou as notas (Clarity 0.85, Precision 0.90).
- As quedas pontuais em modal, iOS e email (F1 −0.11 a −0.15) não têm relação com as mudanças desta
  rodada e são compatíveis com a variação do avaliador observada entre rodadas.
