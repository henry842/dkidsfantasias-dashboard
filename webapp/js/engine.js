/* ============================================================
   DKidsFantasias BI · engine.js
   Camada de dados: parse do CSV, enriquecimento, agregações,
   insights e modelo de previsão com validação em holdout.
   ============================================================ */

"use strict";

/* ----------------------- Formatação pt-BR ----------------------- */
const _fmtBRL = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const _fmtBRL0 = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const _fmtInt = new Intl.NumberFormat("pt-BR");

const fmtBRL = (v) => _fmtBRL.format(v || 0);
const fmtBRL0 = (v) => _fmtBRL0.format(v || 0);
const fmtInt = (v) => _fmtInt.format(Math.round(v || 0));
const fmtPct = (v, d = 1) => (v || 0).toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d }) + "%";
const fmtCompact = (v) => {
  if (Math.abs(v) >= 1e6) return "R$ " + (v / 1e6).toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " mi";
  if (Math.abs(v) >= 1e3) return "R$ " + (v / 1e3).toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " mil";
  return fmtBRL0(v);
};

const DIAS_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];
const MESES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

/* ----------------------- Parser CSV ----------------------- */
function parseCSV(text) {
  const rows = [];
  let row = [], field = "", inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else inQuotes = false;
      } else field += c;
    } else if (c === '"') inQuotes = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(field); field = "";
      if (row.length > 1 || row[0] !== "") rows.push(row);
      row = [];
    } else field += c;
  }
  if (field !== "" || row.length) { row.push(field); rows.push(row); }
  return rows;
}

/* ----------------------- Inferência de categoria ----------------------- */
const REGRAS_CATEGORIA = [
  [["fant"], "Fantasia"],
  [["conjunto"], "Conjunto"],
  [["vestido"], "Vestido"],
  [["camisa", "camiseta", "blusa", "colete", "body"], "Camisas & Coletes"],
  [["calça", "calcinha", "cueca", "short", "bermuda", "saia", "salopete", "legging", "macacão"], "Vestuário"],
  [["laço", "faixa", "tiara", "meia", "bolsa", "arco", "papel", "presente", "asa", "varinha", "coroa", "máscara", "mascara", "luva", "sapat", "tênis", "tenis"], "Acessórios"],
];

function inferirCategoria(produto) {
  const nome = String(produto || "").toLowerCase();
  for (const [termos, cat] of REGRAS_CATEGORIA) {
    if (termos.some((t) => nome.includes(t))) return cat;
  }
  return "Outros";
}

/* ----------------------- Carga e enriquecimento ----------------------- */
function construirRegistros(csvText) {
  const rows = parseCSV(csvText);
  const header = rows[0].map((h) => h.trim());
  const idx = Object.fromEntries(header.map((h, i) => [h, i]));
  const obrig = ["Codigo_da_Venda", "Produto", "Qtd", "Data", "Subtotal", "Valor_Unit",
    "Forma_de_Pagamento_Simples", "Hora_do_Dia", "Periodo_do_Dia"];
  for (const c of obrig) {
    if (!(c in idx)) throw new Error(`Coluna obrigatória ausente no CSV: ${c}`);
  }

  const registros = [];
  for (let r = 1; r < rows.length; r++) {
    const linha = rows[r];
    if (linha.length < header.length - 2) continue;
    const get = (col) => (idx[col] !== undefined ? linha[idx[col]] : "");

    const dataStr = String(get("Data")).slice(0, 10);
    const data = new Date(dataStr + "T12:00:00");
    if (isNaN(data)) continue;

    const subtotal = parseFloat(get("Subtotal"));
    if (!isFinite(subtotal)) continue;

    // getDay(): 0=Dom ... 6=Sáb  →  0=Seg ... 6=Dom
    const diaSemana = (data.getDay() + 6) % 7;
    const catOriginal = String(get("Categoria") || "").trim();

    registros.push({
      venda: String(get("Codigo_da_Venda")),
      produto: String(get("Produto")).trim(),
      qtd: parseFloat(get("Qtd")) || 0,
      data, dataStr,
      mesKey: dataStr.slice(0, 7),
      mes: data.getMonth() + 1,
      diaSemana,
      diaSemanaPt: DIAS_PT[diaSemana],
      hora: parseInt(get("Hora_do_Dia"), 10),
      periodo: String(get("Periodo_do_Dia")).trim(),
      pagamento: String(get("Forma_de_Pagamento_Simples")).trim() || "Outros",
      valorUnit: parseFloat(get("Valor_Unit")) || 0,
      subtotal,
      categoria: catOriginal || inferirCategoria(get("Produto")),
    });
  }
  registros.sort((a, b) => a.data - b.data);
  return registros;
}

/* ----------------------- Agregações genéricas ----------------------- */
function somaPor(registros, chaveFn, valorFn = (r) => r.subtotal) {
  const mapa = new Map();
  for (const r of registros) {
    const k = chaveFn(r);
    mapa.set(k, (mapa.get(k) || 0) + valorFn(r));
  }
  return mapa;
}

function agrupar(registros, chaveFn) {
  const mapa = new Map();
  for (const r of registros) {
    const k = chaveFn(r);
    if (!mapa.has(k)) mapa.set(k, []);
    mapa.get(k).push(r);
  }
  return mapa;
}

const totalFat = (registros) => registros.reduce((s, r) => s + r.subtotal, 0);

function vendasUnicas(registros) {
  const mapa = new Map();
  for (const r of registros) mapa.set(r.venda, (mapa.get(r.venda) || 0) + r.subtotal);
  return mapa;
}

function serieMensal(registros) {
  const mapa = somaPor(registros, (r) => r.mesKey);
  return [...mapa.entries()].sort((a, b) => a[0].localeCompare(b[0]));
}

function serieDiaria(registros) {
  const mapa = somaPor(registros, (r) => r.dataStr);
  return [...mapa.entries()].sort((a, b) => a[0].localeCompare(b[0]));
}

const mesKeyLabel = (k) => MESES_PT[parseInt(k.slice(5, 7), 10) - 1] + "/" + k.slice(2, 4);
const dataStrBR = (s) => s.slice(8, 10) + "/" + s.slice(5, 7) + "/" + s.slice(0, 4);

/* ----------------------- KPIs ----------------------- */
function kpisGerais(registros) {
  const vendas = vendasUnicas(registros);
  const mensal = serieMensal(registros);
  let variacaoMM = null;
  if (mensal.length >= 2) {
    const ant = mensal[mensal.length - 2][1];
    if (ant > 0) variacaoMM = ((mensal[mensal.length - 1][1] - ant) / ant) * 100;
  }
  const nVendas = vendas.size;
  const fat = totalFat(registros);
  return {
    faturamento: fat,
    nVendas,
    itens: registros.reduce((s, r) => s + r.qtd, 0),
    ticketMedio: nVendas ? fat / nVendas : 0,
    produtosAtivos: new Set(registros.map((r) => r.produto)).size,
    variacaoMM,
  };
}

/* ----------------------- Insights automáticos ----------------------- */
function insightsExecutivos(registros) {
  const out = [];
  const total = totalFat(registros);
  if (!total || !registros.length) return out;

  const ordenado = (mapa) => [...mapa.entries()].sort((a, b) => b[1] - a[1]);

  // Concentração (Pareto)
  const fatProd = ordenado(somaPor(registros, (r) => r.produto));
  let acum = 0, n80 = 0;
  for (const [, v] of fatProd) { acum += v; n80++; if (acum / total >= 0.8) break; }
  const pctProdutos = (n80 / fatProd.length) * 100;
  out.push({
    titulo: "🎯 Concentração de faturamento",
    texto: `Apenas <b>${n80} produtos</b> (${fmtPct(pctProdutos, 0)} do portfólio) geram 80% do faturamento. ` +
      `O líder é <b>${fatProd[0][0]}</b>, com ${fmtBRL(fatProd[0][1])} (${fmtPct((fatProd[0][1] / total) * 100)}).`,
    tom: pctProdutos < 15 ? "warn" : "ok",
  });

  // Ritmo semanal
  const dia = ordenado(somaPor(registros, (r) => r.diaSemanaPt));
  if (dia.length >= 2) {
    out.push({
      titulo: "📅 Ritmo semanal",
      texto: `<b>${dia[0][0]}</b> é o dia mais forte (${fmtPct((dia[0][1] / total) * 100)} do faturamento), ` +
        `seguido de <b>${dia[1][0]}</b>. O dia mais fraco é <b>${dia[dia.length - 1][0]}</b> — bom candidato a promoções de tráfego.`,
      tom: "ok",
    });
  }

  // Janela de ouro
  const hora = ordenado(somaPor(registros, (r) => r.hora));
  if (hora.length >= 3) {
    const top3 = hora.slice(0, 3).map((h) => h[0]).sort((a, b) => a - b);
    const pctPico = (hora.slice(0, 3).reduce((s, h) => s + h[1], 0) / total) * 100;
    out.push({
      titulo: "⏰ Janela de ouro",
      texto: `As faixas de <b>${top3[0]}h, ${top3[1]}h e ${top3[2]}h</b> concentram ${fmtPct(pctPico)} das vendas. ` +
        "Garanta equipe completa e caixa ágil nesses horários.",
      tom: "ok",
    });
  }

  // Pagamentos
  const pag = ordenado(somaPor(registros, (r) => r.pagamento));
  if (pag.length) {
    const pixVal = pag.find((p) => p[0] === "Pix");
    out.push({
      titulo: "💳 Meios de pagamento",
      texto: `<b>${pag[0][0]}</b> lidera com ${fmtPct((pag[0][1] / total) * 100)} do faturamento.` +
        (pixVal ? ` Pix representa ${fmtPct((pixVal[1] / total) * 100)} — recebimento instantâneo e sem taxa de adquirente.` : ""),
      tom: "ok",
    });
  }

  // Tendência
  const mensal = serieMensal(registros);
  if (mensal.length >= 3) {
    const ult3 = mensal.slice(-3);
    const cresce = ult3[2][1] > ult3[0][1];
    const varPct = ult3[0][1] > 0 ? (Math.abs(ult3[2][1] - ult3[0][1]) / ult3[0][1]) * 100 : 0;
    out.push({
      titulo: "📈 Tendência recente",
      texto: `Nos últimos 3 meses o faturamento apresenta <b>${cresce ? "crescimento" : "queda"}</b> de ${fmtPct(varPct)} — ` +
        `de ${fmtBRL(ult3[0][1])} para ${fmtBRL(ult3[2][1])}.`,
      tom: cresce ? "ok" : "warn",
    });
  }

  return out;
}

/* ============================================================
   Previsão de faturamento
   Modelo: sazonalidade semanal (média ponderada dos últimos 4
   mesmos dias-da-semana) × fator de tendência amortecido.
   Validação: holdout com os últimos 28 dias de venda — as
   métricas (MAE/WMAPE/cobertura) vêm só desse período.
   ============================================================ */
const HOLDOUT_DIAS = 28;

function _preverPonto(historico, diaSemanaAlvo) {
  // historico: array de {dataStr, valor, diaSemana} anteriores ao alvo
  const mesmos = [];
  for (let i = historico.length - 1; i >= 0 && mesmos.length < 4; i--) {
    if (historico[i].diaSemana === diaSemanaAlvo) mesmos.push(historico[i].valor);
  }
  if (!mesmos.length) {
    const ult = historico.slice(-7);
    return ult.reduce((s, h) => s + h.valor, 0) / Math.max(ult.length, 1);
  }
  // Pesos decrescentes: mais recente vale mais
  const pesos = [4, 3, 2, 1];
  let soma = 0, pesoTotal = 0;
  mesmos.forEach((v, i) => { soma += v * pesos[i]; pesoTotal += pesos[i]; });
  const sazonal = soma / pesoTotal;

  // Tendência: média 14 recentes vs 14 anteriores, amortecida (raiz) e limitada
  let tendencia = 1;
  if (historico.length >= 28) {
    const vals = historico.map((h) => h.valor);
    const rec = vals.slice(-14).reduce((a, b) => a + b, 0) / 14;
    const ant = vals.slice(-28, -14).reduce((a, b) => a + b, 0) / 14;
    if (ant > 0) tendencia = Math.sqrt(Math.min(Math.max(rec / ant, 0.6), 1.5));
  }
  return Math.max(sazonal * tendencia, 0);
}

function calcularPrevisao(registros, horizonte = 30) {
  const diaria = serieDiaria(registros).map(([dataStr, valor]) => {
    const d = new Date(dataStr + "T12:00:00");
    return { dataStr, valor, diaSemana: (d.getDay() + 6) % 7 };
  });
  if (diaria.length < HOLDOUT_DIAS + 30) return null;

  // ---- validação honesta: prevê cada dia do holdout usando só o passado ----
  const corte = diaria.length - HOLDOUT_DIAS;
  const validacao = [];
  for (let i = corte; i < diaria.length; i++) {
    const prev = _preverPonto(diaria.slice(0, i), diaria[i].diaSemana);
    validacao.push({ dataStr: diaria[i].dataStr, real: diaria[i].valor, previsto: prev });
  }
  const residuos = validacao.map((v) => v.real - v.previsto);
  const mae = residuos.reduce((s, r) => s + Math.abs(r), 0) / residuos.length;
  const somaReal = validacao.reduce((s, v) => s + v.real, 0);
  const wmape = (residuos.reduce((s, r) => s + Math.abs(r), 0) / somaReal) * 100;
  const media = residuos.reduce((s, r) => s + r, 0) / residuos.length;
  const desvio = Math.sqrt(residuos.reduce((s, r) => s + (r - media) ** 2, 0) / (residuos.length - 1));
  const banda = 1.96 * desvio;
  const cobertura = (residuos.filter((r) => Math.abs(r) <= banda).length / residuos.length) * 100;

  // ---- projeção futura: só nos dias da semana em que a loja vende ----
  const diasAtivos = new Set(diaria.map((d) => d.diaSemana));
  const historico = [...diaria];
  const futuro = [];
  let cursor = new Date(diaria[diaria.length - 1].dataStr + "T12:00:00");
  while (futuro.length < horizonte) {
    cursor = new Date(cursor.getTime() + 86400000);
    const ds = (cursor.getDay() + 6) % 7;
    if (!diasAtivos.has(ds)) continue;
    const prev = _preverPonto(historico, ds);
    const dataStr = cursor.toISOString().slice(0, 10);
    futuro.push({
      dataStr,
      diaSemanaPt: DIAS_PT[ds],
      previsto: prev,
      limInf: Math.max(prev - banda, 0),
      limSup: prev + banda,
    });
    historico.push({ dataStr, valor: prev, diaSemana: ds });
  }

  return {
    diaria, validacao, futuro,
    metricas: {
      mae, wmape, cobertura,
      holdoutDias: HOLDOUT_DIAS,
      totalPrevisto: futuro.reduce((s, f) => s + f.previsto, 0),
    },
  };
}
