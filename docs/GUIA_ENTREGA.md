# Guia de entrega do P0 (passo a passo)

Regras do curso que este guia segue:

- **Um repositório público por projeto** (P0, P1, P2, P3a, P3b, P4). O P0 tem o seu próprio.
- O nome é livre; sugestão: prefixo comum, como `pu57-p0-conciliacao-competencia`.
- O repositório é registrado no início e **deve ser o mesmo até o fim**.
- Tags de nome fixo: `p0-basico`, `p0-intermediario`, `p0-avancado`.
- Na entrega final você informa o link da tag `p0-avancado`; **é avaliado o estado do repositório nessa tag**.
- O P0 exige **pelo menos uma branch integrada por pull request**; o histórico de commits também é evidência.

Não publique tudo em um único commit. Reconstrua o projeto em etapas, lendo e entendendo cada módulo
antes de adicioná-lo, e faça cada commit quando realmente concluir aquela parte.

## 0. Antes de começar

### 0.1 Ferramentas (confira com o terminal)

```bash
git --version
python --version        # precisa ser 3.10 ou superior (no Linux/macOS/WSL: python3 --version)
git config --global user.name
git config --global user.email
```

Se nome e e-mail vierem vazios, configure (use o **mesmo e-mail da conta do GitHub**):

```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu@email.com"
```

### 0.2 Autenticação no GitHub (necessária para o `git push`)

- **Windows:** o Git Credential Manager, instalado com o Git, abre o navegador no primeiro `push`.
- **Qualquer sistema, com GitHub CLI:** `gh auth login` e siga as perguntas.
- Alternativa: Personal Access Token (Settings → Developer settings → Tokens) usado como senha.

### 0.3 Criar o repositório e registrar o link

1. GitHub → **New repository**; nome `pu57-p0-conciliacao-competencia` (ajuste o prefixo, se o seu for outro);
   **Public**.
2. **Repositório vazio** (sem README, sem .gitignore) é o caminho mais simples: o instrutor confirmou que
   pode começar vazio. Se você já o criou **com** README/.gitignore, também funciona; veja a nota 0.4.
3. Registre o link na atividade **Registro inicial do repositório** do Moodle.
4. Ative, em **Settings → Code security**, *Secret scanning* e *Push protection*, se disponíveis: o GitHub
   bloqueia o push se detectar uma chave de API.

### 0.4 Pasta local

**Caminho A: repositório vazio**

```bash
cd caminho/para/pasta-do-projeto
git init -b main
git remote add origin https://github.com/SEU_USUARIO/pu57-p0-conciliacao-competencia.git
git remote -v
```

**Caminho B: repositório criado com README/.gitignore**

```bash
git clone https://github.com/SEU_USUARIO/pu57-p0-conciliacao-competencia.git
cd pu57-p0-conciliacao-competencia
# copie seus arquivos para cá; ao colar o .gitignore e o README, substitua os gerados pelo GitHub
```

### 0.5 Ambiente virtual (um `.venv` por projeto, na raiz)

```bash
python -m venv .venv                       # Linux/macOS/WSL: python3 -m venv .venv
.venv\Scripts\Activate.ps1                 # Linux/macOS/WSL: source .venv/bin/activate
```

O prefixo `(.venv)` deve aparecer no terminal. No VS Code: `Ctrl+Shift+P` → *Python: Select Interpreter*
→ escolha o do `.venv`.

## 1. Nível Básico → tag `p0-basico`

Commits sugeridos na `main`:

```bash
# 1) estrutura segura
git add .gitignore .env.example requirements.txt
git status                     # CONFIRA: .env NÃO pode aparecer
git commit -m "chore: estrutura inicial com .gitignore, .env.example e dependências"

# 2) primeira chamada ao LLM (app_basico.py, veja o código abaixo)
git add app_basico.py
git commit -m "feat: primeira chamada ao LLM via API REST"

# 3) README inicial (problema, instalação, execução)
git add README.md
git commit -m "docs: README inicial com problema e instruções de execução"

git push -u origin main
git tag p0-basico
git push origin p0-basico
```

> Evite `git add .` até ter certeza de que o `.gitignore` está protegendo o `.env`. Prefira adicionar
> arquivos pelo nome e conferir `git status` antes de cada commit.

Antes do primeiro commit: `cp .env.example .env` (PowerShell: `Copy-Item .env.example .env`), preencha
`LLM_API_KEY` e `LLM_MODEL`, e confira que o `.env` aparece **acinzentado** no VS Code (ignorado pelo Git).

**`app_basico.py`** — menor fluxo funcional possível (terminal → LLM → resposta). Escreva-o você mesmo,
entendendo cada linha; este é só um ponto de partida (formato Anthropic; se o seu provedor usa
`chat/completions`, adapte conforme a documentação dele ou o `cliente_llm.py`):

```python
import os

import requests
from dotenv import load_dotenv

load_dotenv()
chave = os.environ["LLM_API_KEY"]
modelo = os.environ["LLM_MODEL"]

fato = input("Descreva o fato operacional: ")

resposta = requests.post(
    "https://api.anthropic.com/v1/messages",
    headers={
        "x-api-key": chave,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    },
    json={
        "model": modelo,
        "max_tokens": 1000,
        "system": "Transforme o fato operacional em lançamentos contábeis de partidas "
                  "dobradas pelo regime de competência. Explique a competência.",
        "messages": [{"role": "user", "content": fato}],
    },
    timeout=30,
)
print(resposta.json()["content"][0]["text"])
```

Remova `app_basico.py` quando o pacote `lancamentos/` o substituir (próxima etapa).

## 2. Nível Intermediário → PR e tag `p0-intermediario`

```bash
git switch -c feature/organizacao-e-erros

git add lancamentos/__init__.py lancamentos/erros.py lancamentos/entrada.py
git commit -m "feat: captura e validação de entrada (impede entrada vazia)"

git add lancamentos/config.py
git commit -m "feat: carregamento e validação da configuração"

git add lancamentos/prompt.py
git commit -m "feat: preparação da solicitação com prompt de competência"

git add lancamentos/cliente_llm.py
git commit -m "feat: cliente REST com tratamento de 401/403, 429/5xx, rede e timeout"

git add lancamentos/resposta.py lancamentos/apresentacao.py lancamentos/main.py lancamentos/__main__.py
git commit -m "feat: interpretação do JSON, apresentação e orquestração com códigos de saída"

git rm app_basico.py
git commit -m "refactor: remove script básico substituído pelo pacote lancamentos"

git add exemplos README.md
git commit -m "docs: exemplos de entrada e saída e instruções de configuração"

git push -u origin feature/organizacao-e-erros
```

Abra o PR e faça a auto-revisão (seção 5), integre e depois:

```bash
git switch main
git pull
git tag p0-intermediario
git push origin p0-intermediario
```

## 3. Nível Avançado → PR e tag `p0-avancado`

```bash
git switch -c feature/reprodutibilidade

git add lancamentos/logs.py
git commit -m "feat: registros de execução sem dados sensíveis"

git add pytest.ini tests/__init__.py tests/auxiliares.py tests/test_entrada.py tests/test_config.py tests/test_prompt.py
git commit -m "test: entrada, configuração e preparação da solicitação"

git add tests/test_resposta.py tests/test_cliente_llm.py tests/test_main.py
git commit -m "test: resposta, falhas simuladas da API e fluxo principal"

git add tests/test_integracao_real.py
git commit -m "test: testes reais opcionais (RUN_REAL_TESTS=1)"

git add README.md RELATORIO_EXECUCAO.md docs
git commit -m "docs: relatório de execução, limitações e guia de entrega"

git push -u origin feature/reprodutibilidade
```

Abra o PR, faça a auto-revisão (seção 5) e integre. **Antes de criar a tag**, valide em ambiente limpo
(seção 6) e complete README e relatório (nenhum `[PREENCHER]` pode sobrar). Só então:

```bash
git switch main
git pull
git tag p0-avancado
git push origin p0-avancado
```

Como a avaliação olha **o estado do repositório na tag `p0-avancado`**, tudo (código, README, relatório,
link do vídeo) precisa estar commitado e integrado antes dela. Se precisar corrigir algo **antes de
registrar a entrega final**, mova a tag para o commit corrigido:

```bash
git switch main && git pull
git tag -f p0-avancado
git push -f origin p0-avancado
```

Depois de registrada a entrega, não mova mais a tag.

## 4. Commits atômicos (evitar "ajustes" com 300 linhas)

Um commit = uma ideia, com mensagem que diz o quê (prefixos: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`).

- **Separar mudanças do mesmo arquivo:** no VS Code, abra o painel Git, clique no arquivo e use *Stage
  Selected Ranges* (ou o `+` ao lado de cada trecho). Pelo terminal: `git add -p`.
- **Já fez uma bagunça sem commitar:** `git status` e `git diff` para ver tudo; adicione por partes e
  faça vários commits.
- **Já commitou grande demais (ainda sem `push`):** `git reset --soft HEAD~1` desfaz o commit mantendo as
  mudanças; depois refaça em commits menores.
- Mensagens ruins: "ajustes", "final", "teste". Boas: "fix: trata timeout da chamada ao LLM".

## 5. Pull request com auto-revisão

Fluxo: **branch → push → PR → revisão → merge**.

1. Depois do `git push -u origin <branch>`, abra o repositório no GitHub e clique em **Compare & pull
   request**.
2. Título claro e descrição curta: *o que mudou*, *por que*, *como testei* (ex.: "pytest: 54 passam; testei
   entrada vazia e credencial inválida pelo terminal").
3. Abra a aba **Files changed** e leia o seu próprio diff como se fosse de outra pessoa. Confira:
   nenhuma chave ou `.env`; nenhum arquivo temporário; nenhum `print` de depuração; mensagens de erro claras.
4. Deixe pelo menos um comentário de revisão (botão `+` ao lado de uma linha → *Add single comment*, ou
   **Review changes → Comment**). Um autor não aprova o próprio PR; use "Comment".
5. Em **Merge pull request**, prefira **Create a merge commit** (ou *Rebase and merge*). **Evite
   "Squash and merge"**, porque ele junta todos os seus commits em um e apaga a evolução que o avaliador
   quer ver.
6. Clique em **Delete branch** e atualize a `main` local: `git switch main && git pull`.

## 6. Validação em ambiente limpo (fluxo da cartilha)

Faça a partir de uma cópia **nova do repositório**, em pasta vazia, seguindo **somente o README**:

```bash
cd /tmp                       # Windows: cd $env:TEMP
git clone https://github.com/SEU_USUARIO/pu57-p0-conciliacao-competencia.git limpo
cd limpo
python3 -m venv .venv                      # Windows: python -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                       # Windows: Copy-Item .env.example .env ; edite com sua chave
pytest -v                                  # tudo OK; os 2 testes reais aparecem como skipped
python -m lancamentos --arquivo exemplos/fato_energia.txt
```

Se tudo passar, o ambiente está reproduzível. Para auditar "funciona na minha máquina":

```bash
python -c "import sys; print(sys.executable)"      # deve apontar para dentro de .venv
pip list                                           # só o necessário, sem pacotes "globais" misteriosos
python --version                                   # compare com a versão declarada no README
```

Ideal: peça a outra pessoa para seguir somente o README. Anote data, sistema, versão do Python e resultado
no README (seção 12) e no relatório. Se algo falhar, corrija em novo commit e **registre o problema e a
correção**.

## 7. Se uma chave vazar no Git

Remover a chave do arquivo e commitar de novo **não a apaga do histórico**. Siga a ordem:

1. **Revogue a chave agora** no console do provedor (isto é o que de fato resolve; é obrigatório).
2. Gere uma chave nova e atualize só o seu `.env` local.
3. Limpe o histórico. Faça antes um backup (`git clone` do repositório em outra pasta). Com a ferramenta
   `git-filter-repo` (`pip install git-filter-repo`):

   ```bash
   # caso a chave esteja num arquivo que nunca deveria ter sido versionado (ex.: .env)
   git filter-repo --invert-paths --path .env

   # caso esteja dentro de um arquivo de código: crie "trocas.txt" com a linha  CHAVE_REAL==>REMOVIDA
   git filter-repo --replace-text trocas.txt
   ```

4. O `filter-repo` remove o `origin`; recoloque e force o envio (inclui as tags):

   ```bash
   git remote add origin https://github.com/SEU_USUARIO/pu57-p0-conciliacao-competencia.git
   git push --force --all
   git push --force --tags
   ```

5. Reconfira com a seção 8. Se o vazamento atingiu commits já tagueados, recrie as tags afetadas.

O repositório precisa continuar o **mesmo** (não apague e recrie): o link já foi registrado no Moodle.

## 8. Verificação de segredos antes de entregar

```bash
git ls-files | grep -E "^\.env$" && echo "ERRO: .env versionado!" || echo "ok: .env não versionado"
git log -p --all | grep -n -i -E "api[_-]?key *= *[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}" || echo "ok: nenhuma chave encontrada"
```

No PowerShell: `git log -p --all | Select-String -Pattern "sk-[A-Za-z0-9_-]{20,}"` (sem saída = ok).

## 9. Roteiro do vídeo (máximo 5 min, gravação de tela com narração)

| Tempo | Tópico | O que mostrar e dizer |
|---|---|---|
| 0:00–0:40 | **Problema** | O contador do banco público, fatos em texto livre, necessidade de lançamentos por competência. Mostre o `fato_energia.txt`. |
| 0:40–1:30 | **Solução** | Estrutura do repositório e fluxo: entrada → configuração → solicitação → LLM → validação do JSON → saída. Mostre o `README.md`. |
| 1:30–2:30 | **Execução normal** | Rode `python -m lancamentos --arquivo exemplos/fato_energia.txt`. Narre a entrada, a chamada e leia a competência na saída. |
| 2:30–3:30 | **Tratamento de falha** | Rode com entrada vazia e com chave inválida (ou sem `.env`); mostre a mensagem e o código de saída (`echo $?` / `echo $LASTEXITCODE`). Rode `pytest -v`. |
| 3:30–4:20 | **Decisão técnica** | Mostre o `.env` fora do Git (`.gitignore`) e o `cliente_llm.py`: REST, classificação de erros e por que a chave e o texto não vão ao log. |
| 4:20–5:00 | **Reflexão** | Uma limitação real (ex.: o modelo pode errar a competência) e como a IA foi usada (o que delegou, o que verificou e corrigiu). |

Publique no YouTube como **não listado**, revise as legendas automáticas (ou anexe transcrição), deixe
terminal e código legíveis (aumente a fonte) e coloque o link no README e no relatório.

## 10. Entrega final e avaliação por pares

1. Conferir: README completo (sem `[PREENCHER]`), `RELATORIO_EXECUCAO.md`, link do vídeo, as três tags,
   pelo menos um PR integrado, `.env.example` e `.gitignore`.
2. Registrar a entrega na atividade final do Moodle com o **link da tag `p0-avancado`**.
3. Avaliar duas entregas de outros alunos examinando repositório, relatório, testes e vídeo, comparando o
   que o relatório afirma com o que está nos artefatos.

## Apêndice: obstáculos da cartilha e onde estão resolvidos

| Obstáculo (cartilha) | Onde tratar |
|---|---|
| Instalei a biblioteca e o Python não encontra (Vídeo 1) | README, seção 13 |
| Resposta do modelo cortada (Vídeo 2) | README, seção 13; código: `LLM_MAX_TOKENS` e `ErroResposta` |
| Chave no histórico do Git (Vídeo 3) | este guia, seção 7 |
| Rede caiu e a aplicação quebrou (Vídeo 4) | `cliente_llm.py` e testes `test_cliente_llm.py` |
| Testar sem internet e sem gastar crédito (Vídeo 5) | `tests/` (dublês) |
| Commit "ajustes" com 300 linhas (Vídeo 6) | este guia, seção 4 |
| Abri o PR e agora? (Vídeo 7) | este guia, seção 5 |
| Log com a pergunta inteira (Vídeo 8) | `logs.py` e README, seção 10 |
| README que ninguém consegue rodar (Vídeo 9) | este guia, seção 6 e README |
| Funciona na minha máquina, não na do avaliador (Vídeo 10) | este guia, seção 6 (auditoria do ambiente) |
