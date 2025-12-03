"""

ANÁLISE DE ROTAS E ACESSIBILIDADE URBANA

"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString, Polygon
import numpy as np
from osgeo import gdal, ogr, osr
import networkx as nx
import warnings
warnings.filterwarnings('ignore')

print(" Bibliotecas carregadas com sucesso")


# 1. CRIAR REDE VIÁRIA SIMULADA


np.random.seed(789)

# Definir área urbana
x_min, x_max = -46.65, -46.55
y_min, y_max = -23.58, -23.48

# Criar grid de ruas (rede simplificada)
n_linhas_h = 12  # Ruas horizontais
n_linhas_v = 12  # Ruas verticais

ruas = []
rua_id = 1

# Ruas horizontais
for i in range(n_linhas_h):
    y = y_min + (y_max - y_min) * i / (n_linhas_h - 1)
    linha = LineString([(x_min, y), (x_max, y)])
    ruas.append({
        'id': rua_id,
        'tipo': 'Avenida' if i % 3 == 0 else 'Rua',
        'comprimento_km': linha.length * 111,
        'velocidade_media': 50 if i % 3 == 0 else 40,
        'geometry': linha
    })
    rua_id += 1

# Ruas verticais
for j in range(n_linhas_v):
    x = x_min + (x_max - x_min) * j / (n_linhas_v - 1)
    linha = LineString([(x, y_min), (x, y_max)])
    ruas.append({
        'id': rua_id,
        'tipo': 'Avenida' if j % 3 == 0 else 'Rua',
        'comprimento_km': linha.length * 111,
        'velocidade_media': 50 if j % 3 == 0 else 40,
        'geometry': linha
    })
    rua_id += 1

gdf_ruas = gpd.GeoDataFrame(ruas, crs='EPSG:4326')

print(f"\n Rede viária criada: {len(gdf_ruas)} segmentos")


# 2. CRIAR PONTOS DE INTERESSE (POIs)


categorias_poi = ['Hospital', 'Escola', 'Estação de Metrô', 'Shopping', 'Parque']
cores_poi = {
    'Hospital': 'red',
    'Escola': 'blue',
    'Estação de Metrô': 'purple',
    'Shopping': 'orange',
    'Parque': 'green'
}

n_pois = 40
pois = []

for i in range(n_pois):
    categoria = np.random.choice(categorias_poi, p=[0.15, 0.30, 0.20, 0.20, 0.15])
    lon = np.random.uniform(x_min, x_max)
    lat = np.random.uniform(y_min, y_max)
    
    pois.append({
        'id': i + 1,
        'nome': f'{categoria}_{i+1}',
        'categoria': categoria,
        'capacidade': np.random.randint(100, 2000),
        'longitude': lon,
        'latitude': lat,
        'geometry': Point(lon, lat)
    })

gdf_pois = gpd.GeoDataFrame(pois, crs='EPSG:4326')

print(f" {len(gdf_pois)} pontos de interesse criados")


# 3. SALVAR DADOS COM GDAL/OGR


# Salvar ruas
gdf_ruas.to_file('rede_viaria.shp', driver='ESRI Shapefile')
print(" Shapefile 'rede_viaria.shp' salvo")

# Salvar POIs usando OGR
driver = ogr.GetDriverByName('ESRI Shapefile')
ds_pois = driver.CreateDataSource('pontos_interesse.shp')

srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)

layer_pois = ds_pois.CreateLayer('pois', srs, ogr.wkbPoint)

# Adicionar campos
layer_pois.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
layer_pois.CreateField(ogr.FieldDefn('nome', ogr.OFTString))
layer_pois.CreateField(ogr.FieldDefn('categoria', ogr.OFTString))
layer_pois.CreateField(ogr.FieldDefn('capacidade', ogr.OFTInteger))

# Adicionar features
for idx, row in gdf_pois.iterrows():
    feature = ogr.Feature(layer_pois.GetLayerDefn())
    feature.SetField('id', int(row['id']))
    feature.SetField('nome', row['nome'])
    feature.SetField('categoria', row['categoria'])
    feature.SetField('capacidade', int(row['capacidade']))
    
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(row['longitude'], row['latitude'])
    feature.SetGeometry(point)
    
    layer_pois.CreateFeature(feature)
    feature = None

ds_pois = None
print(" Shapefile 'pontos_interesse.shp' salvo com GDAL/OGR")


# 4. ANÁLISE DE ACESSIBILIDADE


print("\n" + "="*80)
print("ANÁLISE DE ACESSIBILIDADE")
print("="*80)

# Converter para sistema métrico
gdf_ruas_m = gdf_ruas.to_crs('EPSG:31983')
gdf_pois_m = gdf_pois.to_crs('EPSG:31983')

# Criar buffers de acessibilidade (raio de 500m)
gdf_pois_m['buffer_500m'] = gdf_pois_m.geometry.buffer(500)

# Contar POIs por categoria
contagem_pois = gdf_pois['categoria'].value_counts()
print("\nPontos de Interesse por Categoria:")
print(contagem_pois)

# Calcular área de cobertura
area_cobertura = {}
for categoria in categorias_poi:
    subset = gdf_pois_m[gdf_pois_m['categoria'] == categoria]
    if len(subset) > 0:
        # União de todos os buffers da categoria
        buffers = subset['buffer_500m'].unary_union
        area_km2 = buffers.area / 1_000_000
        area_cobertura[categoria] = area_km2

print("\nÁrea de Cobertura (raio 500m):")
for cat, area in area_cobertura.items():
    print(f"  {cat:20s}: {area:.2f} km²")


# 5. ANÁLISE DE REDE COM NETWORKX


# Criar grafo de rede viária
G = nx.Graph()

# Adicionar nós (interseções)
intersecoes = set()
for idx, rua in gdf_ruas.iterrows():
    coords = list(rua['geometry'].coords)
    for coord in coords:
        intersecoes.add(coord)

# Adicionar nós ao grafo
for i, intersecao in enumerate(intersecoes):
    G.add_node(i, pos=intersecao)

# Criar dicionário de coordenadas para índices
coord_to_idx = {coord: i for i, coord in enumerate(intersecoes)}

# Adicionar arestas (segmentos de rua)
for idx, rua in gdf_ruas.iterrows():
    coords = list(rua['geometry'].coords)
    for i in range(len(coords) - 1):
        idx1 = coord_to_idx[coords[i]]
        idx2 = coord_to_idx[coords[i+1]]
        
        # Calcular distância
        p1 = Point(coords[i])
        p2 = Point(coords[i+1])
        dist_km = p1.distance(p2) * 111
        
        # Calcular tempo (minutos)
        tempo_min = (dist_km / rua['velocidade_media']) * 60
        
        G.add_edge(idx1, idx2, weight=dist_km, time=tempo_min)

print(f"\n Grafo de rede criado: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")

# Calcular centralidade
centralidade = nx.degree_centrality(G)
no_mais_central = max(centralidade, key=centralidade.get)
print(f" Nó mais central (conectividade): {no_mais_central}")


# 6. ANÁLISE ESPACIAL COM GEOPANDAS


# Calcular densidade de POIs por tipo
print("\n" + "="*80)
print("ESTATÍSTICAS DE INFRAESTRUTURA")
print("="*80)

stats_pois = gdf_pois.groupby('categoria').agg({
    'id': 'count',
    'capacidade': ['sum', 'mean']
})
stats_pois.columns = ['Quantidade', 'Capacidade Total', 'Capacidade Média']
print(stats_pois)

# Encontrar POI mais próximo de cada tipo para um ponto de referência
ponto_referencia = Point(-46.60, -23.53)
gdf_ref = gpd.GeoDataFrame({'geometry': [ponto_referencia]}, crs='EPSG:4326')
gdf_ref_m = gdf_ref.to_crs('EPSG:31983')

print("\n" + "="*80)
print("DISTÂNCIAS DO CENTRO (ponto de referência)")
print("="*80)

for categoria in categorias_poi:
    subset = gdf_pois_m[gdf_pois_m['categoria'] == categoria]
    if len(subset) > 0:
        distancias = subset.geometry.distance(gdf_ref_m.iloc[0].geometry)
        dist_min = distancias.min()
        print(f"{categoria:20s}: {dist_min:.0f} metros")


# 7. PROCESSAMENTO COM GDAL - LER E ANALISAR


# Ler shapefile de ruas com OGR
datasource = ogr.Open('rede_viaria.shp')
layer_ruas = datasource.GetLayer()

# Calcular comprimento total da rede
comprimento_total = 0
for feature in layer_ruas:
    geom = feature.GetGeometryRef()
    comprimento_total += geom.Length() * 111  # Conversão para km

print(f"\n Comprimento total da rede viária (OGR): {comprimento_total:.2f} km")

datasource = None


# 8. VISUALIZAÇÕES


fig = plt.figure(figsize=(18, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

fig.suptitle('Análise de Rotas e Acessibilidade Urbana', 
             fontsize=16, fontweight='bold')

# Gráfico 1: Mapa completo da rede viária e POIs
ax1 = fig.add_subplot(gs[0:2, 0:2])
gdf_ruas.plot(ax=ax1, color='gray', linewidth=1, alpha=0.6)
for categoria in categorias_poi:
    subset = gdf_pois[gdf_pois['categoria'] == categoria]
    subset.plot(ax=ax1, color=cores_poi[categoria], markersize=50, 
                alpha=0.7, label=categoria)
ax1.set_title('Rede Viária e Pontos de Interesse', fontweight='bold', fontsize=13)
ax1.set_xlabel('Longitude')
ax1.set_ylabel('Latitude')
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)

# Gráfico 2: Áreas de influência (buffers)
ax2 = fig.add_subplot(gs[0:2, 2])
gdf_pois_m_plot = gdf_pois_m.to_crs('EPSG:4326')
buffers_plot = gdf_pois_m_plot.copy()
buffers_plot['geometry'] = buffers_plot['buffer_500m']
buffers_plot = buffers_plot.set_geometry('geometry')
buffers_plot = buffers_plot.to_crs('EPSG:4326')

gdf_ruas.plot(ax=ax2, color='lightgray', linewidth=0.5, alpha=0.5)
for categoria in categorias_poi:
    subset = buffers_plot[buffers_plot['categoria'] == categoria]
    subset.plot(ax=ax2, color=cores_poi[categoria], alpha=0.2, edgecolor='none')
    subset_center = gdf_pois[gdf_pois['categoria'] == categoria]
    subset_center.plot(ax=ax2, color=cores_poi[categoria], markersize=20, 
                      edgecolor='black', linewidth=0.5)
ax2.set_title('Áreas de Influência\n(raio 500m)', fontweight='bold', fontsize=12)
ax2.set_xlabel('Longitude')
ax2.set_ylabel('Latitude')
ax2.grid(True, alpha=0.3)

# Gráfico 3: Distribuição de POIs
ax3 = fig.add_subplot(gs[2, 0])
contagem_pois_sorted = contagem_pois.sort_values()
cores_bars = [cores_poi[cat] for cat in contagem_pois_sorted.index]
bars = ax3.barh(contagem_pois_sorted.index, contagem_pois_sorted.values, 
                color=cores_bars, edgecolor='black', linewidth=1.5)
ax3.set_title('Quantidade de POIs por Categoria', fontweight='bold', fontsize=12)
ax3.set_xlabel('Quantidade')
for i, v in enumerate(contagem_pois_sorted.values):
    ax3.text(v, i, f' {v}', va='center', fontweight='bold')

# Gráfico 4: Cobertura por categoria
ax4 = fig.add_subplot(gs[2, 1])
if area_cobertura:
    categorias = list(area_cobertura.keys())
    areas = list(area_cobertura.values())
    cores_cob = [cores_poi[cat] for cat in categorias]
    bars = ax4.bar(range(len(categorias)), areas, color=cores_cob, 
                   edgecolor='black', linewidth=1.5)
    ax4.set_xticks(range(len(categorias)))
    ax4.set_xticklabels(categorias, rotation=45, ha='right')
    ax4.set_title('Área de Cobertura (km²)', fontweight='bold', fontsize=12)
    ax4.set_ylabel('Área (km²)')
    for i, v in enumerate(areas):
        ax4.text(i, v, f'{v:.1f}', ha='center', va='bottom', fontweight='bold')

# Gráfico 5: Capacidade total
ax5 = fig.add_subplot(gs[2, 2])
capacidade_cat = gdf_pois.groupby('categoria')['capacidade'].sum().sort_values()
cores_cap = [cores_poi[cat] for cat in capacidade_cat.index]
ax5.barh(capacidade_cat.index, capacidade_cat.values, color=cores_cap, 
         edgecolor='black', linewidth=1.5)
ax5.set_title('Capacidade Total por Categoria', fontweight='bold', fontsize=12)
ax5.set_xlabel('Capacidade')
for i, v in enumerate(capacidade_cat.values):
    ax5.text(v, i, f' {v}', va='center', fontweight='bold')

plt.savefig('analise_rotas_acessibilidade.png', dpi=300, bbox_inches='tight')
print("\n Visualizações salvas em 'analise_rotas_acessibilidade.png'")
plt.show()


# 9. EXPORTAR RELATÓRIOS


# Relatório de POIs
relatorio_pois = gdf_pois[['id', 'nome', 'categoria', 'capacidade', 
                           'longitude', 'latitude']].copy()
relatorio_pois.to_csv('relatorio_pois.csv', index=False)
print("\n Relatório de POIs: 'relatorio_pois.csv'")

# Relatório de rede viária
relatorio_vias = gdf_ruas[['id', 'tipo', 'comprimento_km', 'velocidade_media']].copy()
relatorio_vias.to_csv('relatorio_rede_viaria.csv', index=False)
print(" Relatório de vias: 'relatorio_rede_viaria.csv'")

# Resumo de acessibilidade
resumo_acess = pd.DataFrame({
    'Categoria': list(area_cobertura.keys()),
    'Quantidade': [contagem_pois[cat] for cat in area_cobertura.keys()],
    'Area_Cobertura_km2': list(area_cobertura.values()),
    'Capacidade_Total': [gdf_pois[gdf_pois['categoria']==cat]['capacidade'].sum() 
                         for cat in area_cobertura.keys()]
})
resumo_acess.to_csv('resumo_acessibilidade.csv', index=False)
print(" Resumo de acessibilidade: 'resumo_acessibilidade.csv'")

print("\n" + "="*80)
print("INSIGHTS PRINCIPAIS")
print("="*80)
categoria_mais_comum = contagem_pois.index[0]
maior_cobertura = max(area_cobertura, key=area_cobertura.get) if area_cobertura else "N/A"
print(f" Categoria mais frequente: {categoria_mais_comum} ({contagem_pois[categoria_mais_comum]} unidades)")
print(f" Maior área de cobertura: {maior_cobertura}")
print(f" Rede viária: {len(gdf_ruas)} segmentos, {comprimento_total:.2f} km totais")
print(f" Densidade média: {len(gdf_pois)/((x_max-x_min)*(y_max-y_min)*111*111):.1f} POIs/km²")

print("\n Análise de rotas e acessibilidade concluída com sucesso!")