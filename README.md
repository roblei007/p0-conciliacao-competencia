# P0 — Lançamentos contábeis por competência com apoio de LLM

Projeto P0 (Primeiro fluxo com LLM) — TrendsIA / SOFTEX Campinas / UNIVESP.
Autor: **Roberto Alves Leite** · Vídeo de demonstração: **Link do YouTube ainda não listado**

## 1. Problema

> Um contador que trabalha em um banco público e realiza conciliação contábil precisa transformar
> informações dos sistemas operacionais em registros com lançamentos contábeis pelo princípio da
> competência, porque atualmente enfrenta dificuldade em garantir a qualidade desses fatos
> operacionais nas demonstrações contábeis.

**Usuário:** contador(a) que faz conciliação contábil e recebe fatos operacionais descritos em
texto livre (notas, e-mails, descrições de sistemas), com datas de emissão, vencimento e pagamento
misturadas.

**Entrada:** descrição textual de um fato operacional.
**Saída:** sugestão de lançamentos de partidas dobradas (data de competência, conta a débito, conta a
crédito, valor, histórico e justificativa da competência) e lista de pontos de atenção.

## 2. Por que usar um LLM?

Uma regra fixa não resolve a tarefa: o texto vem em linguagem livre, e decidir **qual é o fato
gerador** exige interpretação (o consumo ocorreu em outubro, mesmo com fatura recebida em outubro e
vencimento em novembro? o prêmio de seguro pago hoje cobre 12 meses?). O LLM interpreta a descrição,
separa valores por período e explica a competência. A saída é **sugestão para revisão do contador**,
nunca contabilização automática.

## 3. Como a solução funciona

```
entrada no terminal → configuração (.env) → API Ollama → resposta no terminal
```

O programa está em `app_basico.py`. Por padrão, usa a API nativa do Ollama no servidor configurado
em `LLM_OLLAMA_HOST_URL`, com o modelo indicado em `LLM_MODEL`. Também mantém suporte a APIs
compatíveis com OpenAI.

## 4. Limites do projeto

Python, execução local, um único LLM, entrada e saída textuais, um fato operacional por execução.
**Fora do escopo:** interface web/gráfica, banco de dados, RAG, agentes, plano de contas oficial
(COSIF), integração com sistemas contábeis, contabilização automática.

## 5. Instalação

Requisitos: **Python 3.10 ou superior** (desenvolvido e testado com Python 3.12.3) e Git.
Bibliotecas: `openai`, `python-dotenv` e `pytest` (para os testes).
Terminal: qualquer um (Windows Terminal/PowerShell, macOS, Linux ou WSL). Os comandos abaixo indicam as variações.

```bash
git clone [URL do seu repositório]
cd [nome da pasta]

# Linux / macOS / WSL  (no Ubuntu/WSL pode ser preciso: sudo apt-get install python3-venv python3-pip)
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

O ambiente está ativo quando o prefixo `(.venv)` aparece no início da linha do terminal.

## 6. Configuração do acesso ao LLM

1. Copie o modelo de configuração:

```bash
cp .env.example .env            # Windows: Copy-Item .env.example .env
```

2. No `.env`, configure o host Ollama e o modelo. O arquivo `.env` está no `.gitignore`:
   **nunca o publique**.

Variáveis de configuração (o Dockerfile fornece padrões para o Ollama):

| Variável | Padrão | Função |
|---|---|---|
| `LLM_OLLAMA_HOST_URL` | `https://llm-internal.softex:9001` no Docker | endereço base do Ollama; o app usa `/api/chat` |
| `LLM_MODEL` | `qwen3.5:9b-q4_K_M` no Docker | modelo Ollama |
| `LLM_MAX_TOKENS` | 1000 | limite máximo de tokens gerados |
| `LLM_TIMEOUT` | 120 | segundos de espera pela resposta |

Para usar outra API compatível com OpenAI, configure `LLM_API_URL` e `LLM_API_KEY`; a variável
legada `GROQ_API_KEY` também é aceita. Como a imagem Docker define o host Ollama por padrão,
adicione `LLM_OLLAMA_HOST_URL=` ao `.env` para desativá-lo nesse modo.

## 7. Execução

```bash
python app_basico.py
```

Digite o fato operacional quando solicitado. O computador ou container precisa ter acesso ao host
configurado em `LLM_OLLAMA_HOST_URL`; essa configuração Ollama não exige chave de API.

**Códigos de saída:** `0` sucesso · `1` entrada vazia ou encerrada · `2` configuração inválida ou
solicitação rejeitada (HTTP 4xx, exceto 401/403) · `3` autenticação/permissão recusada · `4` falha de rede,
limite de requisições ou indisponibilidade (HTTP 5xx) · `5` resposta vazia ou truncada · `99` erro
inesperado do SDK.

## 8. Exemplos de entrada e saída

**Exemplo de entrada**:

```
Em 28/10/2026 o banco recebeu a fatura de energia elétrica da agência central, no valor de
R$ 12.400,00, referente ao consumo de 01/10/2026 a 31/10/2026, com vencimento em 10/11/2026.
```

**Exemplo ilustrativo de saída**:

```
Lançamento 1 | competência 31/10/2026
  D  Despesa com energia elétrica                      R$ 12.400,00
  C  Energia elétrica a pagar                          R$ 12.400,00
  Histórico:   Consumo de energia da agência central - outubro/2026
  Competência: O consumo ocorreu de 01/10 a 31/10/2026; o vencimento em novembro não altera o período de reconhecimento.

Pontos de atenção para o contador:
  - Confirmar se a conta de contrapartida segue o plano de contas (COSIF) adotado pela instituição.

Sugestão gerada por IA: revise contas, valores e datas antes de contabilizar.
```

> **Atenção:** a saída acima é apenas ilustrativa; o programa imprime o texto gerado pelo modelo,
> que pode variar e deve ser revisado por um contador.

**Entrada vazia** (enviar só Enter):

```
Erro: descreva o fato operacional.
```

## 9. Testes automatizados

Os testes em `tests/test_app_basico.py` usam mocks e não fazem chamadas ao serviço LLM. Eles cobrem
configuração, chamada Ollama/OpenAI, respostas vazias/truncadas, classificação de erros e comportamento
do terminal.

```bash
python -m pytest -v
# Alternativa sem pytest:
python -m unittest discover -s tests -v
```

Uma chamada real ao serviço LLM não faz parte da suíte automatizada; teste-a manualmente apenas
quando o host estiver acessível.

## 10. Privacidade e credenciais

O programa envia o fato operacional ao serviço LLM configurado. Não envie dados pessoais ou
sigilosos sem autorização institucional. O `.env` está no `.gitignore`; nunca publique credenciais.
O aplicativo não cria arquivos de log.

## 11. Limitações conhecidas

- O modelo pode errar contas, valores ou o período de competência; **a revisão do contador é obrigatória**.
- Os nomes das contas são descritivos: não seguem o plano de contas oficial (COSIF) da instituição.
- Um fato por execução; não há novas tentativas automáticas em caso de indisponibilidade.
- A resposta pode variar entre execuções. O programa detecta respostas vazias e truncamento pelo
  limite de tokens, mas não valida a correção contábil do conteúdo.
- O acesso ao serviço LLM depende da rede, do host configurado e da disponibilidade do provedor.

## 12. Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `ModuleNotFoundError: No module named 'openai'` ou `'dotenv'` | ambiente virtual não ativado, ou `pip install` feito em outro Python | ative o `.venv` (prefixo `(.venv)`), rode `pip install -r requirements.txt` e confira com `python -c "import sys; print(sys.executable)"` que o Python é o do `.venv` |
| PowerShell: "a execução de scripts foi desabilitada" | política de execução do Windows | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e ative o `.venv` de novo |
| Falha de conexão com o Ollama | host incorreto, sem conectividade ou serviço indisponível | confira `LLM_OLLAMA_HOST_URL`, a rede e o caminho `/api/chat` |
| Modelo não encontrado | nome do modelo inválido ou não disponível no servidor | confira `LLM_MODEL` e se o modelo está disponível no Ollama |
| Acesso negado (401/403) | serviço exige credencial ou acesso não autorizado | confira a política de autenticação do serviço |
| Resposta truncada | `LLM_MAX_TOKENS` insuficiente | aumente `LLM_MAX_TOKENS` no `.env` |
| Solicitação rejeitada (HTTP 400) | modelo ou configuração recusados pelo serviço | confira `LLM_MODEL` e as configurações |
| Limite de requisições ou serviço indisponível | limite ou indisponibilidade temporária | aguarde e tente novamente; confira o serviço LLM |
| `pytest` não encontrado | dependências não instaladas | `pip install -r requirements.txt` com o `.venv` ativo |

**Se uma chave real for parar no Git:** remover o arquivo depois **não** a retira do histórico. Revogue a
chave imediatamente no console do provedor e gere outra.

## 13. Criar e exportar a imagem Docker

Abra o terminal na pasta que contém o `Dockerfile` e mantenha o Docker Desktop iniciado.
No PowerShell, crie a imagem com o ponto final (`.`), que informa ao Docker que a pasta atual
é o contexto do build:

```powershell
docker build -t meu-app:1.0 .
```

Para salvar a imagem como um arquivo TAR na pasta do projeto:

```powershell
docker save -o .\meu-app.tar meu-app:1.0
```

O arquivo `.env` não é incluído na imagem. Para executar o programa no container, crie esse arquivo
com as variáveis de configuração necessárias e rode:

```powershell
docker run --rm -it --env-file .env meu-app:1.0
```

Se o Docker informar que não consegue conectar ao daemon/engine, inicie o Docker Desktop,
aguarde o engine ficar pronto e repita os comandos.
