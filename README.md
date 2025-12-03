## Portfólio de Análise Geoespacial com Python
Repositório com projetos de análise e processamento de dados geoespaciais desenvolvidos em Python.

## Sobre os Projetos
Este repositório contém três projetos práticos que demonstram diferentes aspectos da análise geoespacial com Python, utilizando as principais bibliotecas do ecossistema geo-python:

# Análise Espacial de Estabelecimentos Comerciais

Análise de distribuição geográfica e densidade de estabelecimentos usando dados vetoriais.

Funcionalidades:

Criação de dados geoespaciais (pontos e polígonos)
Operações de buffer e análise de proximidade
Cálculo de densidade espacial
Geração de heatmaps
Exportação em múltiplos formatos (SHP, GeoJSON, CSV)



# Análise de Uso do Solo e Cobertura Vegetal
Processamento de dados vetoriais e raster para análise de ocupação territorial.
Tecnologias e técnicas:


Funcionalidades:

Criação de polígonos de uso do solo
Rasterização de dados vetoriais
Cálculo de áreas e perímetros
Análise de percentuais de cobertura
Operações de interseção e buffer



# Análise de Rotas e Acessibilidade Urbana

Análise de rede viária, pontos de interesse e áreas de influência.


Funcionalidades:

Criação de rede viária como grafo
Análise de conectividade e centralidade
Cálculo de áreas de influência (buffers)
Análise de acessibilidade a serviços
Cálculo de distâncias e rotas




Tecnologias e Bibliotecas


Python 3.8+
pandas 1.5+ - Manipulação de dados
geopandas 0.12+ - Dados geoespaciais
GDAL/OGR 3.4+ - Leitura/escrita de formatos geo

Análise e Visualização

numpy - Computação científica
matplotlib - Visualizações
shapely - Geometrias
networkx - Análise de redes




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


