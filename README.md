Portfólio de Análise Geoespacial com Python
Repositório com projetos de análise e processamento de dados geoespaciais desenvolvidos em Python, demonstrando habilidades em geoprocessamento, análise espacial e visualização de dados geográficos.

🎯 Sobre os Projetos
Este repositório contém três projetos práticos que demonstram diferentes aspectos da análise geoespacial com Python, utilizando as principais bibliotecas do ecossistema geo-python:
1️⃣ Análise Espacial de Estabelecimentos Comerciais
Análise de distribuição geográfica e densidade de estabelecimentos usando dados vetoriais.
Tecnologias e técnicas:

pandas: Manipulação de dados tabulares
geopandas: Operações espaciais em geometrias vetoriais
GDAL/OGR: Leitura e escrita de formatos geoespaciais (Shapefile, GeoJSON)
matplotlib: Visualizações cartográficas

Funcionalidades:

Criação de dados geoespaciais (pontos e polígonos)
Operações de buffer e análise de proximidade
Cálculo de densidade espacial
Geração de heatmaps
Exportação em múltiplos formatos (SHP, GeoJSON, CSV)

Principais insights:

Identificação de clusters de estabelecimentos
Análise de distribuição por tipo
Mapeamento de áreas de maior concentração comercial


2️⃣ Análise de Uso do Solo e Cobertura Vegetal
Processamento de dados vetoriais e raster para análise de ocupação territorial.
Tecnologias e técnicas:

geopandas: Manipulação de polígonos e análise de área
GDAL: Criação e processamento de dados raster
numpy: Operações matriciais para rasterização
shapely: Geometrias e operações topológicas

Funcionalidades:

Criação de polígonos de uso do solo
Rasterização de dados vetoriais
Cálculo de áreas e perímetros
Análise de percentuais de cobertura
Operações de interseção e buffer

Principais insights:

Distribuição percentual de uso do solo
Identificação de áreas de preservação
Análise de fragmentação territorial


3️⃣ Análise de Rotas e Acessibilidade Urbana
Análise de rede viária, pontos de interesse e áreas de influência.
Tecnologias e técnicas:

geopandas: Análise de linhas e pontos
GDAL/OGR: Processamento de shapefiles
networkx: Análise de redes e grafos
matplotlib: Cartografia e visualização avançada

Funcionalidades:

Criação de rede viária como grafo
Análise de conectividade e centralidade
Cálculo de áreas de influência (buffers)
Análise de acessibilidade a serviços
Cálculo de distâncias e rotas

Principais insights:

Mapeamento de áreas de cobertura de serviços
Identificação de pontos críticos de acesso
Análise de densidade de infraestrutura


🛠️ Tecnologias e Bibliotecas
Core Libraries

Python 3.8+
pandas 1.5+ - Manipulação de dados
geopandas 0.12+ - Dados geoespaciais
GDAL/OGR 3.4+ - Leitura/escrita de formatos geo

Análise e Visualização

numpy - Computação científica
matplotlib - Visualizações
shapely - Geometrias
networkx - Análise de redes

Sistemas de Coordenadas

EPSG:4326 - WGS 84 (lat/lon)
EPSG:31983 - SIRGAS 2000 UTM Zone 23S (métrica)


📁 Estrutura do Repositório
analise-geoespacial-python/
│
├── README.md
│
├── 01_estabelecimentos_comerciais/
│   ├── analise_estabelecimentos.py
│   ├── estabelecimentos.shp (+ .dbf, .shx, .prj)
│   ├── zona_urbana.shp (+ .dbf, .shx, .prj)
│   ├── relatorio_estabelecimentos.csv
│   ├── analise_espacial_estabelecimentos.png
│   └── README.md
│
├── 02_uso_do_solo/
│   ├── analise_uso_solo.py
│   ├── uso_do_solo.shp (+ .dbf, .shx, .prj)
│   ├── uso_do_solo.geojson
│   ├── uso_solo_raster.tif
│   ├── relatorio_uso_solo.csv
│   ├── resumo_uso_solo.csv
│   ├── analise_uso_solo.png
│   └── README.md
│
├── 03_rotas_acessibilidade/
│   ├── analise_rotas.py
│   ├── rede_viaria.shp (+ .dbf, .shx, .prj)
│   ├── pontos_interesse.shp (+ .dbf, .shx, .prj)
│   ├── relatorio_pois.csv
│   ├── relatorio_rede_viaria.csv
│   ├── resumo_acessibilidade.csv
│   ├── analise_rotas_acessibilidade.png
│   └── README.md
│
└── requirements.txt

🚀 Como Executar
Pré-requisitos
bash# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt
requirements.txt
pandas>=1.5.0
geopandas>=0.12.0
matplotlib>=3.5.0
numpy>=1.23.0
shapely>=2.0.0
GDAL>=3.4.0
networkx>=2.8.0
Executar os projetos
bash# Projeto 1
cd 01_estabelecimentos_comerciais
python analise_estabelecimentos.py

# Projeto 2
cd 02_uso_do_solo
python analise_uso_solo.py

# Projeto 3
cd 03_rotas_acessibilidade
python analise_rotas.py
