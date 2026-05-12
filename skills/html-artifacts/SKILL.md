---
name: html-artifacts
description: "Use when the user requests visually complex output that does not fit cleanly in markdown chat - comparisons, plans, status reports, post-mortems, flowcharts, explainers of features or concepts, PR reviews, triage or kanban boards, config editors, prompt tuning UIs. Generates a self-contained HTML artifact in .claude/_html/artifacts/ from a curated 17-template library (Thariq Shihipar, Anthropic Claude Code team)."
---

# HTML Artifacts — Templates do Thariq

> **O que faz:** quando o pedido casar com um gatilho visualmente complexo
> (comparacao, plano, status, fluxograma, explainer, review de PR, kanban,
> config editor, prompt tuner), gera um arquivo HTML auto-contido em
> `.claude/_html/artifacts/<tipo>-<timestamp>.html` baseado num template
> real do Thariq Shihipar, e avisa o caminho no chat.
>
> **Por que:** terminal renderiza markdown em monospace. HTML inline na chat
> aparece como tag literal — pior que markdown. HTML em arquivo separado
> ganha SVG, navegacao, interatividade, hierarquia espacial, tipografia
> editorial. Tese central da "unreasonable effectiveness".

---

## Catalogo completo

**Lista dos 17 templates + decision tree + convencao de estilo + naming convention** vive em `examples/INDEX.md` (single source of truth). Sempre consultar la antes de gerar artifact.

**Catalogo trading** (schemas pydantic + renderers em `scripts/artifact_engine.py`):

| `type_id` | Template / Render | Gatilho |
|---|---|---|
| `table` | gen_artifact | Dataset tabular simples |
| `report` | gen_artifact | Texto + tabelas estruturado |
| `interactive` | Interactive Moderno | Painel com 10 tipos de input, validacao, localStorage |
| `backtest-comparison` | Thariq 16 (comparison) | Comparar N estrategias de backtest |
| `risk-dashboard` | Thariq 12 (kanban) | Painel de risco / exposicao |
| `signal-audit` | Thariq 13 (flowchart) | Audit trail de sinais / execucao |
| `market-regime` | Thariq 15 (concept) | Timeline de regimes / estados |
| `spec-requirements` | Spec Renderer | Spec de requirements (Kiro/GSD/generic) |
| `spec-design` | Spec Renderer | Spec de design / arquitetura |
| `spec-tasks` | Spec Renderer | Spec de tasks / checkpoints |

---

## Fluxo de uso (1 passo)

```python
from scripts.artifact_engine import ArtifactEngine
from pathlib import Path

engine = ArtifactEngine()

# 1. Dataset dict → artifact
path = engine.render("<type_id>", dataset_dict)  # pydantic valida + dispatch

# 2. Spec markdown → artifact (auto-detecta tipo: requirements/design/tasks)
path = engine.render_from_spec(Path(".kiro/specs/feat/requirements.md"))

# path → .claude/_html/artifacts/<type_id>-<timestamp>.html
# index.html atualizado automaticamente
```

**Sob o capo:**
1. `ArtifactEngine` consulta `_SCHEMA_MAP` e valida `dataset_dict` via pydantic
2. Consulta `_RENDERERS` — gen_artifact (legacy) ou `ThariqRenderer` (templates 11-20)
3. Persiste HTML em `.claude/_html/artifacts/`
4. Atualiza index: `scripts/build_artifact_index.py` gera `.claude/_html/artifacts/index.html`

Para regenerar o index manualmente:
```bash
python scripts/build_artifact_index.py .claude/_html/artifacts
```

---

## Common Mistakes

| Erro | Correcao |
|---|---|
| Despejar HTML inline no chat | Salvar como arquivo `.html` em `.claude/_html/artifacts/`, avisar path |
| Re-renderizar conteudo do HTML em markdown | Path + 1 linha resumo, deixar o user abrir no browser |
| Ignorar o catalogo de `INDEX.md` e improvisar | Sempre tentar bater com 1 dos templates primeiro |
| Combinar 2 templates sem pensar | Combinar e ok (ex: 16 + 13 para plano com fluxograma), mas estrutura comum vem do template "dominante" |
| Trocar a paleta editorial Thariq por cores aleatorias | Manter ivory/slate base. Pode trocar accent quente (clay) por algo do tema (ouro, verde gain). |
| Gerar artifact com dados sensiveis (secrets, IDs privados) sem confirmar | Perguntar antes de salvar |
| Esquecer de ler `INDEX.md` e usar gatilhos fora da decision tree | Decision tree e a SSOT — atualizar la se aparecer caso novo recorrente |
| Criar CSS inline duplicado em vez de herdar `base.css` | Templates novos devem linkar `../base.css` e conter apenas overrides |

---

## Manutencao

| Acao | Comando ou onde |
|---|---|
| Re-baixar exemplos quando Thariq publicar mais | Ver bloco `curl` no fim de `examples/INDEX.md` §Manutencao |
| Promover artifact recorrente a template proprio | Salvar em `examples/9N-<descricao>.html` (N = numero sequencial). Adicionar linha em `INDEX.md` §Catalogo. |
| Verificar saude | `ls .claude/skills/html-artifacts/examples/*.html \| wc -l` deve ser 17 (+ proprios 9N) |
| Atualizar gatilhos | Editar **apenas** `examples/INDEX.md` (decision tree e tabela). SKILL.md so referencia. |
| Testar suite | `pytest tests/html_artifacts/ -v` (102 tests) |
| Type check / lint | `mypy scripts/artifact_engine.py scripts/artifact_schemas.py scripts/build_artifact_index.py` |

---

## Limites

- Nao gera do nada — o usuario passa contexto, o agent monta.
- Nao roda no chat — output sempre vai pra arquivo.
- Nao substitui `gen_artifact.py table|report` (templates basicos sem estilo Thariq) — sao complementares.
- Nao renderiza HTML inline na chat — terminal nao suporta.

---

## Referencias

- Artigo fonte: https://thariqs.github.io/html-effectiveness/
- Autor: Thariq Shihipar (@trq212), Anthropic Claude Code team
- Posicao oficial: nao e recomendacao Anthropic — observacao pessoal de engenheiro do time, mas com peso interno
- Limite da tese: vale para **output** (artifacts em arquivo). Arquivos de **contexto** (CLAUDE.md, skills, agents) continuam markdown.
