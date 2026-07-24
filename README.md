# 🎭 DKidsFantasias · BI de Vendas

Aplicação web de inteligência comercial para a loja DKidsFantasias. Transforma o
histórico de vendas em decisões: concentração de receita, sazonalidade, mix de
pagamentos e previsão de faturamento com validação estatística honesta.

**100% standalone** — roda em qualquer navegador, sem instalar Python, sem servidor
e sem dependências. É só abrir a pasta [`webapp/`](webapp) e pronto.

## 📊 Módulos

| Página | O que entrega |
|---|---|
| **🎭 Visão Executiva** | KPIs do negócio, evolução mensal, mix de categorias, top produtos e insights automáticos |
| **🧸 Produtos & Portfólio** | Curva ABC (Pareto), matriz estratégica Volume × Ticket, performance por categoria e auditoria de consistência de preço |
| **⏱️ Temporalidade** | Sazonalidade mensal e semanal, mapa de calor dia × hora, melhores dias e horários de pico |
| **💳 Pagamentos** | Mix de recebimento, ticket médio por forma, evolução do share mês a mês |
| **🔮 Previsão** | Projeção de 30 dias com validação em holdout (28 dias fora do treino), MAE/WMAPE honestos e intervalo de confiança de 95% |

## ✨ Diferenciais

- **Zero infraestrutura:** um dashboard BI completo em HTML + JavaScript puro (ECharts). Pode ser aberto com dois cliques, hospedado em qualquer site estático ou enviado por e-mail/pendrive.
- **Insights automáticos:** todos os textos analíticos são calculados dos dados — se atualizam com os filtros.
- **Filtros globais** (período, categoria, forma de pagamento) aplicados a todas as análises em tempo real.
- **Previsão validada:** o modelo é avaliado em dias que nunca viu e reporta erro real — sem ilusão de precisão.
- **Identidade visual própria:** paleta, tipografia e componentes consistentes em todas as telas. Formatação monetária pt-BR.

## 🚀 Como usar

### Opção 1 — Abrir direto (mais simples)
1. Abra `webapp/index.html` no navegador (duplo clique).
2. Na primeira vez, arraste o arquivo `data/vendas_tratadas.csv` para a tela.
   O navegador memoriza a base — nas próximas aberturas carrega sozinho.

### Opção 2 — Servidor local (carrega o CSV automaticamente)
```bash
python -m http.server 8765
```
Depois acesse: `http://localhost:8765/webapp/`

### Opção 3 — Publicar no GitHub Pages (já configurado neste repositório)
A pasta [`docs/`](docs) é o espelho de publicação: contém uma cópia de `webapp/` +
`data/vendas_tratadas.csv` pronta para o GitHub Pages servir direto do branch `main`.

Para ativar (uma vez só): **Settings → Pages → Source: Deploy from a branch →
Branch: `main` / `docs` → Save**. Em ~1 minuto o site fica público em
`https://<usuario>.github.io/<repositorio>/`.

> ⚠️ O repositório é público, então o link fica acessível a qualquer pessoa —
> incluindo os números reais de faturamento. Torne o repositório privado
> (exige GitHub Pro para Pages em repo privado) se isso for um problema.

### Opção 4 — Outra hospedagem estática
Envie a pasta `webapp/` (+ `data/`) para qualquer hospedagem estática (Netlify,
Vercel, S3...). A aplicação encontra o CSV em `../data/` automaticamente.

## 🔄 Atualizando os dados

Basta substituir `data/vendas_tratadas.csv` por uma versão mais recente com as
mesmas colunas (ou arrastar o novo arquivo na tela de abertura). Todos os números,
gráficos, insights e a previsão se recalculam sozinhos.

Para regenerar o CSV tratado a partir da base bruta: `python export.py`.

Depois de atualizar os dados ou editar `webapp/`, rode `./sync_docs.sh` para
espelhar as mudanças em `docs/` antes de dar commit/push — é isso que mantém o
GitHub Pages em dia.

## 🗂️ Arquitetura

```
├── webapp/                 # ⭐ Aplicação web (BI standalone)
│   ├── index.html          # Estrutura das 5 páginas
│   ├── css/style.css       # Identidade visual
│   └── js/
│       ├── engine.js       # Parse do CSV, agregações, insights e modelo de previsão
│       └── app.js          # Interface: filtros, gráficos ECharts, tabelas e navegação
├── docs/                   # Espelho de publicação (GitHub Pages serve daqui)
├── sync_docs.sh            # Copia webapp/ + data/ para docs/
├── data/
│   └── vendas_tratadas.csv # Base tratada de vendas
├── export.py               # Pipeline: gera o CSV tratado a partir do bruto
└── core/, app.py, views/   # Versão anterior em Streamlit (legado)
```

## 🔮 Metodologia da previsão

- **Modelo:** sazonalidade semanal (média ponderada dos últimos 4 mesmos dias da semana)
  com fator de tendência amortecido (últimos 14 dias vs 14 anteriores).
- **Validação:** os últimos 28 dias de venda são previstos usando apenas o passado de
  cada um — as métricas exibidas (MAE, WMAPE, cobertura) vêm exclusivamente desse período.
- **Intervalo de 95%:** desvio-padrão dos erros de validação × 1,96.
- **Projeção:** dia a dia, realimentando o histórico; dias sem funcionamento são excluídos.

## 🛠️ Stack

HTML5 · CSS3 · JavaScript (ES2020) · [Apache ECharts](https://echarts.apache.org/) 5
