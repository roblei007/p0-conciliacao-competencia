# Relatório de execução — P0

> Itens marcados **[PREENCHER]** dependem de ações suas (execuções reais, histórico do Git, vídeo,
> sua reflexão). Os resultados de testes simulados abaixo foram obtidos de fato na execução do projeto;
> revise-os e **repita-os na sua máquina** antes de entregar.

## 1. Evolução por nível

**Básico (`p0-basico`)** — script Python que lê um fato operacional no terminal, envia ao LLM por API
REST e mostra a resposta. Chave lida de variável de ambiente (`.env`, fora do Git); dependências em
`requirements.txt`; repositório público no GitHub.

**Intermediário (`p0-intermediario`)** — código separado em módulos com responsabilidade única
(entrada, configuração, solicitação, chamada, resposta, apresentação). Entrada vazia é impedida;
erros previsíveis (configuração/credencial ausente ou inválida, indisponibilidade, falha de rede,
timeout, resposta vazia ou fora do formato) viram mensagens claras com código de saída. Acréscimos:
`.env.example`, `.gitignore`, instruções no README, exemplos e pull request da branch de desenvolvimento.

**Avançado (`p0-avancado`)** — parâmetros do modelo (`LLM_MAX_TOKENS`, `LLM_TEMPERATURE`,
`LLM_TIMEOUT`, `LLM_MODEL`, `LLM_API_FORMAT`, `LLM_API_URL`) alteráveis só pelo ambiente (inclusive trocar o provedor entre os formatos `anthropic` e `openai`); registros de execução sem dados sensíveis;
versões de Python e bibliotecas documentadas; testes da lógica local sem chamada real; validação em
ambiente limpo; relatório e vídeo.

## 2. Decisões principais

| # | Decisão | Alternativa considerada | Justificativa |
|---|---|---|---|
| 1 | Chamar a API por **REST** com `requests` | SDK oficial do provedor | A competência C03 pede integração REST; deixa visíveis cabeçalhos, status HTTP e falhas, e reduz dependências. |
| 2 | Pedir ao LLM **JSON** e validá-lo (data, valor > 0, campos obrigatórios) | Texto livre exibido como veio | Permite detectar respostas fora do formato e apresentar uma tabela padronizada; erros do modelo viram `ErroResposta` em vez de dados ruins. |
| 3 | **Validar a entrada antes** de carregar a configuração e chamar o LLM | Carregar tudo primeiro | Entrada vazia nunca consome chamada paga nem exige chave configurada. |
| 4 | Logs **somente com metadados** | Registrar prompt e resposta para depuração | Fatos contábeis de uma instituição podem ser sensíveis; há teste que garante ausência de chave e de texto de entrada. |
| 5 | Testes com **dublês (`unittest.mock`)** da API, executados com `pytest` | Testar só com chamadas reais | Execução sem chave, internet ou custo; cobre falhas difíceis de provocar de verdade (401, 503, timeout). Chamadas reais ficam em teste opcional à parte. |

## 3. Testes e resultados

### 3.1 Testes automatizados simulados (sem chamada real ao LLM)

Comando: `pytest -v` (equivalente: `python -m unittest discover -s tests -t . -v`)

| Teste | Entrada ou situação | Resultado esperado | Resultado obtido |
|---|---|---|---|
| Entrada válida (simulada) | Fato de energia + resposta JSON simulada | Lançamento formatado com valor `R$ 12.400,00` | OK |
| Entrada vazia | `""`, espaços, `None` | Envio impedido, mensagem orientando o usuário | OK (código 1) |
| Entrada grande demais | 4001 caracteres | Rejeitada com orientação | OK |
| Credencial ausente | `.env` sem `LLM_API_KEY` | Erro claro, sem expor dados | OK (código 2) |
| Configuração inválida | `LLM_MAX_TOKENS=abc`, URL `ftp://`, etc. | Erro específico por variável | OK (código 2) |
| Credencial inválida (simulada) | HTTP 401 e 403 simulados | Término controlado, chave não aparece | OK (código 3) |
| Indisponibilidade (simulada) | HTTP 429, 500, 503, 529 | Mensagem "indisponível, tente novamente" | OK (código 4) |
| Falha de comunicação (simulada) | `ConnectionError` | Mensagem sobre conexão | OK (código 4) |
| Timeout (simulado) | `Timeout` | Mensagem citando os segundos | OK (código 4) |
| Resposta vazia/truncada/inválida | corpo vazio, `max_tokens`, JSON quebrado, data/valor inválidos | `ErroResposta` com orientação | OK (código 5) |
| Erro inesperado | `RuntimeError` contendo a chave | Mensagem genérica sem a chave | OK (código 99) |
| Logs sem segredos | Execução com chave e texto "confidencial" | Log sem chave nem texto | OK |

Resultado da última execução com `unittest` no desenvolvimento: **54 testes, 0 falhas, 2 ignorados** (os 2 testes reais, que exigem `RUN_REAL_TESTS=1`).
**[PREENCHER: rode `pytest -v` na sua máquina e cole o resultado final. O `pytest` não pôde ser executado durante a geração do projeto, então confirme que os mesmos testes passam.]**

### 3.2 Execuções reais pelo terminal

| Teste | Entrada ou situação | Resultado esperado | Resultado obtido |
|---|---|---|---|
| Entrada vazia (real) | Enter sem texto | Mensagem de entrada vazia, sem chamada | Observado no desenvolvimento: código 1 e mensagem orientativa |
| Credencial ausente (real) | Sem `.env` / sem `LLM_API_KEY` | Mensagem pedindo configurar `.env` | Observado no desenvolvimento: código 2 |
| Falha de comunicação (real) | `LLM_API_URL=http://localhost:9` | Mensagem de falha de conexão | Observado no desenvolvimento: código 4 |
| Entrada válida (real) | `exemplos/fato_energia.txt` com chave válida | Lançamento com competência em outubro/2026 | **[PREENCHER]** |
| Entrada válida 2 (real) | `exemplos/fato_seguro.txt` | Despesa do mês + despesa antecipada | **[PREENCHER]** |
| Entrada incompleta (real) | `exemplos/fato_incompleto.txt` | Sem lançamento, com alerta de dados ausentes | **[PREENCHER]** |
| Credencial inválida (real) | `LLM_API_KEY=chave-falsa` | HTTP 401 → término controlado | **[PREENCHER]** |
| Testes reais automatizados | `RUN_REAL_TESTS=1 pytest tests/test_integracao_real.py -v` | 2 testes OK | **[PREENCHER]** |
| Ambiente limpo | Novo venv + seguir só o README | Instalação e execução sem ajuda | **[PREENCHER]** |
| Proteção de segredo | `git log -p \| grep -i "sk-"` e conferir `.env` | Nenhuma ocorrência | **[PREENCHER]** |

## 4. Falhas e limitações

**Falha observada durante o desenvolvimento (HTTP 403 confundido com credencial inválida).**
- *O que aconteceu:* ao executar a aplicação em um ambiente com a rede restrita, o acesso foi bloqueado por um proxy que devolveu HTTP 403. A primeira versão tratava 401 e 403 com a mesma mensagem ("credencial recusada"), o que levaria o usuário a procurar o problema no lugar errado.
- *Como foi identificado:* ao rodar o cenário de falha real pelo terminal e comparar a mensagem com a causa conhecida (bloqueio de rede, não chave errada).
- *Como foi tratado:* 401 e 403 passaram a ter mensagens diferentes; a de 403 cita permissão do modelo e possível bloqueio por proxy/firewall. Foi criado o teste `test_403_menciona_possivel_bloqueio_de_rede`.
- *Por que permanece parcialmente:* a aplicação não consegue distinguir com certeza "sem permissão" de "bloqueio de rede" só pelo status 403; por isso a mensagem lista as duas causas.

**[PREENCHER: acrescente uma dificuldade real que VOCÊ encontrou ao executar (ex.: resposta cortada por `max_tokens`, modelo devolvendo JSON em bloco de código, conta contábil discutível, valor com formato inesperado), explicando: o que aconteceu, como identificou, como tratou e o que permanece.]**

**Limitações que permanecem:** o modelo pode errar a competência ou as contas; nomes de contas
não seguem o plano de contas oficial; um fato por execução; sem novas tentativas automáticas.

## 5. Uso de IA no desenvolvimento

| Item | Registro |
|---|---|
| Ferramenta utilizada | Claude (Anthropic), via claude.ai — **[PREENCHER: modelo/versão exibida]** |
| Tarefa delegada | Proposta de arquitetura em módulos, código Python, testes `unittest`, `README`, modelo deste relatório e roteiro do vídeo, a partir do enunciado do P0 e do problema escolhido. |
| Resultado aproveitado | Estrutura de módulos, prompt de sistema, classificação de erros HTTP, validação do JSON, testes simulados e documentação. |
| Correções ou alterações | Durante a geração, a IA encontrou e corrigiu: isolamento dos testes de log, criação indevida de `logs/` durante os testes e a mensagem única para 401/403. **[PREENCHER: o que VOCÊ alterou, simplificou ou reescreveu após revisar (ex.: nomes de contas, mensagens, prompt, exemplos).]** |
| Forma de verificação | Execução dos testes simulados; execução de cenários de falha pelo terminal; leitura linha a linha dos módulos. **[PREENCHER: confirme o que você de fato verificou e executou, incluindo a chamada real ao LLM.]** |

## 6. Reflexão final

**[PREENCHER com suas palavras, em poucas linhas:]**
- Principal aprendizado (ex.: por que pedir saída estruturada e validá-la; diferença entre os tipos de falha de uma API).
- Competência mais desenvolvida (C01, C02, C03 ou C04) e por quê.
- O que ainda precisa melhorar (ex.: plano de contas real, novas tentativas automáticas, avaliação da qualidade contábil das respostas).

## 7. Vídeo de demonstração

**[PREENCHER: link do vídeo no YouTube (não listado, máximo de 5 min, legendas revisadas).]**
