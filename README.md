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
navegador → aplicação web Flask → API compatível com OpenAI → sugestão na página
```

O formulário web está em `app_web.py`. O backend usa o SDK OpenAI contra
`https://llm-internal.softex:9001/v1`, com o modelo `qwen3.5:9b-q4_K_M`.

## 4. Limites do projeto

Python, aplicação web, um único LLM, entrada e saída textuais. **Fora do escopo:** banco de dados,
RAG, agentes, plano de contas oficial (COSIF), integração com sistemas contábeis e contabilização
automática.

## 5. Instalação

Requisitos: **Python 3.10 ou superior** e Git. As dependências (Flask, Waitress, SDK OpenAI,
python-dotenv e pytest) são instaladas pelo arquivo `requirements.txt`.

```bash
git clone [URL do seu repositório]
cd [nome da pasta]
cd p0-conciliacao-competencia

# Linux / macOS / WSL  (no Ubuntu/WSL pode ser preciso: sudo apt-get install python3-venv python3-pip)
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

O ambiente está ativo quando o prefixo `(.venv)` aparece no início da linha do terminal.

## 6. Configuração do portal e do LLM

Para abrir a interface web do portal Devel, acesse
[https://devel-llm.eastus.cloudapp.azure.com/](https://devel-llm.eastus.cloudapp.azure.com/) no navegador e entre com
o acesso disponibilizado para você. Se o cadastro não estiver liberado, abra um ticket no Jira do Devel.

O portal é a interface web para acessar os recursos da LLM. O endpoint
`https://llm-internal.softex:9001/v1` é uma API usada pelo aplicativo P0, não a página web do portal.
Para gerar uma resposta, além do portal/cadastro, o computador ou container que executa a aplicação
precisa estar na rede que resolve `llm-internal.softex` e permite conexão na porta `9001`.

1. Copie o modelo de configuração:

```bash
cp .env.example .env
# Windows (PowerShell):
Copy-Item .env.example .env
```

2. O arquivo `.env` usa como padrão o endpoint OpenAI-compatible e o modelo indicados pelo ambiente.
   O arquivo `.env` está no `.gitignore`: **nunca o publique**.

Variáveis de configuração:

| Variável | Padrão | Função |
|---|---|---|
| `LLM_BASE_URL` | `https://llm-internal.softex:9001/v1` | URL base da API compatível com OpenAI |
| `LLM_API_KEY` | `qualquer` | chave aceita pelo serviço interno |
| `LLM_MODEL` | `qwen3.5:9b-q4_K_M` | modelo utilizado |
| `LLM_MAX_TOKENS` | 2000 | limite máximo de tokens gerados |
| `LLM_TIMEOUT` | 120 | segundos de espera pela resposta |

O certificado TLS da LLM é autogerado. O cliente HTTP do SDK está configurado com `verify=False`,
conforme o manual do serviço; use essa configuração apenas para o endpoint interno indicado.

## 7. Execução local

No PowerShell, partindo da pasta raiz do repositório:

```powershell
Set-Location .\p0-conciliacao-competencia
.\.venv\Scripts\Activate.ps1
python app_web.py
```

Se preferir não ativar o ambiente virtual, execute diretamente:

```powershell
Set-Location .\p0-conciliacao-competencia
.\.venv\Scripts\python.exe app_web.py
```

Mantenha o terminal aberto e acesse `http://localhost:8000` no navegador. Descreva o fato operacional
e selecione **Gerar sugestão**. Para encerrar o servidor, volte ao terminal e pressione `Ctrl+C`.
O serviço escuta em `0.0.0.0` na porta definida por `PORT` (padrão `8000`).

No Linux/macOS/WSL, partindo da raiz do repositório:

```bash
cd p0-conciliacao-competencia
source .venv/bin/activate
python app_web.py
```

Em qualquer sistema, a aplicação pode abrir mesmo sem acesso à LLM; nesse caso, o envio do formulário
mostrará um erro de conexão. No Windows, verifique a resolução e a porta do serviço com:

```powershell
Resolve-DnsName llm-internal.softex
Test-NetConnection llm-internal.softex -Port 9001
```

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

**Entrada vazia**:

```
Descreva o fato operacional.
```

## 9. Testes automatizados

Os testes em `tests/` usam mocks e não fazem chamadas ao serviço LLM. Eles cobrem a chamada OpenAI,
TLS, respostas inválidas, classificação de erros e rotas/formulário web.

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
- Cada envio é processado em uma requisição web; não há novas tentativas automáticas em caso de
  indisponibilidade.
- A resposta pode variar entre execuções. O programa detecta respostas vazias e truncamento pelo
  limite de tokens, mas não valida a correção contábil do conteúdo.
- O acesso ao serviço LLM depende da rede, do host configurado e da disponibilidade do provedor.

## 12. Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `ModuleNotFoundError` de Flask ou OpenAI | dependências não instaladas no ambiente ativo | ative o `.venv` (prefixo `(.venv)`) e rode `pip install -r requirements.txt` |
| PowerShell: "a execução de scripts foi desabilitada" | política de execução do Windows | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e ative o `.venv` de novo |
| Cadastro não liberado no portal Devel | acesso ainda não provisionado | abra um ticket no Jira do Devel |
| Falha de conexão com a LLM | sem conectividade à rede interna ou serviço indisponível | confira `LLM_BASE_URL` e se a rede resolve `llm-internal.softex` |
| `SSLCertVerificationError` | certificado autogerado da LLM | o cliente OpenAI usa `verify=False` conforme o manual; confirme que está executando a versão atual |
| Modelo não encontrado | nome do modelo inválido ou indisponível | confira `LLM_MODEL` |
| Acesso negado (401/403) | chave ou modelo sem autorização | confira `LLM_API_KEY` e solicite acesso pelo Jira do Devel |
| Aplicação web não responde | porta não publicada ou container não está saudável | publique a porta `8000` e confira os logs do container |
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

O arquivo `.env` não é incluído na imagem. Para executar o serviço web e publicar a porta `8000`:

```powershell
docker run --rm -p 8000:8000 --env-file .env meu-app:1.0
```

O container inicia o Waitress escutando em `0.0.0.0:8000`; não precisa de terminal interativo.
O Waitress usa a variável `PORT` (padrão `8000`). Se definir outra porta, publique a mesma porta
do container, por exemplo: `docker run --rm -p 9000:9000 -e PORT=9000 --env-file .env meu-app:1.0`.

Se o Docker informar que não consegue conectar ao daemon/engine, inicie o Docker Desktop,
aguarde o engine ficar pronto e repita os comandos.
