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
entrada no terminal → configuração (.env) → Ollama interno (API REST) → resposta no terminal
```

O programa está em `app_basico.py`. Ele usa a API de chat nativa do Ollama, configurada para
`https://llm-internal.softex:9001/api/chat`, com o modelo `qwen3.5:9b-q4_K_M`.

## 4. Limites do projeto

Python, execução local, um único LLM, entrada e saída textuais, um fato operacional por execução.
**Fora do escopo:** interface web/gráfica, banco de dados, RAG, agentes, plano de contas oficial
(COSIF), integração com sistemas contábeis, contabilização automática.

## 5. Instalação

Requisitos: **Python 3.10 ou superior** (desenvolvido e testado com Python 3.12.3) e Git.
Bibliotecas: `requests` (testado com 2.33.1), `python-dotenv` (testado com 1.2.2) e `pytest` (para os testes).
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

2. O `.env.example` já aponta para o Ollama interno e para o modelo solicitado. A API interna não
   exige chave por padrão; se a equipe que administra o servidor fornecer uma, configure `LLM_API_KEY`
   no `.env`. O arquivo `.env` está no `.gitignore`: **nunca o publique**.

Parâmetros opcionais (alteráveis sem mexer no código):

| Variável | Padrão | Função |
|---|---|---|
| `LLM_API_URL` | `https://llm-internal.softex:9001/api/chat` | endpoint de chat do Ollama |
| `LLM_MODEL` | `qwen3.5:9b-q4_K_M` | modelo disponibilizado no servidor |
| `LLM_API_KEY` | vazio | opcional; só use se o servidor exigir |
| `LLM_MAX_TOKENS` | 1000 | limite máximo de tokens gerados |
| `LLM_TIMEOUT` | 120 | segundos de espera pela resposta |

## 7. Execução

```bash
python app_basico.py
```

Digite o fato operacional quando solicitado. O computador precisa estar conectado à rede que
resolve e permite acesso a `llm-internal.softex`; em Docker, essa conectividade e a confiança no
certificado HTTPS também precisam estar disponíveis dentro do container.

**Códigos de saída:** `0` sucesso · `1` entrada inválida · `2` configuração/credencial ausente ou
inválida · `3` credencial recusada pelo serviço · `4` serviço indisponível, falha de rede ou timeout ·
`5` resposta vazia/truncada/em formato inesperado · `99` erro inesperado.

## 8. Exemplos de entrada e saída

**Entrada** (`exemplos/fato_energia.txt`):

```
Em 28/10/2026 o banco recebeu a fatura de energia elétrica da agência central, no valor de
R$ 12.400,00, referente ao consumo de 01/10/2026 a 31/10/2026, com vencimento em 10/11/2026.
```

**Saída** (`exemplos/saida_energia.txt`):

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

> **Atenção:** `saida_energia.txt` é uma saída **ilustrativa**, gerada a partir de uma resposta
> simulada para mostrar o formato. [substitua pela saída da sua execução real e indique a
> data e o modelo usado.] A resposta de um LLM pode variar entre execuções.

Outros exemplos prontos: `exemplos/fato_seguro.txt` (pagamento antecipado que abrange vários
períodos) e `exemplos/fato_incompleto.txt` (falta de dados: o esperado é nenhum lançamento e um
alerta pedindo as informações ausentes).

**Entrada vazia** (enviar só Enter):

```
Erro: Entrada vazia. Descreva o fato operacional (o que ocorreu, quando, valor e período).
```

## 9. Testes

Os testes usam `unittest` e `unittest.mock` (dublês da API) e são executados com `pytest`.

```bash
# Testes SEM chamada real ao LLM (simulados) — não precisam de chave, de internet nem gastam crédito
pytest -v
# alternativa equivalente, sem pytest:  python -m unittest discover -s tests -t . -v

# Testes COM chamada real (opcionais; exigem internet e chave válida; consomem créditos)
RUN_REAL_TESTS=1 pytest tests/test_integracao_real.py -v      # PowerShell: $env:RUN_REAL_TESTS="1"
```

Sem `RUN_REAL_TESTS=1`, os 2 testes reais aparecem como *skipped* (ignorados), o que é o esperado.

| Tipo | O que cobre |
|---|---|
| **Simulados** (`test_entrada`, `test_config`, `test_prompt`, `test_resposta`, `test_cliente_llm`, `test_main`) | entrada vazia/grande, configuração ausente/inválida, **credencial ausente**, **credencial inválida** (HTTP 401/403 simulado), indisponibilidade (429/5xx), **falha de comunicação** e **timeout**, resposta vazia/truncada/inválida (nos dois formatos de API), logs sem segredos |
| **Reais** (`test_integracao_real`) | chamada real com entrada válida e **credencial inválida real** (chave falsa contra o serviço) |

Falhas reais também podem ser demonstradas manualmente: sem `.env` (credencial ausente),
`LLM_API_KEY=chave-falsa` (credencial inválida) e `LLM_API_URL=http://localhost:9` (falha de comunicação).

## 10. Registros de execução

`logs/execucao.log` guarda só metadados: data/hora, modelo, status HTTP, duração, tamanho da entrada
e número de lançamentos. **Nunca** grava chave, texto do fato operacional ou conteúdo da resposta
(há teste automatizado para isso). Motivo: o texto digitado pode conter dados pessoais ou sigilosos
(LGPD) e não é necessário para investigar o comportamento da aplicação.

## 11. Limitações conhecidas

- O modelo pode errar contas, valores ou o período de competência; **a revisão do contador é obrigatória**.
- Os nomes das contas são descritivos: não seguem o plano de contas oficial (COSIF) da instituição.
- Um fato por execução; sem novas tentativas automáticas em caso de indisponibilidade.
- A resposta pode variar entre execuções, mesmo com temperatura 0.
- Respostas muito longas podem ser cortadas por `LLM_MAX_TOKENS` (o programa avisa e orienta a aumentar).
- Não envie dados pessoais ou sigilosos reais a um provedor externo sem autorização da instituição.
  [Acrescente aqui as limitações que você observou nas suas execuções.]

## 12. Validação em ambiente limpo

[Data, sistema operacional, versão do Python e resultado de seguir apenas este README
em um novo ambiente virtual ou outro computador. Registre qualquer problema encontrado e a correção.]

## 13. Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `ModuleNotFoundError: No module named 'requests'` ou `'dotenv'` | ambiente virtual não ativado, ou `pip install` feito em outro Python | ative o `.venv` (prefixo `(.venv)`), rode `pip install -r requirements.txt` e confira com `python -c "import sys; print(sys.executable)"` que o Python é o do `.venv` |
| `ModuleNotFoundError: No module named 'lancamentos'` | comando executado fora da pasta do projeto | entre na raiz do repositório e use `python -m lancamentos` |
| PowerShell: "a execução de scripts foi desabilitada" | política de execução do Windows | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e ative o `.venv` de novo |
| `Erro: A variável LLM_API_KEY não foi encontrada` | `.env` não existe ou está em outra pasta | `cp .env.example .env` na raiz e preencha a chave |
| `O serviço recusou a credencial` (401) | chave errada, revogada ou com espaços | gere outra chave e atualize o `.env` |
| `Acesso negado pelo serviço (HTTP 403)` | sem permissão para o modelo ou bloqueio de proxy/firewall | confira `LLM_MODEL`, a rede (VPN/proxy) e as permissões da chave |
| `A resposta foi cortada por atingir o limite de tokens` | `LLM_MAX_TOKENS` baixo para o fato descrito | aumente `LLM_MAX_TOKENS` no `.env` (ex.: 3000) |
| `O serviço rejeitou a solicitação (HTTP 400)` | nome de modelo inválido ou parâmetro não aceito | confira `LLM_MODEL`; se necessário deixe `LLM_TEMPERATURE=` em branco |
| `pytest` não encontrado | dependências não instaladas | `pip install -r requirements.txt` com o `.venv` ativo |
| Funciona na minha máquina, não na de outra pessoa | Python < 3.10 ou dependência não declarada | confira `python --version` e instale só com `requirements.txt` em um `.venv` novo |

**Se uma chave real for parar no Git:** remover o arquivo depois **não** a retira do histórico. Revogue a
chave imediatamente no console do provedor, gere outra e só então limpe o histórico (passo a passo em
`docs/GUIA_ENTREGA.md`).

## 14. Documentos do projeto

- `RELATORIO_EXECUCAO.md` — evolução por nível, decisões, testes, falhas e uso de IA.
- `docs/GUIA_ENTREGA.md` — roteiro de commits, tags, pull request, ambiente limpo, chave vazada e vídeo.

## 15. Criar e exportar a imagem Docker

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

O arquivo `.env` não é incluído na imagem. Para executar o programa no container, crie e preencha
esse arquivo com as variáveis de acesso ao provedor e rode:

```powershell
docker run --rm -it --env-file .env meu-app:1.0
```

Se o Docker informar que não consegue conectar ao daemon/engine, inicie o Docker Desktop,
aguarde o engine ficar pronto e repita os comandos.
