"""
Módulo de Unificación, Limpieza e Ingeniería de Características Geo-Sismológicas.
Procesa el catálogo sísmico completo de la Red Sismológica Nacional de Colombia (SGC)
(1993 - 2026), unifica los esquemas previo y posterior a 2018, e integra datos
oficiales del DANE / IGAC para el Departamento de Santander.
"""

import os
import glob
import math
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
import numpy as np
import pandas as pd

from src.dane_santander import get_dane_info, normalizar_texto

# Centro de referencia geofísica: Nido Sísmico de Bucaramanga (Mesa de Los Santos)
NIDO_LAT = 6.800
NIDO_LON = -73.120

def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia geodésica en kilómetros entre dos coordenadas (Haversine)."""
    R = 6371.0 # Radio medio de la Tierra en km
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0)**2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return R * c

def estimar_pga_attenuation(magnitud, profundidad_km, dist_epicentral_km):
    """
    Estima la Aceleración Pico del Suelo (PGA en g) mediante ley de atenuación GMPE
    adaptada a zonas de subducción intermedia / corteza andina (Campbell / SGC).
    R_hypo = sqrt(R_epi^2 + Prof^2)
    """
    r_hypo = np.sqrt(dist_epicentral_km**2 + profundidad_km**2)
    # Modelo espectral empírico de atenuación
    ln_pga = -1.20 + 0.72 * magnitud - 1.35 * np.log(np.maximum(r_hypo, 5.0) + 12.0)
    pga = np.exp(ln_pga)
    return np.clip(pga, 0.0001, 1.5)

def extraer_filas_xlsx(filepath):
    """Extrae las filas crudas de un archivo .xlsx directamente desde el XML para máxima velocidad."""
    with zipfile.ZipFile(filepath, 'r') as z:
        sst = []
        if 'xl/sharedStrings.xml' in z.namelist():
            tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
            ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            for si in tree.findall('ns:si', ns):
                t = si.find('ns:t', ns)
                sst.append(t.text if t is not None else '')
        
        tree = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        rows = tree.findall('.//ns:row', ns)
        
        data = []
        for r in rows:
            row_data = []
            for c in r.findall('ns:c', ns):
                t_attr = c.attrib.get('t')
                v = c.find('ns:v', ns)
                val = v.text if v is not None else ''
                if t_attr == 's' and val.isdigit():
                    val = sst[int(val)]
                row_data.append(val)
            data.append(row_data)
        return data

def parsear_reporte(filepath):
    """Detecta el formato (previo a 2018 o moderno post-2018) y extrae los sismos de Santander."""
    raw_rows = extraer_filas_xlsx(filepath)
    if not raw_rows:
        return []

    r0 = raw_rows[0]
    is_new = 'PARAMETROS' in r0[0] if len(r0) > 0 and r0[0] else False
    
    start_row = 14 if is_new else 1
    dept_idx = 12 if is_new else 7
    
    registros = []
    
    for r in raw_rows[start_row:]:
        if len(r) <= dept_idx:
            continue
        
        # Filtro de Santander
        dept_str = r[dept_idx].upper()
        if 'SANTANDER' not in dept_str or 'NORTE DE SANTANDER' in dept_str:
            continue
            
        try:
            if is_new:
                # Esquema post-marzo 2018:
                # 0: FECHA - HORA UTC, 1: LATITUD, 2: LONGITUD, 3: PROFUNDIDAD, 4: MAGNITUD,
                # 5: TIPO MAG, 6: FASES, 7: RMS, 8: GAP, 9: ERR LAT, 10: ERR LON, 11: ERR PROF, 12: REGION, 13: ESTADO
                fecha_hora = r[0].strip()
                lat = float(r[1]) if len(r) > 1 and r[1] else np.nan
                lon = float(r[2]) if len(r) > 2 and r[2] else np.nan
                prof = float(r[3]) if len(r) > 3 and r[3] else np.nan
                mag = float(r[4]) if len(r) > 4 and r[4] else np.nan
                fases = int(float(r[6])) if len(r) > 6 and r[6] else 0
                rms = float(r[7]) if len(r) > 7 and r[7] else np.nan
                gap = float(r[8]) if len(r) > 8 and r[8] else np.nan
                err_lat = float(r[9]) if len(r) > 9 and r[9] else np.nan
                err_lon = float(r[10]) if len(r) > 10 and r[10] else np.nan
                err_prof = float(r[11]) if len(r) > 11 and r[11] else np.nan
                region = r[12] if len(r) > 12 else ''
                mun = region.split('-')[0].strip() if '-' in region else region
                estado = r[13] if len(r) > 13 else 'manual'
            else:
                # Esquema previo a marzo 2018:
                # 0: FECHA, 1: HORA_UTC, 2: LATITUD, 3: LONGITUD, 4: PROFUNDIDAD, 5: MAG Ml,
                # 6: MAG Mw, 7: DEPARTAMENTO, 8: MUNICIPIO, 9: FASES, 10: RMS, 11: GAP, 12: ERR LAT, 13: ERR LON, 14: ERR PROF, 15: ESTADO
                fecha_hora = f"{r[0].strip()} {r[1].strip()}"
                lat = float(r[2]) if len(r) > 2 and r[2] else np.nan
                lon = float(r[3]) if len(r) > 3 and r[3] else np.nan
                prof = float(r[4]) if len(r) > 4 and r[4] else np.nan
                # Preferir Mw si está disponible, si no Ml
                mag_mw = float(r[6]) if len(r) > 6 and r[6] else np.nan
                mag_ml = float(r[5]) if len(r) > 5 and r[5] else np.nan
                mag = mag_mw if not np.isnan(mag_mw) else mag_ml
                mun = r[8].strip() if len(r) > 8 else ''
                fases = int(float(r[9])) if len(r) > 9 and r[9] else 0
                rms = float(r[10]) if len(r) > 10 and r[10] else np.nan
                gap = float(r[11]) if len(r) > 11 and r[11] else np.nan
                err_lat = float(r[12]) if len(r) > 12 and r[12] else np.nan
                err_lon = float(r[13]) if len(r) > 13 and r[13] else np.nan
                err_prof = float(r[14]) if len(r) > 14 and r[14] else np.nan
                estado = r[15] if len(r) > 15 else 'Revisado'

            registros.append({
                'fecha_hora_utc': fecha_hora,
                'latitud': lat,
                'longitud': lon,
                'profundidad_km': prof,
                'magnitud': mag,
                'municipio_raw': mun,
                'fases_estaciones': fases,
                'rms_seg': rms,
                'gap_grados': gap,
                'error_latitud_km': err_lat,
                'error_longitud_km': err_lon,
                'error_profundidad_km': err_prof,
                'estado': estado,
                'fuente_archivo': os.path.basename(filepath)
            })
        except Exception:
            continue

    return registros

def construir_dataset_unificado(input_dir='.', output_csv='dataset_santander_unificado.csv', max_records=None):
    """Lee todos los reportes, filtra Santander, limpia duplicados y deriva las variables geo-sismológicas."""
    print("Iniciando extracción y unificación de catálogos del SGC...")
    archivos = sorted(glob.glob(os.path.join(input_dir, 'reporte*.xlsx')))
    print(f"Archivos encontrados: {len(archivos)}")

    todos_registros = []
    for f in archivos:
        print(f"  Procesando {os.path.basename(f)}...", end=" ", flush=True)
        regs = parsear_reporte(f)
        print(f"{len(regs)} eventos de Santander.")
        todos_registros.extend(regs)

    df = pd.DataFrame(todos_registros)
    print(f"\nTotal registros brutos de Santander extraídos: {len(df):,}")

    # 1. Limpieza de fechas y ordenamiento cronológico
    df['fecha_hora_utc'] = pd.to_datetime(df['fecha_hora_utc'], errors='coerce')
    df = df.dropna(subset=['fecha_hora_utc', 'latitud', 'longitud', 'magnitud'])
    df = df.sort_values('fecha_hora_utc').reset_index(drop=True)

    # 2. Filtrado geográfico de control (Bounding Box Santander: Lat [5.5, 8.5], Lon [-74.6, -72.0])
    df = df[(df['latitud'] >= 5.5) & (df['latitud'] <= 8.5) & 
            (df['longitud'] >= -74.6) & (df['longitud'] <= -72.0)]

    # 3. Tratamiento de duplicados
    registros_antes = len(df)
    # Redondeo temporal a minutos para detectar eventos duplicados por reconteo
    df['fecha_minuto'] = df['fecha_hora_utc'].dt.floor('min')
    df = df.drop_duplicates(subset=['fecha_minuto', 'latitud', 'longitud', 'magnitud'], keep='first')
    df = df.drop(columns=['fecha_minuto']).reset_index(drop=True)
    print(f"Duplicados eliminados: {registros_antes - len(df):,} | Registros limpios: {len(df):,}")

    # 4. Imputación de nulos y control de calidad instrumental
    df['error_latitud_km'] = df['error_latitud_km'].fillna(df['error_latitud_km'].median())
    df['error_longitud_km'] = df['error_longitud_km'].fillna(df['error_longitud_km'].median())
    df['error_profundidad_km'] = df['error_profundidad_km'].fillna(df['error_profundidad_km'].median())
    df['rms_seg'] = df['rms_seg'].fillna(df['rms_seg'].median())
    df['gap_grados'] = df['gap_grados'].fillna(df['gap_grados'].median())

    # 5. Cruce con Datos Oficiales DANE / IGAC
    print("Integrando información oficial DANE e IGAC por municipio...")
    df['municipio_normalizado'] = df['municipio_raw'].apply(normalizar_texto)
    
    dane_info = df['municipio_normalizado'].apply(get_dane_info)
    dane_df = pd.DataFrame(list(dane_info))
    
    for col in ['codigo_dane', 'subregion', 'poblacion', 'area_km2', 'densidad_hab_km2', 
                'nbi_porcentaje', 'vulnerabilidad_vivienda_pct', 'lat_centroide', 'lon_centroide']:
        df[col] = dane_df[col]

    # 6. Ingeniería de Variables Geo-Sismológicas
    print("Calculando variables físicas, geofísicas y derivadas...")

    # Variable: Distancia al epicentro del Nido Sísmico de Bucaramanga
    df['distancia_nido_km'] = calcular_distancia_haversine(
        df['latitud'].values, df['longitud'].values, NIDO_LAT, NIDO_LON
    )

    # Variable: Distancia al centroide municipal
    df['distancia_centroide_km'] = calcular_distancia_haversine(
        df['latitud'].values, df['longitud'].values, 
        df['lat_centroide'].values, df['lon_centroide'].values
    )

    # Variable: Error hipocentral tridimensional combinado
    df['error_hipocentral_3d_km'] = np.sqrt(
        df['error_latitud_km']**2 + df['error_longitud_km']**2 + df['error_profundidad_km']**2
    )

    # Variable: Energía sísmica liberada en Joules (Gutenberg-Richter)
    # log10(E) = 4.8 + 1.5 * M
    df['energia_sismica_joules'] = 10.0 ** (4.8 + 1.5 * df['magnitud'])

    # Variable: Deformación de Benioff (Benioff Strain, proporcional a sqrt(E))
    df['benioff_strain'] = 10.0 ** (0.75 * df['magnitud'])

    # Variable: Clasificación focal (Profundo vs Cortical)
    # Sismos profundos del nido (h >= 70 km) causan menos aceleración superficial que sismos corticales (h < 70 km)
    df['es_sismo_profundo'] = (df['profundidad_km'] >= 70.0).astype(int)

    # Variable: Aceleración pico del suelo estimada (PGA en g)
    df['aceleracion_suelo_estimada_pga'] = estimar_pga_attenuation(
        df['magnitud'].values, df['profundidad_km'].values, df['distancia_centroide_km'].values
    )

    # Variable: Tiempo inter-evento (horas transcurridas desde el evento anterior)
    df['tiempo_inter_evento_horas'] = df['fecha_hora_utc'].diff().dt.total_seconds().fillna(0.0) / 3600.0
    # Recorte de anomalías por gaps entre periodos
    df['tiempo_inter_evento_horas'] = df['tiempo_inter_evento_horas'].clip(lower=0.0, upper=720.0)

    # Variables temporales móviles por subregión / municipio (Tasa 30 días y Energía Acumulada)
    print("Calculando dinámicas temporales rodantes (tasa sísmica y acumulación)...")
    # Para calcular de manera vectorial y rápida:
    # Usamos rolling temporal de 30 días sobre el catálogo cronológico
    df = df.set_index('fecha_hora_utc')
    df['tasa_sismicidad_30d'] = df['magnitud'].rolling('30D').count()
    df['energia_acumulada_30d'] = df['energia_sismica_joules'].rolling('30D').sum()
    df['magnitud_max_30d'] = df['magnitud'].rolling('30D').max()
    df['profundidad_media_30d'] = df['profundidad_km'].rolling('30D').mean()
    df = df.reset_index()

    # Variable: b-value local estimado (Gutenberg-Richter)
    # Estimación de Aki (1965): b = log10(e) / (M_mean - M_min)
    m_min = 1.0
    m_rolling_mean = df['magnitud'].rolling(window=100, min_periods=20).mean().fillna(df['magnitud'].mean())
    df['b_value_local'] = (np.log10(np.e) / np.maximum(m_rolling_mean - m_min, 0.15)).clip(0.4, 2.5)

    # 7. Variable Objetivo Formal: Prioridad de Riesgo Socio-Sísmico Territorial
    # Definición: No es una suma lineal simple, sino una formulación física-social no lineal:
    # Amenaza = PGA * Factor_Profundidad * log10(Energia_30d)
    # Vulnerabilidad = (NBI / 100) * (Vulnerabilidad_Vivienda / 100)
    # Exposición = log10(Población)
    # Riesgo = Amenaza * Vulnerabilidad * Exposición
    print("Calculando Variable Objetivo (Prioridad de Riesgo Socio-Sísmico)...")
    
    factor_prof = np.where(df['es_sismo_profundo'] == 1, 0.45, 1.25) # Las fallas superficiales amplifican la amenaza
    factor_amenaza = (df['aceleracion_suelo_estimada_pga'] * 100.0) * factor_prof * np.log10(np.maximum(df['energia_acumulada_30d'], 1e6) / 1e5)
    factor_vulnerabilidad = (df['nbi_porcentaje'] / 100.0) * (df['vulnerabilidad_vivienda_pct'] / 100.0)
    factor_exposicion = np.log10(np.maximum(df['poblacion'], 500.0))

    score_riesgo_bruto = factor_amenaza * factor_vulnerabilidad * factor_exposicion
    
    # Normalización a escala [0, 100] percentilar robusta
    p99 = np.percentile(score_riesgo_bruto, 99.5)
    p01 = np.percentile(score_riesgo_bruto, 0.5)
    df['prioridad_riesgo_socio_sismico'] = np.clip((score_riesgo_bruto - p01) / (p99 - p01) * 100.0, 0.0, 100.0)

    # Categorización ordinal de riesgo
    condiciones = [
        df['prioridad_riesgo_socio_sismico'] < 25.0,
        (df['prioridad_riesgo_socio_sismico'] >= 25.0) & (df['prioridad_riesgo_socio_sismico'] < 50.0),
        (df['prioridad_riesgo_socio_sismico'] >= 50.0) & (df['prioridad_riesgo_socio_sismico'] < 75.0),
        df['prioridad_riesgo_socio_sismico'] >= 75.0
    ]
    etiquetas = ['Bajo', 'Medio', 'Alto', 'Critico']
    df['categoria_riesgo'] = np.select(condiciones, etiquetas, default='Bajo')

    # Guardar dataset
    print(f"Guardando dataset limpio final en '{output_csv}'...")
    df.to_csv(output_csv, index=False)
    print(f"¡Éxito! Dataset generado con {len(df):,} filas y {len(df.columns)} columnas.")
    return df

if __name__ == '__main__':
    construir_dataset_unificado()
