"""

ANÁLISE ESPACIAL DE ESTABELECIMENTOS COMERCIAIS

"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
import numpy as np
from osgeo import gdal, ogr, osr
import warnings
warnings.filterwarnings('ignore')




# GERAÇÃO DE DADOS ESPACIAIS SIMULADOS


np.random.seed(42)

# Criar zona urbana fictícia (polígono)
zona_coords = [(-46.70, -23.60), (-46.60, -23.60), 
               (-46.60, -23.50), (-46.70, -23.50), (-46.70, -23.60)]
zona_urbana = Polygon(zona_coords)

# Gerar pontos de estabelecimentos comerciais
n_estabelecimentos = 200

tipos = ['Restaurante', 'Farmácia', 'Supermercado', 'Posto de Gasolina', 'Banco']
categorias = np.random.choice(tipos, n_estabelecimentos, 
                               p=[0.35, 0.20, 0.20, 0.15, 0.10])

# Coordenadas aleatórias dentro da zona
lons = np.random.uniform(-46.70, -46.60, n_estabelecimentos)
lats = np.random.uniform(-23.60, -23.50, n_estabelecimentos)

# Criar DataFrame
data = {
    'id': range(1, n_estabelecimentos + 1),
    'nome': [f'{cat}_{i}' for i, cat in enumerate(categorias, 1)],
    'tipo': categorias,
    'faturamento_mensal': np.random.randint(10000, 150000, n_estabelecimentos),
    'longitude': lons,
    'latitude': lats
}

df = pd.DataFrame(data)

# Converter para GeoDataFrame
geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
gdf_estabelecimentos = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

print(f"\n {len(gdf_estabelecimentos)} estabelecimentos gerados")


# 2. CRIAR ZONA URBANA COM GEOPANDAS


# Criar GeoDataFrame da zona urbana
gdf_zona = gpd.GeoDataFrame({'id': [1], 'nome': ['Zona Central']}, 
                             geometry=[zona_urbana], crs='EPSG:4326')

# Salvar em Shapefile usando GDAL/OGR
gdf_estabelecimentos.to_file('estabelecimentos.shp', driver='ESRI Shapefile')
gdf_zona.to_file('zona_urbana.shp', driver='ESRI Shapefile')

print(" Shapefiles salvos com sucesso")


# 3. OPERAÇÕES ESPACIAIS COM GEOPANDAS


# Buffer de 500m ao redor de cada estabelecimento (convertendo para métrica)
gdf_projetado = gdf_estabelecimentos.to_crs('EPSG:31983')  # SIRGAS 2000 UTM 23S
gdf_projetado['buffer_500m'] = gdf_projetado.geometry.buffer(500)

# Contar estabelecimentos por tipo
contagem_tipo = gdf_estabelecimentos['tipo'].value_counts()

print("\n" + "="*80)
print("ESTATÍSTICAS POR TIPO DE ESTABELECIMENTO")
print("="*80)
print(contagem_tipo)

# Análise de densidade
print("\n" + "="*80)
print("ANÁLISE DE FATURAMENTO")
print("="*80)
stats_por_tipo = gdf_estabelecimentos.groupby('tipo')['faturamento_mensal'].agg([
    ('Total', 'sum'),
    ('Média', 'mean'),
    ('Máximo', 'max')
])
print(stats_por_tipo.round(2))


# 4. ANÁLISE ESPACIAL COM GDAL/OGR


# Ler shapefile com OGR
driver = ogr.GetDriverByName('ESRI Shapefile')
datasource = driver.Open('estabelecimentos.shp', 0)
layer = datasource.GetLayer()

print(f"\n Shapefile lido com GDAL/OGR: {layer.GetFeatureCount()} features")

# Criar grid de densidade (raster)
x_min, x_max = -46.70, -46.60
y_min, y_max = -23.60, -23.50
cell_size = 0.01  # ~1km

n_cols = int((x_max - x_min) / cell_size)
n_rows = int((y_max - y_min) / cell_size)

# Criar matriz de densidade
densidade = np.zeros((n_rows, n_cols))

for idx, row in gdf_estabelecimentos.iterrows():
    col = int((row['longitude'] - x_min) / cell_size)
    row_idx = int((y_max - row['latitude']) / cell_size)
    if 0 <= row_idx < n_rows and 0 <= col < n_cols:
        densidade[row_idx, col] += 1

print(f" Grid de densidade criado: {n_rows}x{n_cols} células")


# 5. VISUALIZAÇÕES


fig, axes = plt.subplots(2, 2, figsize=(16, 14))
fig.suptitle('Análise Espacial de Estabelecimentos Comerciais', 
             fontsize=16, fontweight='bold')

# Gráfico 1: Mapa de todos os estabelecimentos
ax1 = axes[0, 0]
gdf_zona.boundary.plot(ax=ax1, color='black', linewidth=2)
gdf_estabelecimentos.plot(ax=ax1, column='tipo', categorical=True, 
                          legend=True, markersize=30, alpha=0.6,
                          legend_kwds={'loc': 'upper left', 'fontsize': 8})
ax1.set_title('Distribuição Espacial por Tipo', fontweight='bold', fontsize=12)
ax1.set_xlabel('Longitude')
ax1.set_ylabel('Latitude')
ax1.grid(True, alpha=0.3)

# Gráfico 2: Mapa de calor (densidade)
ax2 = axes[0, 1]
gdf_zona.boundary.plot(ax=ax2, color='black', linewidth=2)
im = ax2.imshow(densidade, extent=[x_min, x_max, y_min, y_max], 
                cmap='YlOrRd', alpha=0.7, aspect='auto')
gdf_estabelecimentos.plot(ax=ax2, markersize=10, color='black', alpha=0.3)
plt.colorbar(im, ax=ax2, label='Densidade de Estabelecimentos')
ax2.set_title('Mapa de Densidade (Heatmap)', fontweight='bold', fontsize=12)
ax2.set_xlabel('Longitude')
ax2.set_ylabel('Latitude')
ax2.grid(True, alpha=0.3)

# Gráfico 3: Faturamento por tipo
ax3 = axes[1, 0]
faturamento_tipo = gdf_estabelecimentos.groupby('tipo')['faturamento_mensal'].sum().sort_values()
colors = plt.cm.Set3(range(len(faturamento_tipo)))
bars = ax3.barh(faturamento_tipo.index, faturamento_tipo.values, color=colors, edgecolor='black')
ax3.set_title('Faturamento Total por Tipo', fontweight='bold', fontsize=12)
ax3.set_xlabel('Faturamento Mensal (R$)')
for i, v in enumerate(faturamento_tipo.values):
    ax3.text(v, i, f' R$ {v/1000:.0f}k', va='center', fontweight='bold')

# Gráfico 4: Distribuição espacial de faturamento
ax4 = axes[1, 1]
gdf_zona.boundary.plot(ax=ax4, color='black', linewidth=2)
scatter = gdf_estabelecimentos.plot(ax=ax4, column='faturamento_mensal', 
                                     cmap='viridis', markersize=50,
                                     legend=True, alpha=0.7,
                                     legend_kwds={'label': 'Faturamento (R$)', 
                                                 'orientation': 'horizontal',
                                                 'shrink': 0.8})
ax4.set_title('Distribuição de Faturamento', fontweight='bold', fontsize=12)
ax4.set_xlabel('Longitude')
ax4.set_ylabel('Latitude')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('analise_espacial_estabelecimentos.png', dpi=300, bbox_inches='tight')
print("\n Visualizações salvas em 'analise_espacial_estabelecimentos.png'")
plt.show()


# 6. ANÁLISE DE PROXIMIDADE


# Calcular estabelecimento mais próximo para cada tipo
print("\n" + "="*80)
print("ANÁLISE DE PROXIMIDADE")
print("="*80)

gdf_metro = gdf_estabelecimentos.to_crs('EPSG:31983')

# Exemplo: distância média entre restaurantes
restaurantes = gdf_metro[gdf_metro['tipo'] == 'Restaurante']
if len(restaurantes) > 1:
    distancias = []
    for idx, rest in restaurantes.iterrows():
        outros = restaurantes[restaurantes.index != idx]
        dist_min = min([rest.geometry.distance(outro.geometry) for _, outro in outros.iterrows()])
        distancias.append(dist_min)
    print(f"Distância média entre Restaurantes: {np.mean(distancias):.2f} metros")


# 7. EXPORTAR RELATÓRIO


# Criar CSV com estatísticas
relatorio = gdf_estabelecimentos[['id', 'nome', 'tipo', 'faturamento_mensal', 
                                   'longitude', 'latitude']].copy()
relatorio.to_csv('relatorio_estabelecimentos.csv', index=False)

print("\n Relatório exportado: 'relatorio_estabelecimentos.csv'")

# Estatísticas finais usando OGR
layer.ResetReading()
total_faturamento = 0
for feature in layer:
    # Acessar atributos com OGR
    faturamento = feature.GetField('faturament')  # Nome truncado em shapefile
    if faturamento:
        total_faturamento += faturamento

print(f"\n Faturamento total calculado com OGR: R$ {total_faturamento:,.2f}")

datasource = None  # Fechar datasource

print("\n" + "="*80)
print("INSIGHTS PRINCIPAIS")
print("="*80)
tipo_dominante = contagem_tipo.index[0]
zona_maior_densidade = f"Centro da área ({densidade.max():.0f} estabelecimentos/km²)"
print(f" Tipo mais comum: {tipo_dominante} ({contagem_tipo[tipo_dominante]} unidades)")
print(f" Área de maior densidade: {zona_maior_densidade}")
print(f" Faturamento médio: R$ {gdf_estabelecimentos['faturamento_mensal'].mean():,.2f}")

print("\n Análise espacial concluída com sucesso!")