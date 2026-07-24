#!/usr/bin/env bash
# Sincroniza webapp/ + data/vendas_tratadas.csv para docs/, a pasta que o
# GitHub Pages publica (Settings > Pages > main /docs). Rode este script
# sempre que editar webapp/ ou atualizar a base de vendas.
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p docs/css docs/js docs/data
cp webapp/index.html docs/index.html
cp webapp/css/style.css docs/css/style.css
cp webapp/js/engine.js docs/js/engine.js
cp webapp/js/app.js docs/js/app.js
cp data/vendas_tratadas.csv docs/data/vendas_tratadas.csv

echo "docs/ atualizado. Faça commit e push para publicar no GitHub Pages."
