"""

ANÁLISE DE USO DO SOLO E COBERTURA VEGETAL

"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon
import numpy as np
from osgeo import gdal, ogr, osr
import warnings
warnings.filterwarnings('ignore')

print(" Bibliotecas carregadas com sucesso")


# 1. CRIAR POLÍGONOS DE USO DO SOLO


np.random.seed(123)

# Definir tipos de uso do solo
usos = ['Floresta', 'Agricultura', 'Área Urbana', 'Pastagem', 'Corpo d\'água']
cores_uso = {
    'Floresta': '#228B22',
    'Agricultura': '#FFD700',
    'Área Urbana': '#DC143C',
    'Pastagem': '#90EE90',
    'Corpo d\'água': '#1E90FF'
}

# Criar polígonos simulados
def criar_poligono_aleatorio(x_min, x_max, y_min, y_max, n_pontos=6):
    """Cria um polígono aleatório dentro dos limites"""
    x_centro = np.random.uniform(x_min, x_max)
    y_centro = np.random.uniform(y_min, y_max)
    raio = np.random.uniform(0.01, 0.03)
    
    angulos = np.sort(np.random.uniform(0, 2*np.pi, n_pontos))
    coords = [(x_centro + raio * np.cos(a), y_centro + raio * np.sin(a)) 
              for a in angulos]
    coords.append(coords[0])  # Fechar polígono
    
    return Polygon(coords)

# Limites da área de estudo
x_min, x_max = -47.0, -46.5
y_min, y_max = -23.8, -23.3

# Gerar polígonos
n_poligonos = 50
poligonos_data = []

for i in range(n_poligonos):
    poly = criar_poligono_aleatorio(x_min, x_max, y_min, y_max)
    uso = np.random.choice(usos, p=[0.30, 0.25, 0.15, 0.20, 0.10])
    area_ha = poly.area * 111000 * 111000 / 10000  # Conversão aproximada para hectares
    
    poligonos_data.append({
        'id': i + 1,
        'uso_solo': uso,
        'area_ha': area_ha,
        'perimetro_km': poly.length * 111,
        'geometry': poly
    })

# Criar GeoDataFrame
gdf_uso_solo = gpd.GeoDataFrame(poligonos_data, crs='EPSG:4326')

print(f"\n {len(gdf_uso_solo)} polígonos de uso do solo criados")


# 2. SALVAR COM GDAL/OGR


# Salvar como Shapefile
gdf_uso_solo.to_file('uso_do_solo.shp', driver='ESRI Shapefile')
print(" Shapefile 'uso_do_solo.shp' salvo")

# Salvar como GeoJSON usando OGR
driver_geojson = ogr.GetDriverByName('GeoJSON')
if driver_geojson:
    ds = driver_geojson.CreateDataSource('uso_do_solo.geojson')
    
    # Criar sistema de referência espacial
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    
    # Criar layer
    layer = ds.CreateLayer('uso_solo', srs, ogr.wkbPolygon)
    
    # Adicionar campos
    layer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
    layer.CreateField(ogr.FieldDefn('uso_solo', ogr.OFTString))
    field_area = ogr.FieldDefn('area_ha', ogr.OFTReal)
    field_area.SetWidth(10)
    field_area.SetPrecision(2)
    layer.CreateField(field_area)
    
    # Adicionar features
    for idx, row in gdf_uso_solo.iterrows():
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField('id', int(row['id']))
        feature.SetField('uso_solo', row['uso_solo'])
        feature.SetField('area_ha', float(row['area_ha']))
        
        # Converter geometria
        geom = ogr.CreateGeometryFromWkt(row['geometry'].wkt)
        feature.SetGeometry(geom)
        
        layer.CreateFeature(feature)
        feature = None
    
    ds = None
    print(" GeoJSON 'uso_do_solo.geojson' salvo com GDAL/OGR")


# 3. PROCESSAR COM GDAL/OGR


# Ler shapefile com OGR
driver_shp = ogr.GetDriverByName('ESRI Shapefile')
datasource = driver_shp.Open('uso_do_solo.shp', 0)
layer = datasource.GetLayer()

print(f"\n Leitura com OGR: {layer.GetFeatureCount()} features")

# Calcular estatísticas por tipo de uso
stats_por_uso = {}
layer.ResetReading()

for feature in layer:
    uso = feature.GetField('uso_solo')
    area = feature.GetField('area_ha')
    
    if uso not in stats_por_uso:
        stats_por_uso[uso] = []
    stats_por_uso[uso].append(area)

print("\n" + "="*80)
print("ESTATÍSTICAS DE ÁREA POR USO DO SOLO (via OGR)")
print("="*80)
for uso, areas in stats_por_uso.items():
    print(f"{uso:15s}: {sum(areas):8.2f} ha (média: {np.mean(areas):.2f} ha)")

datasource = None


# 4. ANÁLISE ESPACIAL COM GEOPANDAS


# Análise de área por tipo
area_por_uso = gdf_uso_solo.groupby('uso_solo')['area_ha'].agg([
    ('Total_ha', 'sum'),
    ('Media_ha', 'mean'),
    ('Contagem', 'count')
])

print("\n" + "="*80)
print("ANÁLISE DETALHADA POR USO DO SOLO")
print("="*80)
print(area_por_uso.round(2))

# Calcular percentual de área
area_total = gdf_uso_solo['area_ha'].sum()
percentuais = gdf_uso_solo.groupby('uso_solo')['area_ha'].sum() / area_total * 100
percentuais = percentuais.sort_values(ascending=False)

print("\n" + "="*80)
print("PERCENTUAL DE COBERTURA")
print("="*80)
for uso, perc in percentuais.items():
    print(f"{uso:15s}: {perc:5.1f}%")


# 5. OPERAÇÕES ESPACIAIS


# Criar buffer de 1km para áreas de floresta (proteção)
gdf_metricas = gdf_uso_solo.to_crs('EPSG:31983')  # Projetar para métrica
florestas = gdf_metricas[gdf_metricas['uso_solo'] == 'Floresta'].copy()
florestas['buffer_1km'] = florestas.geometry.buffer(1000)

# Calcular área do buffer
florestas['area_protecao_ha'] = florestas['buffer_1km'].area / 10000

print(f"\n Área total de proteção (buffer 1km): {florestas['area_protecao_ha'].sum():.2f} ha")

# Identificar áreas urbanas próximas a florestas
urbano = gdf_metricas[gdf_metricas['uso_solo'] == 'Área Urbana']
florestas_geom = florestas.set_geometry('buffer_1km')

# Intersecção
if len(urbano) > 0 and len(florestas) > 0:
    urbano_proximo = gpd.sjoin(urbano, florestas_geom, how='inner', predicate='intersects')
    print(f" {len(urbano_proximo)} áreas urbanas próximas a florestas (< 1km)")


# 6. CRIAR RASTER DE USO DO SOLO COM GDAL


# Definir parâmetros do raster
pixel_size = 0.001  # ~100m
n_cols = int((x_max - x_min) / pixel_size)
n_rows = int((y_max - y_min) / pixel_size)

# Criar array numpy
raster_uso = np.zeros((n_rows, n_cols), dtype=np.uint8)

# Mapear usos para valores
uso_para_valor = {uso: i+1 for i, uso in enumerate(usos)}

# Rasterizar polígonos
for idx, row in gdf_uso_solo.iterrows():
    poly = row['geometry']
    valor = uso_para_valor[row['uso_solo']]
    
    # Obter bounds do polígono
    minx, miny, maxx, maxy = poly.bounds
    
    # Converter para índices da matriz
    col_min = max(0, int((minx - x_min) / pixel_size))
    col_max = min(n_cols, int((maxx - x_min) / pixel_size))
    row_min = max(0, int((y_max - maxy) / pixel_size))
    row_max = min(n_rows, int((y_max - miny) / pixel_size))
    
    # Preencher área aproximada
    raster_uso[row_min:row_max, col_min:col_max] = valor

# Salvar raster com GDAL
driver_gtiff = gdal.GetDriverByName('GTiff')
dataset = driver_gtiff.Create('uso_solo_raster.tif', n_cols, n_rows, 1, gdal.GDT_Byte)

# Definir geotransform
geotransform = [x_min, pixel_size, 0, y_max, 0, -pixel_size]
dataset.SetGeoTransform(geotransform)

# Definir projeção
srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)
dataset.SetProjection(srs.ExportToWkt())

# Escrever dados
band = dataset.GetRasterBand(1)
band.WriteArray(raster_uso)
band.SetNoDataValue(0)

dataset.FlushCache()
dataset = None

print(f" Raster criado com GDAL: {n_rows}x{n_cols} pixels")
print(f"  Resolução: ~{pixel_size*111:.0f}m por pixel")


# 7. VISUALIZAÇÕES


fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.25)

fig.suptitle('Análise de Uso do Solo e Cobertura Vegetal', 
             fontsize=16, fontweight='bold')

# Gráfico 1: Mapa de uso do solo
ax1 = fig.add_subplot(gs[0:2, 0])
for uso in usos:
    subset = gdf_uso_solo[gdf_uso_solo['uso_solo'] == uso]
    subset.plot(ax=ax1, color=cores_uso[uso], edgecolor='black', 
                linewidth=0.5, alpha=0.7, label=uso)
ax1.set_title('Mapa de Uso do Solo', fontweight='bold', fontsize=13)
ax1.set_xlabel('Longitude')
ax1.set_ylabel('Latitude')
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)

# Gráfico 2: Raster de uso
ax2 = fig.add_subplot(gs[0:2, 1])
im = ax2.imshow(raster_uso, extent=[x_min, x_max, y_min, y_max], 
                cmap='tab10', alpha=0.8, aspect='auto')
ax2.set_title('Raster de Uso do Solo (GDAL)', fontweight='bold', fontsize=13)
ax2.set_xlabel('Longitude')
ax2.set_ylabel('Latitude')
ax2.grid(True, alpha=0.3)

# Gráfico 3: Área por uso
ax3 = fig.add_subplot(gs[2, 0])
area_por_tipo = gdf_uso_solo.groupby('uso_solo')['area_ha'].sum().sort_values()
cores_bars = [cores_uso[uso] for uso in area_por_tipo.index]
bars = ax3.barh(area_por_tipo.index, area_por_tipo.values, color=cores_bars, 
                edgecolor='black', linewidth=1.5)
ax3.set_title('Área Total por Tipo de Uso', fontweight='bold', fontsize=12)
ax3.set_xlabel('Área (hectares)')
for i, v in enumerate(area_por_tipo.values):
    ax3.text(v, i, f' {v:.1f} ha', va='center', fontweight='bold')

# Gráfico 4: Percentuais
ax4 = fig.add_subplot(gs[2, 1])
cores_pie = [cores_uso[uso] for uso in percentuais.index]
wedges, texts, autotexts = ax4.pie(percentuais.values, labels=percentuais.index,
                                     autopct='%1.1f%%', startangle=90,
                                     colors=cores_pie, explode=[0.05]*len(percentuais))
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')
    autotext.set_fontsize(10)
ax4.set_title('Distribuição Percentual de Uso', fontweight='bold', fontsize=12)

plt.savefig('analise_uso_solo.png', dpi=300, bbox_inches='tight')
print("\n Visualizações salvas em 'analise_uso_solo.png'")
plt.show()


# 8. EXPORTAR RELATÓRIOS


# Relatório CSV
relatorio = gdf_uso_solo[['id', 'uso_solo', 'area_ha', 'perimetro_km']].copy()
relatorio['percentual'] = (relatorio['area_ha'] / area_total * 100).round(2)
relatorio = relatorio.sort_values('area_ha', ascending=False)
relatorio.to_csv('relatorio_uso_solo.csv', index=False)

print(" Relatório exportado: 'relatorio_uso_solo.csv'")

# Estatísticas resumidas
resumo = pd.DataFrame({
    'Uso do Solo': percentuais.index,
    'Área (ha)': [gdf_uso_solo[gdf_uso_solo['uso_solo']==u]['area_ha'].sum() 
                  for u in percentuais.index],
    'Percentual (%)': percentuais.values,
    'N° Polígonos': [len(gdf_uso_solo[gdf_uso_solo['uso_solo']==u]) 
                     for u in percentuais.index]
})
resumo.to_csv('resumo_uso_solo.csv', index=False)

print(" Resumo estatístico exportado: 'resumo_uso_solo.csv'")

print("\n" + "="*80)
print("INSIGHTS PRINCIPAIS")
print("="*80)
uso_dominante = percentuais.index[0]
area_floresta = gdf_uso_solo[gdf_uso_solo['uso_solo']=='Floresta']['area_ha'].sum()
print(f" Uso predominante: {uso_dominante} ({percentuais.iloc[0]:.1f}%)")
print(f" Área de floresta preservada: {area_floresta:.2f} ha")
print(f" Total de polígonos mapeados: {len(gdf_uso_solo)}")
print(f" Área total da região: {area_total:.2f} ha")

print("\n Análise de uso do solo concluída com sucesso!")