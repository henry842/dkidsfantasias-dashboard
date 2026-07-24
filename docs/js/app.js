/* ============================================================
   DKidsFantasias BI · app.js
   Camada de interface: carga do CSV, filtros, gráficos ECharts,
   tabelas e navegação entre vistas.
   ============================================================ */

"use strict";

/* ----------------------- Paleta ----------------------- */
const C = {
  primary: "#6C3BD9", primarySoft: "#C9B8F2", secondary: "#F72585",
  accent: "#FFB703", teal: "#2EC4B6", sky: "#4CC9F0",
  text: "#3A3752", muted: "#8B87A0", grade: "#EEEBF7", escuro: "#3A3752",
};
const PALETA = [C.primary, C.secondary, C.accent, C.teal, C.sky, "#B5179E", "#FF6B6B", "#8AC926"];

/* ----------------------- Estado ----------------------- */
const estado = {
  registros: [],
  filtrados: [],
  graficos: new Map(),   // id do container -> instância ECharts
  prevCache: null,
  vistaAtual: "home",
};

/* ----------------------- Base ECharts ----------------------- */
const FONTE = { fontFamily: "Inter, sans-serif", color: C.text };

function opcoesBase() {
  return {
    textStyle: FONTE,
    grid: { left: 8, right: 16, top: 30, bottom: 8, containLabel: true },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#fff", borderColor: C.grade,
      textStyle: { color: C.text, fontSize: 12, fontFamily: "Inter, sans-serif" },
      axisPointer: { type: "shadow" },
    },
  };
}

const eixoValor = (extra = {}) => ({
  type: "value",
  axisLabel: { color: C.muted, fontSize: 11, formatter: (v) => fmtCompact(v) },
  splitLine: { lineStyle: { color: C.grade } },
  ...extra,
});

const eixoCat = (dados, extra = {}) => ({
  type: "category", data: dados,
  axisLabel: { color: C.muted, fontSize: 11 },
  axisLine: { lineStyle: { color: "#E0DCEF" } },
  axisTick: { show: false },
  ...extra,
});

function grafico(id, opcoes) {
  let inst = estado.graficos.get(id);
  const el = document.getElementById(id);
  if (!el) return;
  if (!inst) {
    inst = echarts.init(el);
    estado.graficos.set(id, inst);
  }
  inst.setOption(opcoes, true);
  inst.resize();
}

window.addEventListener("resize", () => estado.graficos.forEach((g) => g.resize()));

/* ============================================================
   Carga do CSV
   ============================================================ */
const CAMINHOS_CSV = ["data/vendas_tratadas.csv", "../data/vendas_tratadas.csv"];
const CHAVE_LS = "dkids_csv_v1";

async function carregarCSV() {
  for (const caminho of CAMINHOS_CSV) {
    try {
      const resp = await fetch(caminho, { cache: "no-store" });
      if (resp.ok) {
        const texto = await resp.text();
        if (texto.length > 200 && texto.includes("Codigo_da_Venda")) return texto;
      }
    } catch (_) { /* file:// bloqueia fetch — segue para o fallback */ }
  }
  try {
    const salvo = localStorage.getItem(CHAVE_LS);
    if (salvo && salvo.length > 200) return salvo;
  } catch (_) {}
  return esperarArquivo();
}

function esperarArquivo() {
  return new Promise((resolver) => {
    const zona = document.getElementById("zonaDrop");
    const botao = document.getElementById("btnEscolher");
    const input = document.getElementById("inputCsv");
    document.getElementById("msgCarga").innerHTML =
      "Para começar, carregue a base de vendas:<br><b>vendas_tratadas.csv</b><br>(arraste o arquivo aqui ou clique abaixo — fica salvo no navegador)";
    botao.style.display = "inline-flex";

    const lerArquivo = (arquivo) => {
      const leitor = new FileReader();
      leitor.onload = () => {
        const texto = String(leitor.result);
        try { localStorage.setItem(CHAVE_LS, texto); } catch (_) {}
        resolver(texto);
      };
      leitor.readAsText(arquivo, "utf-8");
    };

    botao.onclick = () => input.click();
    input.onchange = () => input.files.length && lerArquivo(input.files[0]);
    zona.ondragover = (e) => { e.preventDefault(); zona.classList.add("sobre"); };
    zona.ondragleave = () => zona.classList.remove("sobre");
    zona.ondrop = (e) => {
      e.preventDefault(); zona.classList.remove("sobre");
      if (e.dataTransfer.files.length) lerArquivo(e.dataTransfer.files[0]);
    };
  });
}

/* ============================================================
   Filtros
   ============================================================ */
function popularFiltros() {
  const regs = estado.registros;
  const ini = document.getElementById("fltIni");
  const fim = document.getElementById("fltFim");
  ini.min = fim.min = regs[0].dataStr;
  ini.max = fim.max = regs[regs.length - 1].dataStr;
  ini.value = regs[0].dataStr;
  fim.value = regs[regs.length - 1].dataStr;

  const preencher = (id, valores) => {
    const sel = document.getElementById(id);
    [...valores].sort().forEach((v) => {
      const op = document.createElement("option");
      op.value = op.textContent = v;
      sel.appendChild(op);
    });
  };
  preencher("fltCategoria", new Set(regs.map((r) => r.categoria)));
  preencher("fltPagamento", new Set(regs.map((r) => r.pagamento)));

  ["fltIni", "fltFim", "fltCategoria", "fltPagamento"].forEach((id) =>
    document.getElementById(id).addEventListener("change", aoFiltrar)
  );
  document.getElementById("btnLimpar").addEventListener("click", () => {
    ini.value = ini.min; fim.value = fim.max;
    document.getElementById("fltCategoria").value = "";
    document.getElementById("fltPagamento").value = "";
    aoFiltrar();
  });
}

function aoFiltrar() {
  const ini = document.getElementById("fltIni").value;
  const fim = document.getElementById("fltFim").value;
  const cat = document.getElementById("fltCategoria").value;
  const pag = document.getElementById("fltPagamento").value;

  estado.filtrados = estado.registros.filter((r) =>
    (!ini || r.dataStr >= ini) && (!fim || r.dataStr <= fim) &&
    (!cat || r.categoria === cat) && (!pag || r.pagamento === pag)
  );

  const pct = Math.round((estado.filtrados.length / estado.registros.length) * 100);
  document.getElementById("resumoFiltro").innerHTML =
    `<b>${fmtInt(estado.filtrados.length)}</b> itens no recorte (${pct}% da base)`;

  renderizarVista(estado.vistaAtual);
}

/* ============================================================
   Navegação
   ============================================================ */
document.getElementById("navPrincipal").addEventListener("click", (e) => {
  const botao = e.target.closest("button[data-vista]");
  if (!botao) return;
  document.querySelectorAll("#navPrincipal button").forEach((b) => b.classList.remove("ativo"));
  botao.classList.add("ativo");
  document.querySelectorAll(".vista").forEach((v) => v.classList.remove("ativa"));
  const nome = botao.dataset.vista;
  document.getElementById("vista-" + nome).classList.add("ativa");
  estado.vistaAtual = nome;
  renderizarVista(nome);
});

function renderizarVista(nome) {
  const df = estado.filtrados;
  const vazio = !df.length;
  if (nome === "home") vazio ? limparVista("home") : vistaHome(df);
  if (nome === "produtos") vazio ? limparVista("produtos") : vistaProdutos(df);
  if (nome === "temporalidade") vazio ? limparVista("temporalidade") : vistaTemporalidade(df);
  if (nome === "pagamentos") vazio ? limparVista("pagamentos") : vistaPagamentos(df);
  if (nome === "previsao") vistaPrevisao();
}

function limparVista(nome) {
  const alvos = { home: "kpisHome", produtos: "kpisProdutos", temporalidade: "kpisTempo", pagamentos: "kpisPag" };
  document.getElementById(alvos[nome]).innerHTML =
    '<div class="kpi" style="grid-column:1/-1">⚠️ Nenhum dado no recorte selecionado — ajuste os filtros.</div>';
}

/* ----------------------- Componentes ----------------------- */
function kpisHTML(cards) {
  return cards.map((c) => `
    <div class="kpi" style="border-top-color:${c.cor || C.primary}">
      <div class="rotulo">${c.rotulo}</div>
      <div class="valor">${c.valor}</div>
      ${c.delta ? `<div class="delta ${c.dir || ""}">${c.dir === "up" ? "▲" : c.dir === "down" ? "▼" : "•"} ${c.delta}</div>` : ""}
    </div>`).join("");
}

const insightHTML = (i) =>
  `<div class="insight ${i.tom === "warn" ? "warn" : ""}"><div class="t">${i.titulo}</div><div class="x">${i.texto}</div></div>`;

const ordenar = (mapa) => [...mapa.entries()].sort((a, b) => b[1] - a[1]);

/* ============================================================
   VISTA · Home
   ============================================================ */
function vistaHome(df) {
  const k = kpisGerais(df);
  const regs = estado.registros;
  document.getElementById("heroHomeSub").textContent =
    `Panorama consolidado do negócio · Dados de ${dataStrBR(regs[0].dataStr)} a ${dataStrBR(regs[regs.length - 1].dataStr)}`;

  document.getElementById("kpisHome").innerHTML = kpisHTML([
    { rotulo: "Faturamento", valor: fmtBRL(k.faturamento), cor: C.primary,
      delta: k.variacaoMM != null ? fmtPct(Math.abs(k.variacaoMM)) + " vs mês anterior" : null,
      dir: k.variacaoMM != null ? (k.variacaoMM >= 0 ? "up" : "down") : null },
    { rotulo: "Vendas realizadas", valor: fmtInt(k.nVendas), cor: C.secondary },
    { rotulo: "Itens vendidos", valor: fmtInt(k.itens), cor: C.accent },
    { rotulo: "Ticket médio", valor: fmtBRL(k.ticketMedio), cor: C.teal },
    { rotulo: "Produtos ativos", valor: fmtInt(k.produtosAtivos), cor: C.sky },
  ]);

  // Mensal: barras + linha
  const mensal = serieMensal(df);
  grafico("gMensalHome", {
    ...opcoesBase(),
    tooltip: { ...opcoesBase().tooltip, valueFormatter: (v) => fmtBRL(v) },
    xAxis: eixoCat(mensal.map((m) => mesKeyLabel(m[0]))),
    yAxis: eixoValor(),
    series: [
      { name: "Faturamento", type: "bar", data: mensal.map((m) => m[1]),
        itemStyle: { color: C.primary, borderRadius: [6, 6, 0, 0], opacity: 0.85 }, barMaxWidth: 46 },
      { name: "Tendência", type: "line", data: mensal.map((m) => m[1]),
        smooth: true, symbolSize: 8, lineStyle: { color: C.secondary, width: 3 }, itemStyle: { color: C.secondary } },
    ],
  });

  // Categorias: donut
  const cats = ordenar(somaPor(df, (r) => r.categoria));
  grafico("gCategorias", {
    textStyle: FONTE,
    tooltip: { trigger: "item", valueFormatter: (v) => fmtBRL(v),
      backgroundColor: "#fff", borderColor: C.grade, textStyle: { color: C.text, fontSize: 12 } },
    legend: { bottom: 0, textStyle: { color: C.muted, fontSize: 11 }, itemWidth: 12, itemHeight: 12 },
    color: PALETA,
    series: [{
      type: "pie", radius: ["48%", "72%"], center: ["50%", "44%"],
      itemStyle: { borderRadius: 5, borderColor: "#fff", borderWidth: 2 },
      label: { show: true, formatter: (p) => p.percent >= 5 ? p.percent.toFixed(0) + "%" : "", fontSize: 11, color: C.text },
      data: cats.map(([nome, valor]) => ({ name: nome, value: Math.round(valor * 100) / 100 })),
    }],
  });

  // Top produtos: barras horizontais
  const top10 = ordenar(somaPor(df, (r) => r.produto)).slice(0, 10).reverse();
  grafico("gTopProdutos", {
    ...opcoesBase(),
    tooltip: { ...opcoesBase().tooltip, valueFormatter: (v) => fmtBRL(v) },
    grid: { left: 8, right: 46, top: 10, bottom: 8, containLabel: true },
    xAxis: eixoValor(),
    yAxis: eixoCat(top10.map((p) => p[0]), { axisLabel: { color: C.text, fontSize: 11, width: 190, overflow: "truncate" } }),
    series: [{
      type: "bar", data: top10.map((p) => p[1]), barMaxWidth: 20,
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: C.primarySoft }, { offset: 1, color: C.primary }]),
      },
      label: { show: true, position: "right", formatter: (p) => fmtCompact(p.value), fontSize: 10.5, color: C.muted },
    }],
  });

  // Dia da semana
  const porDia = somaPor(df, (r) => r.diaSemanaPt);
  const diasPresentes = DIAS_PT.filter((d) => porDia.has(d));
  grafico("gDiaSemanaHome", {
    ...opcoesBase(),
    tooltip: { ...opcoesBase().tooltip, valueFormatter: (v) => fmtBRL(v) },
    xAxis: eixoCat(diasPresentes),
    yAxis: eixoValor(),
    series: [{
      type: "bar", data: diasPresentes.map((d) => porDia.get(d) || 0), barMaxWidth: 40,
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 1, 0, 0, [
          { offset: 0, color: "#BFEAE6" }, { offset: 1, color: C.teal }]),
      },
    }],
  });

  document.getElementById("insightsHome").innerHTML =
    insightsExecutivos(df).map(insightHTML).join("");
}

/* ============================================================
   VISTA · Produtos
   ============================================================ */
function vistaProdutos(df) {
  const total = totalFat(df);
  const regs = estado.registros;
  document.getElementById("heroProdutosSub").textContent =
    `Concentração de receita, curva ABC e posicionamento estratégico · ${dataStrBR(regs[0].dataStr)} a ${dataStrBR(regs[regs.length - 1].dataStr)}`;

  // Curva ABC
  const fatProd = ordenar(somaPor(df, (r) => r.produto));
  let acum = 0;
  const abc = fatProd.map(([produto, valor], i) => {
    acum += valor;
    const pct = (acum / total) * 100;
    return { produto, valor, acumPct: pct, classe: pct <= 80 ? "A" : pct <= 95 ? "B" : "C", rank: i + 1 };
  });
  const nA = abc.filter((p) => p.classe === "A").length;
  const nB = abc.filter((p) => p.classe === "B").length;
  const nC = abc.filter((p) => p.classe === "C").length;
  const top5Pct = (abc.slice(0, 5).reduce((s, p) => s + p.valor, 0) / total) * 100;

  document.getElementById("kpisProdutos").innerHTML = kpisHTML([
    { rotulo: "Produtos no portfólio", valor: fmtInt(abc.length), cor: C.primary },
    { rotulo: "Classe A (80% da receita)", valor: nA + " produtos", cor: C.secondary },
    { rotulo: "Classe B (15% seguintes)", valor: nB + " produtos", cor: C.accent },
    { rotulo: "Classe C (cauda longa)", valor: nC + " produtos", cor: C.teal },
    { rotulo: "Top 5 concentram", valor: fmtPct(top5Pct), cor: C.sky },
  ]);

  // Pareto
  const pareto = abc.slice(0, 30);
  const corClasse = { A: C.primary, B: C.accent, C: "#C9C5DB" };
  grafico("gPareto", {
    ...opcoesBase(),
    tooltip: {
      ...opcoesBase().tooltip,
      formatter: (ps) => {
        const p = pareto[ps[0].dataIndex];
        return `<b>${p.produto}</b><br>Faturamento: ${fmtBRL(p.valor)}<br>Acumulado: ${fmtPct(p.acumPct)}<br>Classe: ${p.classe}`;
      },
    },
    legend: { top: 0, textStyle: { color: C.muted, fontSize: 11 }, data: ["Faturamento", "Acumulado (%)"] },
    xAxis: eixoCat(pareto.map((p) => p.rank), { name: "ranking", nameTextStyle: { color: C.muted, fontSize: 10 } }),
    yAxis: [
      eixoValor(),
      { type: "value", max: 100, axisLabel: { color: C.muted, fontSize: 11, formatter: "{value}%" }, splitLine: { show: false } },
    ],
    series: [
      { name: "Faturamento", type: "bar", data: pareto.map((p) => ({ value: p.valor, itemStyle: { color: corClasse[p.classe], borderRadius: [4, 4, 0, 0] } })), barMaxWidth: 26 },
      { name: "Acumulado (%)", type: "line", yAxisIndex: 1, data: pareto.map((p) => Math.round(p.acumPct * 10) / 10),
        smooth: true, symbolSize: 6, lineStyle: { color: C.secondary, width: 2.5 }, itemStyle: { color: C.secondary },
        markLine: { silent: true, symbol: "none", lineStyle: { color: C.secondary, type: "dashed", opacity: 0.6 },
          label: { formatter: "80%", color: C.secondary }, data: [{ yAxis: 80 }] } },
    ],
  });

  document.getElementById("insightAbc").innerHTML = insightHTML({
    titulo: "🎯 Leitura",
    texto: `<b>${nA} produtos (Classe A)</b> sustentam 80% do faturamento — prioridade absoluta em estoque, exposição e reposição. ` +
      `Os <b>${nC} produtos da Classe C</b> respondem por apenas 5% da receita: avalie enxugar o portfólio ou usá-los como complemento de ticket.`,
    tom: "warn",
  });

  // Matriz estratégica
  const porProduto = agrupar(df, (r) => r.produto);
  const mapa = [...porProduto.entries()].map(([produto, itens]) => {
    const volume = itens.reduce((s, r) => s + r.qtd, 0);
    const ticket = itens.reduce((s, r) => s + r.valorUnit, 0) / itens.length;
    const fat = itens.reduce((s, r) => s + r.subtotal, 0);
    return { produto, volume, ticket, fat };
  });
  const mediana = (arr) => {
    const s = [...arr].sort((a, b) => a - b);
    return s.length % 2 ? s[(s.length - 1) / 2] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2;
  };
  const volMed = mediana(mapa.map((m) => m.volume));
  const tktMed = mediana(mapa.map((m) => m.ticket));
  const perfilDe = (m) =>
    m.volume >= volMed && m.ticket >= tktMed ? "⭐ Estrela" :
    m.volume >= volMed ? "📦 Fluxo" :
    m.ticket >= tktMed ? "💎 Premium" : "⚠️ Baixo impacto";
  mapa.forEach((m) => (m.perfil = perfilDe(m)));

  const fatMax = Math.max(...mapa.map((m) => m.fat));
  const corPerfil = { "⭐ Estrela": C.primary, "📦 Fluxo": C.teal, "💎 Premium": C.accent, "⚠️ Baixo impacto": "#C9C5DB" };
  const seriesMatriz = Object.keys(corPerfil).map((perfil) => ({
    name: perfil, type: "scatter",
    data: mapa.filter((m) => m.perfil === perfil).map((m) => ({
      value: [m.volume, m.ticket], produto: m.produto, fat: m.fat,
    })),
    symbolSize: (v, p) => 6 + Math.sqrt(p.data.fat / fatMax) * 30,
    itemStyle: { color: corPerfil[perfil], opacity: 0.75 },
  }));
  seriesMatriz[0].markLine = {
    silent: true, symbol: "none",
    lineStyle: { type: "dashed", color: "#A8A4BC" }, label: { show: false },
    data: [{ xAxis: volMed }, { yAxis: tktMed }],
  };
  grafico("gMatriz", {
    textStyle: FONTE,
    tooltip: {
      backgroundColor: "#fff", borderColor: C.grade, textStyle: { color: C.text, fontSize: 12 },
      formatter: (p) => `<b>${p.data.produto}</b><br>${p.seriesName}<br>Unidades: ${fmtInt(p.value[0])}<br>Preço médio: ${fmtBRL(p.value[1])}<br>Faturamento: ${fmtBRL(p.data.fat)}`,
    },
    legend: { bottom: 0, textStyle: { color: C.muted, fontSize: 11 } },
    grid: { left: 8, right: 20, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: "log", logBase: 10, name: "Volume (un)", nameTextStyle: { color: C.muted },
      axisLabel: { color: C.muted, fontSize: 11 }, splitLine: { lineStyle: { color: C.grade } }, min: 0.9 },
    yAxis: { type: "value", name: "Preço médio (R$)", nameTextStyle: { color: C.muted },
      axisLabel: { color: C.muted, fontSize: 11 }, splitLine: { lineStyle: { color: C.grade } } },
    series: seriesMatriz,
  });

  const estrelas = mapa.filter((m) => m.perfil === "⭐ Estrela").sort((a, b) => b.fat - a.fat).slice(0, 3).map((m) => m.produto);
  const premium = mapa.filter((m) => m.perfil === "💎 Premium").sort((a, b) => b.ticket - a.ticket).slice(0, 2).map((m) => m.produto);
  document.getElementById("insightsMatriz").innerHTML =
    (estrelas.length ? insightHTML({
      titulo: "⭐ Estrelas do portfólio",
      texto: `Produtos que combinam giro e valor: <b>${estrelas.join("</b>, <b>")}</b>. Nunca deixe faltar em estoque — cada ruptura aqui custa caro.`,
      tom: "ok" }) : "") +
    (premium.length ? insightHTML({
      titulo: "💎 Âncoras premium",
      texto: `Itens de alto valor como <b>${premium.join("</b>, <b>")}</b> elevam a percepção da loja e funcionam como âncora de preço em vitrines e combos.`,
      tom: "ok" }) : "");

  // Tabela categorias
  const porCat = agrupar(df, (r) => r.categoria);
  const linhasCat = [...porCat.entries()].map(([cat, itens]) => ({
    cat,
    fat: itens.reduce((s, r) => s + r.subtotal, 0),
    un: itens.reduce((s, r) => s + r.qtd, 0),
    preco: itens.reduce((s, r) => s + r.valorUnit, 0) / itens.length,
    nProd: new Set(itens.map((r) => r.produto)).size,
  })).sort((a, b) => b.fat - a.fat);

  document.getElementById("tCategorias").innerHTML = `
    <table><thead><tr>
      <th>Categoria</th><th class="num">Faturamento</th><th class="num">Un.</th>
      <th class="num">Preço médio</th><th class="num">Produtos</th><th>Participação</th>
    </tr></thead><tbody>
    ${linhasCat.map((l) => `<tr>
      <td><b>${l.cat}</b></td>
      <td class="num">${fmtBRL(l.fat)}</td>
      <td class="num">${fmtInt(l.un)}</td>
      <td class="num">${fmtBRL(l.preco)}</td>
      <td class="num">${l.nProd}</td>
      <td><div class="barra-prog"><div style="width:${((l.fat / total) * 100).toFixed(1)}%"></div></div>
          <span style="font-size:11px;color:${C.muted}">${fmtPct((l.fat / total) * 100)}</span></td>
    </tr>`).join("")}
    </tbody></table>`;

  // Consistência de preço
  const precos = [...porProduto.entries()].map(([produto, itens]) => {
    const vendas = new Set(itens.map((r) => r.venda)).size;
    const vals = itens.map((r) => r.valorUnit);
    const media = vals.reduce((a, b) => a + b, 0) / vals.length;
    const desvio = vals.length > 1 ? Math.sqrt(vals.reduce((s, v) => s + (v - media) ** 2, 0) / (vals.length - 1)) : 0;
    return { produto, vendas, min: Math.min(...vals), max: Math.max(...vals), media, cv: media > 0 ? (desvio / media) * 100 : 0 };
  }).filter((p) => p.vendas >= 3 && p.cv > 0).sort((a, b) => b.cv - a.cv).slice(0, 8);

  document.getElementById("tPrecos").innerHTML = precos.length ? `
    <table><thead><tr>
      <th>Produto</th><th class="num">Vendas</th><th class="num">Mín</th><th class="num">Médio</th><th class="num">Máx</th><th class="num">Variação</th>
    </tr></thead><tbody>
    ${precos.map((p) => `<tr>
      <td>${p.produto}</td>
      <td class="num">${p.vendas}</td>
      <td class="num">${fmtBRL(p.min)}</td>
      <td class="num">${fmtBRL(p.media)}</td>
      <td class="num">${fmtBRL(p.max)}</td>
      <td class="num" style="color:${p.cv > 30 ? "#D6336C" : C.text};font-weight:600">${fmtPct(p.cv, 0)}</td>
    </tr>`).join("")}
    </tbody></table>`
    : '<p style="color:var(--text-muted);font-size:13px">Nenhuma variação de preço relevante no recorte atual.</p>';
}

/* ============================================================
   VISTA · Temporalidade
   ============================================================ */
function vistaTemporalidade(df) {
  const regs = estado.registros;
  document.getElementById("heroTempoSub").textContent =
    `Quando o dinheiro entra: sazonalidade, dias e horários de pico · ${dataStrBR(regs[0].dataStr)} a ${dataStrBR(regs[regs.length - 1].dataStr)}`;

  const diaria = serieDiaria(df);
  const mediaDia = diaria.reduce((s, d) => s + d[1], 0) / diaria.length;
  const melhor = [...diaria].sort((a, b) => b[1] - a[1])[0];
  const diaTop = ordenar(somaPor(df, (r) => r.diaSemanaPt))[0][0];
  const horaTop = ordenar(somaPor(df, (r) => r.hora))[0][0];

  document.getElementById("kpisTempo").innerHTML = kpisHTML([
    { rotulo: "Média por dia de venda", valor: fmtBRL(mediaDia), cor: C.primary },
    { rotulo: "Melhor dia registrado", valor: dataStrBR(melhor[0]), delta: fmtBRL(melhor[1]), dir: "up", cor: C.secondary },
    { rotulo: "Dia da semana mais forte", valor: diaTop, cor: C.accent },
    { rotulo: "Horário de pico", valor: `${horaTop}h – ${horaTop + 1}h`, cor: C.teal },
  ]);

  // Mensal com variação
  const mensal = serieMensal(df);
  grafico("gMensalTempo", {
    ...opcoesBase(),
    tooltip: {
      ...opcoesBase().tooltip,
      formatter: (ps) => {
        const i = ps[0].dataIndex;
        const varMM = i > 0 && mensal[i - 1][1] > 0 ? ((mensal[i][1] - mensal[i - 1][1]) / mensal[i - 1][1]) * 100 : null;
        return `<b>${mesKeyLabel(mensal[i][0])}</b><br>Faturamento: ${fmtBRL(mensal[i][1])}` +
          (varMM != null ? `<br>Variação: ${varMM >= 0 ? "+" : ""}${fmtPct(varMM)}` : "");
      },
    },
    xAxis: eixoCat(mensal.map((m) => mesKeyLabel(m[0]))),
    yAxis: eixoValor(),
    series: [{
      type: "line", data: mensal.map((m) => Math.round(m[1])), smooth: true, symbolSize: 9,
      lineStyle: { color: C.primary, width: 3 }, itemStyle: { color: C.primary },
      label: { show: true, position: "top", formatter: (p) => fmtCompact(p.value), fontSize: 10.5, color: C.text, fontWeight: 600 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: "rgba(108,59,217,.28)" }, { offset: 1, color: "rgba(108,59,217,.02)" }]),
      },
    }],
  });

  // Heatmap dia × hora
  const heat = somaPor(df, (r) => r.diaSemanaPt + "|" + r.hora);
  const horas = [...new Set(df.map((r) => r.hora))].sort((a, b) => a - b);
  const diasPresentes = DIAS_PT.filter((d) => df.some((r) => r.diaSemanaPt === d));
  const dadosHeat = [];
  let maxHeat = 0;
  diasPresentes.forEach((dia, yi) => horas.forEach((h, xi) => {
    const v = heat.get(dia + "|" + h) || 0;
    maxHeat = Math.max(maxHeat, v);
    if (v > 0) dadosHeat.push([xi, yi, Math.round(v)]);
  }));
  grafico("gHeatmap", {
    textStyle: FONTE,
    tooltip: {
      backgroundColor: "#fff", borderColor: C.grade, textStyle: { color: C.text, fontSize: 12 },
      formatter: (p) => `<b>${diasPresentes[p.value[1]]}</b> · ${horas[p.value[0]]}h<br>Faturamento: ${fmtBRL(p.value[2])}`,
    },
    grid: { left: 8, right: 90, top: 10, bottom: 8, containLabel: true },
    xAxis: eixoCat(horas.map((h) => h + "h")),
    yAxis: eixoCat(diasPresentes, { inverse: true }),
    visualMap: {
      min: 0, max: maxHeat, orient: "vertical", right: 0, top: "center",
      textStyle: { color: C.muted, fontSize: 10 },
      formatter: (v) => fmtCompact(v),
      inRange: { color: ["#F3F1FA", "#9D4EDD", C.secondary] },
    },
    series: [{ type: "heatmap", data: dadosHeat, itemStyle: { borderRadius: 3, borderColor: "#fff", borderWidth: 2 } }],
  });

  // Período do dia
  const periodos = ["Manha", "Tarde", "Noite"];
  const porPeriodo = somaPor(df, (r) => r.periodo);
  const rotuloPeriodo = { Manha: "Manhã", Tarde: "Tarde", Noite: "Noite" };
  grafico("gPeriodo", {
    textStyle: FONTE,
    tooltip: { trigger: "item", valueFormatter: (v) => fmtBRL(v),
      backgroundColor: "#fff", borderColor: C.grade, textStyle: { color: C.text, fontSize: 12 } },
    legend: { bottom: 0, textStyle: { color: C.muted, fontSize: 11 } },
    color: [C.accent, C.primary, C.escuro],
    series: [{
      type: "pie", radius: ["46%", "70%"], center: ["50%", "44%"],
      itemStyle: { borderRadius: 5, borderColor: "#fff", borderWidth: 2 },
      label: { show: true, formatter: (p) => p.percent.toFixed(0) + "%", fontSize: 11, color: C.text },
      data: periodos.filter((p) => porPeriodo.has(p)).map((p) => ({ name: rotuloPeriodo[p], value: Math.round(porPeriodo.get(p)) })),
    }],
  });

  // Semanal (chave = segunda-feira da semana)
  const porSemana = somaPor(df, (r) => {
    const d = new Date(r.data);
    d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
    return d.toISOString().slice(0, 10);
  });
  const semanas = [...porSemana.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  const mediaSem = semanas.reduce((s, w) => s + w[1], 0) / semanas.length;
  grafico("gSemanal", {
    ...opcoesBase(),
    tooltip: { ...opcoesBase().tooltip,
      formatter: (ps) => `Semana de <b>${dataStrBR(semanas[ps[0].dataIndex][0])}</b><br>Faturamento: ${fmtBRL(ps[0].value)}` },
    xAxis: eixoCat(semanas.map((w) => w[0].slice(8, 10) + "/" + w[0].slice(5, 7)), { axisLabel: { color: C.muted, fontSize: 10, interval: 1 } }),
    yAxis: eixoValor(),
    series: [{
      type: "bar", data: semanas.map((w) => Math.round(w[1])), barMaxWidth: 22,
      itemStyle: { color: C.teal, opacity: 0.85, borderRadius: [3, 3, 0, 0] },
      markLine: { silent: true, symbol: "none", lineStyle: { color: C.secondary, type: "dashed", width: 2 },
        label: { formatter: "média", color: C.secondary, fontSize: 10 }, data: [{ yAxis: Math.round(mediaSem) }] },
    }],
  });

  // Top dias
  const topDias = [...diaria].sort((a, b) => b[1] - a[1]).slice(0, 10);
  document.getElementById("tTopDias").innerHTML = `
    <table><thead><tr><th>#</th><th>Data</th><th>Dia da semana</th><th class="num">Faturamento</th></tr></thead><tbody>
    ${topDias.map(([ds, v], i) => {
      const d = new Date(ds + "T12:00:00");
      return `<tr><td>${i + 1}º</td><td><b>${dataStrBR(ds)}</b></td><td>${DIAS_PT[(d.getDay() + 6) % 7]}</td><td class="num">${fmtBRL(v)}</td></tr>`;
    }).join("")}
    </tbody></table>`;
}

/* ============================================================
   VISTA · Pagamentos
   ============================================================ */
function vistaPagamentos(df) {
  const total = totalFat(df);
  const regs = estado.registros;
  document.getElementById("heroPagSub").textContent =
    `Como o cliente paga: mix de recebimento, ticket e evolução · ${dataStrBR(regs[0].dataStr)} a ${dataStrBR(regs[regs.length - 1].dataStr)}`;

  const porPag = agrupar(df, (r) => r.pagamento);
  const pags = [...porPag.entries()].map(([forma, itens]) => {
    const fat = itens.reduce((s, r) => s + r.subtotal, 0);
    const vendas = new Set(itens.map((r) => r.venda)).size;
    return { forma, fat, vendas, ticket: vendas ? fat / vendas : 0, part: (fat / total) * 100 };
  }).sort((a, b) => b.fat - a.fat);

  const lider = pags[0];
  const maiorTicket = [...pags].sort((a, b) => b.ticket - a.ticket)[0];
  const CORES_PAG = { "Cartão": C.primary, "Pix": C.teal, "Dinheiro": C.accent };
  const corPag = (f) => CORES_PAG[f] || C.secondary;

  document.getElementById("kpisPag").innerHTML = kpisHTML([
    { rotulo: "Forma líder", valor: lider.forma, delta: fmtPct(lider.part) + " do faturamento", dir: "up", cor: C.primary },
    { rotulo: "Maior ticket médio", valor: maiorTicket.forma, delta: fmtBRL(maiorTicket.ticket), dir: "up", cor: C.accent },
    { rotulo: "Formas ativas", valor: pags.length, cor: C.teal },
    { rotulo: "Vendas no recorte", valor: fmtInt(pags.reduce((s, p) => s + p.vendas, 0)), cor: C.secondary },
  ]);

  // Mix (donut)
  grafico("gMixPag", {
    textStyle: FONTE,
    tooltip: { trigger: "item",
      backgroundColor: "#fff", borderColor: C.grade, textStyle: { color: C.text, fontSize: 12 },
      formatter: (p) => `<b>${p.name}</b><br>Faturamento: ${fmtBRL(p.value)}<br>Participação: ${p.percent.toFixed(1)}%` },
    legend: { bottom: 0, textStyle: { color: C.muted, fontSize: 11 } },
    series: [{
      type: "pie", radius: ["50%", "74%"], center: ["50%", "44%"],
      itemStyle: { borderRadius: 5, borderColor: "#fff", borderWidth: 2 },
      label: { show: true, formatter: (p) => p.percent.toFixed(0) + "%", fontSize: 12, color: C.text, fontWeight: 600 },
      data: pags.map((p) => ({ name: p.forma, value: Math.round(p.fat * 100) / 100, itemStyle: { color: corPag(p.forma) } })),
    }],
  });

  // Ticket por forma
  const pagsTicket = [...pags].sort((a, b) => a.ticket - b.ticket);
  grafico("gTicketPag", {
    ...opcoesBase(),
    tooltip: { ...opcoesBase().tooltip, valueFormatter: (v) => fmtBRL(v) },
    grid: { left: 8, right: 70, top: 10, bottom: 8, containLabel: true },
    xAxis: eixoValor(),
    yAxis: eixoCat(pagsTicket.map((p) => p.forma), { axisLabel: { color: C.text, fontSize: 12 } }),
    series: [{
      type: "bar", data: pagsTicket.map((p) => ({ value: Math.round(p.ticket * 100) / 100, itemStyle: { color: corPag(p.forma), borderRadius: [0, 6, 6, 0] } })),
      barMaxWidth: 34,
      label: { show: true, position: "right", formatter: (p) => fmtBRL(p.value), fontSize: 11.5, color: C.text, fontWeight: 600 },
    }],
  });

  // Evolução do mix (100% empilhado)
  const meses = serieMensal(df).map((m) => m[0]);
  const porMesPag = somaPor(df, (r) => r.mesKey + "|" + r.pagamento);
  const totalMes = Object.fromEntries(serieMensal(df));
  grafico("gEvolucaoPag", {
    ...opcoesBase(),
    tooltip: {
      ...opcoesBase().tooltip,
      formatter: (ps) => `<b>${ps[0].axisValue}</b><br>` +
        ps.map((p) => `${p.marker} ${p.seriesName}: ${p.value.toFixed(1)}%`).join("<br>"),
    },
    legend: { top: 0, textStyle: { color: C.muted, fontSize: 11 } },
    xAxis: eixoCat(meses.map(mesKeyLabel)),
    yAxis: { type: "value", max: 100, axisLabel: { color: C.muted, fontSize: 11, formatter: "{value}%" }, splitLine: { lineStyle: { color: C.grade } } },
    series: pags.map((p) => ({
      name: p.forma, type: "line", stack: "mix", smooth: true, symbol: "none",
      lineStyle: { width: 0 },
      areaStyle: { color: corPag(p.forma), opacity: 0.88 },
      data: meses.map((m) => {
        const v = porMesPag.get(m + "|" + p.forma) || 0;
        return totalMes[m] > 0 ? Math.round((v / totalMes[m]) * 1000) / 10 : 0;
      }),
    })),
  });

  // Insights
  const pixPct = (pags.find((p) => p.forma === "Pix") || { part: 0 }).part;
  const dinPct = (pags.find((p) => p.forma === "Dinheiro") || { part: 0 }).part;
  document.getElementById("insightsPag").innerHTML = [
    { titulo: "💳 Custo de recebimento",
      texto: `<b>${lider.forma}</b> concentra ${fmtPct(lider.part)} do faturamento (${fmtBRL(lider.fat)}). ` +
        "Se for cartão, vale negociar a taxa da maquininha — cada 0,5% de redução vai direto para a margem.", tom: "ok" },
    { titulo: "🎟️ Ticket revela comportamento",
      texto: `O maior ticket médio está em <b>${maiorTicket.forma}</b> (${fmtBRL(maiorTicket.ticket)}) — compras maiores tendem a usar esse meio. ` +
        "Use parcelamento como alavanca em itens de maior valor.", tom: "ok" },
    { titulo: "⚡ Pix como aliado do caixa",
      texto: `O Pix responde por ${fmtPct(pixPct)} das vendas: recebimento instantâneo e sem taxas. ` +
        "Incentivar o Pix com pequenos benefícios melhora o fluxo de caixa.", tom: "ok" },
    { titulo: "💵 Gestão do dinheiro físico",
      texto: `Dinheiro em espécie representa ${fmtPct(dinPct)} do faturamento. ` +
        "Mantenha rotina de sangria e conferência de caixa para reduzir risco operacional.", tom: "warn" },
  ].map(insightHTML).join("");
}

/* ============================================================
   VISTA · Previsão (usa a base completa, sem filtros)
   ============================================================ */
function vistaPrevisao() {
  if (!estado.prevCache) estado.prevCache = calcularPrevisao(estado.registros, 30);
  const prev = estado.prevCache;
  const regs = estado.registros;
  document.getElementById("heroPrevSub").textContent =
    `Projeção dos próximos 30 dias de venda · Histórico: ${dataStrBR(regs[0].dataStr)} a ${dataStrBR(regs[regs.length - 1].dataStr)}`;

  if (!prev) {
    document.getElementById("kpisPrev").innerHTML =
      '<div class="kpi" style="grid-column:1/-1">⚠️ Histórico insuficiente para validar o modelo (mínimo ~2 meses de vendas).</div>';
    return;
  }
  const m = prev.metricas;

  document.getElementById("kpisPrev").innerHTML = kpisHTML([
    { rotulo: "Projeção · próx. 30 dias de venda", valor: fmtBRL(m.totalPrevisto), cor: C.primary },
    { rotulo: "Erro médio diário (MAE)", valor: fmtBRL(m.mae), delta: `validado em ${m.holdoutDias} dias fora do treino`, cor: C.accent },
    { rotulo: "Erro relativo (WMAPE)", valor: fmtPct(m.wmape), delta: "quanto menor, melhor", cor: C.teal },
    { rotulo: "Cobertura do intervalo 95%", valor: fmtPct(m.cobertura, 0), delta: "dias reais dentro da faixa prevista", cor: C.secondary },
  ]);

  // Gráfico principal: real + validação + futuro com banda
  const datas = [...prev.diaria.map((d) => d.dataStr), ...prev.futuro.map((f) => f.dataStr)];
  const nHist = prev.diaria.length;
  const nVal = prev.validacao.length;
  const serieReal = datas.map((_, i) => (i < nHist ? Math.round(prev.diaria[i].valor) : null));
  const serieVal = datas.map((_, i) => {
    const j = i - (nHist - nVal);
    return j >= 0 && j < nVal ? Math.round(prev.validacao[j].previsto) : null;
  });
  const serieFut = datas.map((_, i) => (i >= nHist ? Math.round(prev.futuro[i - nHist].previsto) : null));
  // conecta a projeção ao último ponto real
  serieFut[nHist - 1] = Math.round(prev.diaria[nHist - 1].valor);
  const bandaInf = datas.map((_, i) => (i >= nHist ? Math.round(prev.futuro[i - nHist].limInf) : null));
  const bandaAmp = datas.map((_, i) => (i >= nHist ? Math.round(prev.futuro[i - nHist].limSup - prev.futuro[i - nHist].limInf) : null));

  grafico("gPrevisao", {
    ...opcoesBase(),
    tooltip: {
      ...opcoesBase().tooltip, axisPointer: { type: "line" },
      formatter: (ps) => {
        let html = `<b>${dataStrBR(ps[0].axisValue)}</b>`;
        for (const p of ps) {
          if (p.value == null || p.seriesName === "_banda_base") continue;
          if (p.seriesName === "Intervalo 95%") continue;
          html += `<br>${p.marker} ${p.seriesName}: ${fmtBRL(p.value)}`;
        }
        const i = ps[0].dataIndex - nHist;
        if (i >= 0) html += `<br><span style="color:${C.muted}">Faixa: ${fmtBRL(prev.futuro[i].limInf)} – ${fmtBRL(prev.futuro[i].limSup)}</span>`;
        return html;
      },
    },
    legend: { top: 0, data: ["Real", "Previsão (validação)", "Projeção"], textStyle: { color: C.muted, fontSize: 11 } },
    dataZoom: [{ type: "inside" }, { type: "slider", height: 18, bottom: 4, borderColor: C.grade }],
    grid: { left: 8, right: 16, top: 30, bottom: 50, containLabel: true },
    xAxis: eixoCat(datas, { axisLabel: { color: C.muted, fontSize: 10, formatter: (v) => v.slice(8, 10) + "/" + v.slice(5, 7) } }),
    yAxis: eixoValor(),
    series: [
      { name: "_banda_base", type: "line", data: bandaInf, stack: "banda", symbol: "none", lineStyle: { opacity: 0 }, silent: true },
      { name: "Intervalo 95%", type: "line", data: bandaAmp, stack: "banda", symbol: "none",
        lineStyle: { opacity: 0 }, areaStyle: { color: C.secondary, opacity: 0.14 }, silent: true },
      { name: "Real", type: "line", data: serieReal, symbol: "none", lineStyle: { color: C.primary, width: 1.8 } },
      { name: "Previsão (validação)", type: "line", data: serieVal, symbol: "none",
        lineStyle: { color: C.secondary, width: 2, type: "dashed" } },
      { name: "Projeção", type: "line", data: serieFut, symbolSize: 5,
        lineStyle: { color: C.secondary, width: 2.5 }, itemStyle: { color: C.secondary },
        markLine: { silent: true, symbol: "none", lineStyle: { color: "#A8A4BC", type: "dashed" },
          label: { formatter: "hoje", color: C.muted, fontSize: 10 },
          data: [{ xAxis: prev.diaria[nHist - 1].dataStr }] } },
    ],
  });

  document.getElementById("insightPrev").innerHTML = insightHTML({
    titulo: "🧪 Como interpretar a confiabilidade",
    texto: `O modelo foi avaliado em <b>${m.holdoutDias} dias que ele nunca viu</b>. Nesses dias, errou em média ` +
      `${fmtBRL(m.mae)} por dia (${fmtPct(m.wmape)} do faturamento). A faixa rosa indica onde o faturamento real deve ficar ` +
      `em 95% dos casos — na validação, ${fmtPct(m.cobertura, 0)} dos dias ficaram dentro dela.`,
    tom: "ok",
  });

  // Projeção semanal
  const porSem = new Map();
  for (const f of prev.futuro) {
    const d = new Date(f.dataStr + "T12:00:00");
    d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
    const k = d.toISOString().slice(0, 10);
    if (!porSem.has(k)) porSem.set(k, { prev: 0, inf: 0, sup: 0 });
    const w = porSem.get(k);
    w.prev += f.previsto; w.inf += f.limInf; w.sup += f.limSup;
  }
  const sems = [...porSem.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  grafico("gPrevSemana", {
    ...opcoesBase(),
    tooltip: {
      ...opcoesBase().tooltip,
      formatter: (ps) => {
        const w = sems[ps[0].dataIndex][1];
        return `Semana de <b>${dataStrBR(sems[ps[0].dataIndex][0])}</b><br>Previsto: ${fmtBRL(w.prev)}` +
          `<br><span style="color:${C.muted}">Conservador: ${fmtBRL(w.inf)} · Otimista: ${fmtBRL(w.sup)}</span>`;
      },
    },
    xAxis: eixoCat(sems.map((s) => dataStrBR(s[0]).slice(0, 5))),
    yAxis: eixoValor(),
    series: [
      { type: "bar", data: sems.map((s) => Math.round(s[1].prev)), barMaxWidth: 44,
        itemStyle: { color: C.primary, borderRadius: [6, 6, 0, 0] },
        label: { show: true, position: "top", formatter: (p) => fmtCompact(p.value), fontSize: 10.5, color: C.text, fontWeight: 600 } },
      { type: "custom", silent: true,
        renderItem: (params, api) => {
          const x = api.coord([api.value(0), 0])[0];
          const yInf = api.coord([0, api.value(1)])[1];
          const ySup = api.coord([0, api.value(2)])[1];
          const estilo = { stroke: C.secondary, lineWidth: 2 };
          return { type: "group", children: [
            { type: "line", shape: { x1: x, y1: yInf, x2: x, y2: ySup }, style: estilo },
            { type: "line", shape: { x1: x - 6, y1: yInf, x2: x + 6, y2: yInf }, style: estilo },
            { type: "line", shape: { x1: x - 6, y1: ySup, x2: x + 6, y2: ySup }, style: estilo },
          ] };
        },
        data: sems.map((s, i) => [i, Math.round(s[1].inf), Math.round(s[1].sup)]) },
    ],
  });

  // Tabela diária
  document.getElementById("tPrevisao").innerHTML = `
    <table><thead><tr><th>Data</th><th>Dia</th><th class="num">Previsto</th><th class="num">Mínimo</th><th class="num">Máximo</th></tr></thead><tbody>
    ${prev.futuro.map((f) => `<tr>
      <td><b>${dataStrBR(f.dataStr)}</b></td><td>${f.diaSemanaPt}</td>
      <td class="num">${fmtBRL(f.previsto)}</td>
      <td class="num" style="color:${C.muted}">${fmtBRL(f.limInf)}</td>
      <td class="num" style="color:${C.muted}">${fmtBRL(f.limSup)}</td>
    </tr>`).join("")}
    </tbody></table>`;

  document.getElementById("btnBaixarPrev").onclick = () => {
    const linhas = [["Data", "Dia da semana", "Previsto (R$)", "Minimo (R$)", "Maximo (R$)"]];
    prev.futuro.forEach((f) => linhas.push([
      dataStrBR(f.dataStr), f.diaSemanaPt,
      f.previsto.toFixed(2).replace(".", ","), f.limInf.toFixed(2).replace(".", ","), f.limSup.toFixed(2).replace(".", ","),
    ]));
    const csv = "﻿" + linhas.map((l) => l.join(";")).join("\r\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "previsao_faturamento_dkids.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  };
}

/* ============================================================
   Inicialização
   ============================================================ */
async function iniciar() {
  if (!window.echarts) {
    document.getElementById("msgErro").textContent =
      "Não foi possível carregar a biblioteca de gráficos. Conecte-se à internet na primeira abertura (ou adicione lib/echarts.min.js).";
    return;
  }
  try {
    const texto = await carregarCSV();
    document.getElementById("msgCarga").textContent = "Processando dados…";
    estado.registros = construirRegistros(texto);
    if (!estado.registros.length) throw new Error("Nenhum registro válido encontrado no CSV.");
    estado.filtrados = estado.registros;
    popularFiltros();
    document.getElementById("telaCarga").classList.add("oculta");
    aoFiltrar();
  } catch (erro) {
    document.getElementById("msgErro").textContent = "Erro ao carregar os dados: " + erro.message;
    try { localStorage.removeItem(CHAVE_LS); } catch (_) {}
  }
}

iniciar();
