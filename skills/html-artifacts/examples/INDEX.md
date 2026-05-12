# Index — Exemplos Thariq de HTML artifacts

Biblioteca local dos 17 artifacts publicos do Thariq Shihipar (Anthropic,
Claude Code team) em https://thariqs.github.io/html-effectiveness/.

**Como ler:** cada linha mapeia (situacao no chat → template a copiar).
Quando o usuario pedir algo que case com uma linha, o agent abre o `.html`
correspondente, extrai a estrutura, adapta o conteudo, salva como artifact
novo em `.claude/_html/artifacts/`.

---

## Catalogo completo (17 templates)

| # | Arquivo | Titulo original (Thariq) | Quando usar | Estrutura-chave |
|---|---|---|---|---|
| 02 | `02-exploration-visual-designs.html` | Four visual directions for the "no tasks yet" state | Comparar **N opcoes visuais** lado-a-lado (2-6 alternativas) | Grid de cards iguais com mockup + label + tradeoffs |
| 03 | `03-code-review-pr.html` | Add optimistic updates to task list mutations | **Review de PR** mostrando arquivos+diffs+comentarios+decisoes | Layout 2 colunas: diff a esq, threads/decisoes a dir |
| 04 | `04-code-understanding.html` | How authentication flows through the codebase | **Mapa de fluxo** cruzando codebase (auth flow, request lifecycle) | Diagrama SVG + sequencia numerada + snippets de codigo |
| 05 | `05-design-system.html` | Birchline design system | **Sistema de design** completo (tokens, primitivos, componentes) | Cards por categoria (cores, fontes, espacamento, componentes) |
| 06 | `06-component-variants.html` | Card variant matrix | **Matriz de variantes** de UM componente (states x sizes) | Grid table de variantes renderizadas |
| 08 | `08-prototype-interaction.html` | Sidebar drag-to-reorder | **Prototipo interativo** demonstrando uma interacao | Demo funcional inline (JS) + descricao de gestures |
| 10 | `10-svg-illustrations.html` | Background jobs — header illustrations | **Ilustracoes SVG** para uma feature | Galeria SVG com legendas |
| 11 | `11-status-report.html` | Engineering Status — Week 11 | **Status report semanal/mensal** (entregas, riscos, metricas) | Header + secoes (delivered, in-flight, blocked, metrics) |
| 12 | `12-incident-report.html` | Elevated 502s on task sync | **Post-mortem de incidente** | Timeline + root cause + impact + action items |
| 13 | `13-flowchart-diagram.html` | What happens when you... | **Fluxograma** narrativo ("o que acontece quando X") | SVG nodes + edges + descricoes por step |
| 14 | `14-research-feature-explainer.html` | How rate limiting works in... | **Explainer de feature** (como X funciona, em profundidade) | Conceito + analogia + implementacao + edge cases |
| 15 | `15-research-concept-explainer.html` | Consistent hashing, in one ring | **Explainer de conceito** abstrato (algoritmo, padrao, teoria) | Hero diagram SVG + secoes progressivas + props |
| 16 | `16-implementation-plan.html` | Comment threads on task cards | **Plano de implementacao** detalhado (multi-fase, multi-arquivo) | Schema + fases + arquivos a tocar + decisoes + riscos |
| 17 | `17-pr-writeup.html` | #312 — Move notification delivery onto a queue | **PR writeup** pre-merge (resumo + decisoes + testing) | TL;DR + motivacao + mudancas + decisoes + how to test |
| 18 | `18-editor-triage-board.html` | Cycle 14 triage | **Triage board** (issues/items com swim lanes ou colunas) | Kanban-like com filtros |
| 19 | `19-editor-feature-flags.html` | flags.production.json | **Editor de config** (feature flags, settings estruturados) | Form rico + diff vs default + descricao por flag |
| 20 | `20-editor-prompt-tuner.html` | Support reply draft prompt | **Prompt tuning UI** (input, output, A/B compare) | Split: prompt a esq, output a dir, params no header |

---

## Decision tree (situacao no chat → template)

```
PEDIDO DO USUARIO
│
├─ "compara N opcoes / cenarios visuais"          → 02
├─ "review esse PR / essas mudancas"              → 03
├─ "explica como o codigo X funciona"             → 04
├─ "mapeia o fluxo de Y no codebase"              → 04
├─ "qual o design system / paleta / tokens"       → 05
├─ "matriz de variantes do componente Z"          → 06
├─ "prototipa essa interacao / gesture"           → 08
├─ "gera ilustracoes para a feature W"            → 10
├─ "status report da semana / sprint"             → 11
├─ "post-mortem do incidente"                     → 12
├─ "fluxograma do que acontece quando..."         → 13
├─ "explica essa feature em detalhe"              → 14
├─ "explica esse conceito (algoritmo/padrao)"     → 15
├─ "plano de implementacao para X"                → 16
├─ "writeup do PR / changelog antes de merge"     → 17
├─ "triage / kanban de issues/items"              → 18
├─ "editor de config / feature flags"             → 19
├─ "tune esse prompt / compare outputs"           → 20
│
└─ pedido nao bate exato                          → usar `gen_artifact.py table|report`
                                                    (templates basicos, sem Thariq style)
```

---

## Como o agente usa estes templates

### Fluxo padrao

1. **Detectar gatilho.** Pedido do usuario casa com 1 linha da decision tree.
2. **Ler o template fonte.** `Read .claude/skills/html-artifacts/examples/<NN>-*.html`
3. **Extrair estrutura.** Manter `<style>` inline, ajustar `<title>`, substituir conteudo
   das secoes pelo contexto do projeto.
4. **Salvar artifact novo.** `Write` em `.claude/_html/artifacts/<tipo>-YYYYMMDD-HHMMSS.html`
   ou path solicitado pelo usuario.
5. **Avisar no chat.** Caminho do arquivo + 1 linha do que esta dentro.
   Usuario abre com `start <path>`.

### Convencao de tipo no nome

`{tipo}-{YYYYMMDD}-{HHMMSS}.html` onde tipo e:
- `compare` (template 02)
- `pr-review` (03)
- `code-flow` (04)
- `design-system` (05)
- `variants` (06)
- `proto` (08)
- `illust` (10)
- `status` (11)
- `incident` (12)
- `flow` (13)
- `feature-explainer` (14)
- `concept-explainer` (15)
- `plan` (16)
- `pr-writeup` (17)
- `triage` (18)
- `config-editor` (19)
- `prompt-tuner` (20)

### Quando NAO usar template Thariq

- Pedido simples que cabe em prosa markdown no chat (resposta de 1-3 paragrafos).
- Pergunta conversacional / debug rapido.
- Voce explicitamente disse "manda no chat mesmo, sem html".

---

## Convencao de estilo do Thariq (extraida dos 17 exemplos)

Caracteristicas comuns que **eu devo preservar** ao adaptar:

| Aspecto | Valor padrao Thariq | Por que importa |
|---|---|---|
| Background | `#FAF9F5` (ivory) - nao branco puro | Tom editorial, nao tela de PC |
| Texto principal | `#141413` (slate) - quase preto | Contraste alto sem ser duro |
| Accent quente | `#D97757` (clay) ou `#B04A3F` (rust) | Diferenciacao por padrao, nao por hierarquia tech |
| Accent frio | `#788C5D` (olive) ou `#E3DACC` (oat) | Idem |
| Border | `1.5px solid` (nao 1px) | Mais presente, ar editorial |
| Radius | 8-12px (chunky) | Friendlier que 4px |
| Tipografia | Serif para titulos + sans para body + mono para code | Hierarquia por familia, nao so peso |
| Brand fictícia | "Birchline", "Acme", etc | Da identidade sem precisar real |
| Max-width | 860-1100px | Foco em legibilidade, nao expansao |
| Padding root | 56px+ vertical, 24px+ horizontal | Respiracao generosa |

**Quando adaptar pro nosso projeto:** posso trocar a brand pra "FX Studio" ou
"Tape Engine", trocar accent quente por algo que combine com trading (ouro?
verde gain?). Mantenho a estrutura, paleta editorial, hierarquia tipografica.

---

## Manutencao

- **Sincronizar quando o Thariq atualizar** algum template: rebaixar com curl.
  Comando: ver bloco no fim de `SKILL.md`.
- **Adicionar exemplos proprios** que provaram funcionar: salvar em
  `examples/9N-<descricao>.html` (N = numero sequencial 0, 1, 2... — gap
  proposital para nao colidir com os 02-20 do Thariq).
- **Remover** templates que provaram nao caber no projeto.

Fonte original: https://thariqs.github.io/html-effectiveness/
Baixado: 2026-05-11.
