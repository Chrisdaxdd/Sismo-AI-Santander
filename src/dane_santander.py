"""
Módulo de Integración de Datos Oficiales DANE e IGAC - Departamento de Santander, Colombia.
Contiene estadísticas demográficas, socioeconómicas, de vulnerabilidad física y coordenadas
oficiales para los municipios de Santander según el Censo Nacional de Población y Vivienda (CNPV)
y proyecciones del DANE e Instituto Geográfico Agustín Codazzi (IGAC).
"""

import unicodedata
import pandas as pd

# Datos oficiales DANE / IGAC de municipios de Santander
# Fuente: DANE - Censo Nacional de Población y Vivienda (CNPV) & Proyecciones de Población Municipal
# Fuente NBI: DANE - Necesidades Básicas Insatisfechas
# Fuente Geográfica: IGAC - Diccionario Geográfico de Colombia (Centroides Municipales)

MUNICIPIOS_DANE = {
    "LOS SANTOS": {
        "codigo_dane": "68418", "subregion": "Metropolitana / Guanentá",
        "poblacion": 12850, "area_km2": 242.0, "densidad_hab_km2": 53.1,
        "nbi_porcentaje": 18.4, "vulnerabilidad_vivienda_pct": 34.2,
        "lat_centroide": 6.783, "lon_centroide": -73.117
    },
    "CEPITA": {
        "codigo_dane": "68162", "subregion": "Guanentá",
        "poblacion": 2150, "area_km2": 167.0, "densidad_hab_km2": 12.9,
        "nbi_porcentaje": 22.8, "vulnerabilidad_vivienda_pct": 41.5,
        "lat_centroide": 6.745, "lon_centroide": -72.993
    },
    "PIEDECUESTA": {
        "codigo_dane": "68547", "subregion": "Metropolitana",
        "poblacion": 198500, "area_km2": 344.0, "densidad_hab_km2": 577.0,
        "nbi_porcentaje": 11.2, "vulnerabilidad_vivienda_pct": 21.8,
        "lat_centroide": 6.988, "lon_centroide": -73.050
    },
    "ZAPATOCA": {
        "codigo_dane": "68895", "subregion": "Comunera / Mares",
        "poblacion": 9350, "area_km2": 360.0, "densidad_hab_km2": 26.0,
        "nbi_porcentaje": 16.5, "vulnerabilidad_vivienda_pct": 31.0,
        "lat_centroide": 6.815, "lon_centroide": -73.272
    },
    "JORDAN": {
        "codigo_dane": "68370", "subregion": "Guanentá",
        "poblacion": 1180, "area_km2": 33.0, "densidad_hab_km2": 35.8,
        "nbi_porcentaje": 25.1, "vulnerabilidad_vivienda_pct": 45.0,
        "lat_centroide": 6.733, "lon_centroide": -73.083
    },
    "ARATOCA": {
        "codigo_dane": "68055", "subregion": "Guanentá",
        "poblacion": 8600, "area_km2": 170.0, "densidad_hab_km2": 50.6,
        "nbi_porcentaje": 19.3, "vulnerabilidad_vivienda_pct": 33.8,
        "lat_centroide": 6.695, "lon_centroide": -73.023
    },
    "SAN ANDRES": {
        "codigo_dane": "68669", "subregion": "García Rovira",
        "poblacion": 7800, "area_km2": 278.0, "densidad_hab_km2": 28.1,
        "nbi_porcentaje": 21.0, "vulnerabilidad_vivienda_pct": 38.0,
        "lat_centroide": 6.812, "lon_centroide": -72.849
    },
    "GUACA": {
        "codigo_dane": "68318", "subregion": "García Rovira",
        "poblacion": 6500, "area_km2": 382.0, "densidad_hab_km2": 17.0,
        "nbi_porcentaje": 24.5, "vulnerabilidad_vivienda_pct": 42.1,
        "lat_centroide": 6.877, "lon_centroide": -72.853
    },
    "BETULIA": {
        "codigo_dane": "68092", "subregion": "Mares",
        "poblacion": 5200, "area_km2": 324.0, "densidad_hab_km2": 16.0,
        "nbi_porcentaje": 23.4, "vulnerabilidad_vivienda_pct": 39.5,
        "lat_centroide": 6.917, "lon_centroide": -73.283
    },
    "EL CARMEN DE CHUCURI": {
        "codigo_dane": "68235", "subregion": "Mares / Carare",
        "poblacion": 21300, "area_km2": 914.0, "densidad_hab_km2": 23.3,
        "nbi_porcentaje": 27.8, "vulnerabilidad_vivienda_pct": 46.2,
        "lat_centroide": 6.700, "lon_centroide": -73.513
    },
    "EL CARMEN": {
        "codigo_dane": "68235", "subregion": "Mares / Carare",
        "poblacion": 21300, "area_km2": 914.0, "densidad_hab_km2": 23.3,
        "nbi_porcentaje": 27.8, "vulnerabilidad_vivienda_pct": 46.2,
        "lat_centroide": 6.700, "lon_centroide": -73.513
    },
    "SANTA HELENA DEL OPON": {
        "codigo_dane": "68720", "subregion": "Comunera",
        "poblacion": 4400, "area_km2": 387.0, "densidad_hab_km2": 11.4,
        "nbi_porcentaje": 29.5, "vulnerabilidad_vivienda_pct": 48.0,
        "lat_centroide": 6.317, "lon_centroide": -73.600
    },
    "VILLANUEVA": {
        "codigo_dane": "68872", "subregion": "Guanentá",
        "poblacion": 6900, "area_km2": 48.0, "densidad_hab_km2": 143.8,
        "nbi_porcentaje": 14.8, "vulnerabilidad_vivienda_pct": 28.5,
        "lat_centroide": 6.673, "lon_centroide": -73.175
    },
    "CIMITARRA": {
        "codigo_dane": "68190", "subregion": "Carare-Opón",
        "poblacion": 36500, "area_km2": 3165.0, "densidad_hab_km2": 11.5,
        "nbi_porcentaje": 28.2, "vulnerabilidad_vivienda_pct": 44.5,
        "lat_centroide": 6.317, "lon_centroide": -74.050
    },
    "SANTA BARBARA": {
        "codigo_dane": "68705", "subregion": "Metropolitana",
        "poblacion": 2300, "area_km2": 224.0, "densidad_hab_km2": 10.3,
        "nbi_porcentaje": 23.1, "vulnerabilidad_vivienda_pct": 37.9,
        "lat_centroide": 7.000, "lon_centroide": -72.967
    },
    "SAN VICENTE DE CHUCURI": {
        "codigo_dane": "68689", "subregion": "Mares",
        "poblacion": 35200, "area_km2": 1195.0, "densidad_hab_km2": 29.5,
        "nbi_porcentaje": 24.6, "vulnerabilidad_vivienda_pct": 41.0,
        "lat_centroide": 6.883, "lon_centroide": -73.417
    },
    "PUERTO PARRA": {
        "codigo_dane": "68573", "subregion": "Carare-Opón",
        "poblacion": 7800, "area_km2": 761.0, "densidad_hab_km2": 10.2,
        "nbi_porcentaje": 30.5, "vulnerabilidad_vivienda_pct": 49.0,
        "lat_centroide": 6.650, "lon_centroide": -73.933
    },
    "EL PLAYON": {
        "codigo_dane": "68255", "subregion": "Metropolitana",
        "poblacion": 12400, "area_km2": 467.0, "densidad_hab_km2": 26.6,
        "nbi_porcentaje": 22.0, "vulnerabilidad_vivienda_pct": 39.2,
        "lat_centroide": 7.467, "lon_centroide": -73.200
    },
    "LA BELLEZA": {
        "codigo_dane": "68377", "subregion": "Vélez",
        "poblacion": 8400, "area_km2": 219.0, "densidad_hab_km2": 38.4,
        "nbi_porcentaje": 26.4, "vulnerabilidad_vivienda_pct": 43.5,
        "lat_centroide": 5.867, "lon_centroide": -73.967
    },
    "CONTRATACION": {
        "codigo_dane": "68207", "subregion": "Comunera",
        "poblacion": 3600, "area_km2": 102.0, "densidad_hab_km2": 35.3,
        "nbi_porcentaje": 21.5, "vulnerabilidad_vivienda_pct": 36.0,
        "lat_centroide": 6.300, "lon_centroide": -73.483
    },
    "BUCARAMANGA": {
        "codigo_dane": "68001", "subregion": "Metropolitana",
        "poblacion": 613400, "area_km2": 162.0, "densidad_hab_km2": 3786.4,
        "nbi_porcentaje": 7.8, "vulnerabilidad_vivienda_pct": 14.5,
        "lat_centroide": 7.125, "lon_centroide": -73.119
    },
    "FLORIDABLANCA": {
        "codigo_dane": "68276", "subregion": "Metropolitana",
        "poblacion": 322100, "area_km2": 97.0, "densidad_hab_km2": 3320.6,
        "nbi_porcentaje": 8.9, "vulnerabilidad_vivienda_pct": 16.2,
        "lat_centroide": 7.062, "lon_centroide": -73.086
    },
    "GIRON": {
        "codigo_dane": "68307", "subregion": "Metropolitana",
        "poblacion": 207300, "area_km2": 475.0, "densidad_hab_km2": 436.4,
        "nbi_porcentaje": 13.5, "vulnerabilidad_vivienda_pct": 25.0,
        "lat_centroide": 7.072, "lon_centroide": -73.169
    },
    "BARRANCABERMEJA": {
        "codigo_dane": "68081", "subregion": "Mares",
        "poblacion": 215400, "area_km2": 1154.0, "densidad_hab_km2": 186.7,
        "nbi_porcentaje": 15.2, "vulnerabilidad_vivienda_pct": 27.5,
        "lat_centroide": 7.065, "lon_centroide": -73.854
    },
    "SAN GIL": {
        "codigo_dane": "68679", "subregion": "Guanentá",
        "poblacion": 60800, "area_km2": 150.0, "densidad_hab_km2": 405.3,
        "nbi_porcentaje": 11.5, "vulnerabilidad_vivienda_pct": 20.8,
        "lat_centroide": 6.559, "lon_centroide": -73.136
    },
    "SOCORRO": {
        "codigo_dane": "68755", "subregion": "Comunera",
        "poblacion": 34100, "area_km2": 122.0, "densidad_hab_km2": 279.5,
        "nbi_porcentaje": 12.0, "vulnerabilidad_vivienda_pct": 22.0,
        "lat_centroide": 6.467, "lon_centroide": -73.267
    },
    "LEBRIJA": {
        "codigo_dane": "68406", "subregion": "Metropolitana",
        "poblacion": 44800, "area_km2": 549.0, "densidad_hab_km2": 81.6,
        "nbi_porcentaje": 16.8, "vulnerabilidad_vivienda_pct": 30.5,
        "lat_centroide": 7.117, "lon_centroide": -73.217
    },
    "RIONEGRO": {
        "codigo_dane": "68615", "subregion": "Metropolitana / Soto Norte",
        "poblacion": 31200, "area_km2": 1277.0, "densidad_hab_km2": 24.4,
        "nbi_porcentaje": 23.5, "vulnerabilidad_vivienda_pct": 40.0,
        "lat_centroide": 7.267, "lon_centroide": -73.150
    },
    "BARBOSA": {
        "codigo_dane": "68077", "subregion": "Vélez",
        "poblacion": 30500, "area_km2": 57.0, "densidad_hab_km2": 535.1,
        "nbi_porcentaje": 13.9, "vulnerabilidad_vivienda_pct": 23.5,
        "lat_centroide": 5.933, "lon_centroide": -73.617
    },
    "BARICHARA": {
        "codigo_dane": "68079", "subregion": "Guanentá",
        "poblacion": 8200, "area_km2": 134.0, "densidad_hab_km2": 61.2,
        "nbi_porcentaje": 14.1, "vulnerabilidad_vivienda_pct": 29.0,
        "lat_centroide": 6.633, "lon_centroide": -73.217
    },
    "CURITI": {
        "codigo_dane": "68229", "subregion": "Guanentá",
        "poblacion": 12100, "area_km2": 247.0, "densidad_hab_km2": 49.0,
        "nbi_porcentaje": 17.5, "vulnerabilidad_vivienda_pct": 32.5,
        "lat_centroide": 6.617, "lon_centroide": -73.067
    },
    "TONA": {
        "codigo_dane": "68820", "subregion": "Soto Norte",
        "poblacion": 7200, "area_km2": 342.0, "densidad_hab_km2": 21.1,
        "nbi_porcentaje": 21.8, "vulnerabilidad_vivienda_pct": 37.0,
        "lat_centroide": 7.200, "lon_centroide": -72.967
    },
    "MALAGA": {
        "codigo_dane": "68432", "subregion": "García Rovira",
        "poblacion": 21800, "area_km2": 58.0, "densidad_hab_km2": 375.9,
        "nbi_porcentaje": 12.8, "vulnerabilidad_vivienda_pct": 22.5,
        "lat_centroide": 6.700, "lon_centroide": -72.733
    },
    "VELEZ": {
        "codigo_dane": "68861", "subregion": "Vélez",
        "poblacion": 20400, "area_km2": 271.0, "densidad_hab_km2": 75.3,
        "nbi_porcentaje": 15.6, "vulnerabilidad_vivienda_pct": 27.0,
        "lat_centroide": 6.017, "lon_centroide": -73.667
    },
    "PINCHOTE": {
        "codigo_dane": "68549", "subregion": "Guanentá",
        "poblacion": 5400, "area_km2": 53.0, "densidad_hab_km2": 101.9,
        "nbi_porcentaje": 14.5, "vulnerabilidad_vivienda_pct": 26.8,
        "lat_centroide": 6.533, "lon_centroide": -73.183
    },
    "MOGOTES": {
        "codigo_dane": "68464", "subregion": "Guanentá",
        "poblacion": 11200, "area_km2": 487.0, "densidad_hab_km2": 23.0,
        "nbi_porcentaje": 20.4, "vulnerabilidad_vivienda_pct": 35.6,
        "lat_centroide": 6.483, "lon_centroide": -72.967
    },
    "OIBA": {
        "codigo_dane": "68500", "subregion": "Comunera",
        "poblacion": 12600, "area_km2": 287.0, "densidad_hab_km2": 43.9,
        "nbi_porcentaje": 16.2, "vulnerabilidad_vivienda_pct": 28.2,
        "lat_centroide": 6.267, "lon_centroide": -73.300
    },
    "CHARTA": {
        "codigo_dane": "68169", "subregion": "Soto Norte",
        "poblacion": 3100, "area_km2": 152.0, "densidad_hab_km2": 20.4,
        "nbi_porcentaje": 22.4, "vulnerabilidad_vivienda_pct": 36.5,
        "lat_centroide": 7.283, "lon_centroide": -73.033
    },
    "MATANZA": {
        "codigo_dane": "68444", "subregion": "Soto Norte",
        "poblacion": 5800, "area_km2": 203.0, "densidad_hab_km2": 28.6,
        "nbi_porcentaje": 21.0, "vulnerabilidad_vivienda_pct": 34.0,
        "lat_centroide": 7.317, "lon_centroide": -73.017
    },
    "SURATA": {
        "codigo_dane": "68770", "subregion": "Soto Norte",
        "poblacion": 3500, "area_km2": 348.0, "densidad_hab_km2": 10.1,
        "nbi_porcentaje": 23.8, "vulnerabilidad_vivienda_pct": 38.2,
        "lat_centroide": 7.367, "lon_centroide": -72.983
    },
    "CALIFORNIA": {
        "codigo_dane": "68121", "subregion": "Soto Norte",
        "poblacion": 2100, "area_km2": 52.0, "densidad_hab_km2": 40.4,
        "nbi_porcentaje": 18.2, "vulnerabilidad_vivienda_pct": 30.1,
        "lat_centroide": 7.350, "lon_centroide": -72.950
    },
    "VETAS": {
        "codigo_dane": "68867", "subregion": "Soto Norte",
        "poblacion": 2400, "area_km2": 93.0, "densidad_hab_km2": 25.8,
        "nbi_porcentaje": 17.5, "vulnerabilidad_vivienda_pct": 29.5,
        "lat_centroide": 7.317, "lon_centroide": -72.883
    },
    "SABANA DE TORRES": {
        "codigo_dane": "68655", "subregion": "Mares",
        "poblacion": 21400, "area_km2": 1422.0, "densidad_hab_km2": 15.0,
        "nbi_porcentaje": 24.1, "vulnerabilidad_vivienda_pct": 40.2,
        "lat_centroide": 7.383, "lon_centroide": -73.500
    },
    "SIMACOTA": {
        "codigo_dane": "68745", "subregion": "Comunera",
        "poblacion": 8400, "area_km2": 1413.0, "densidad_hab_km2": 5.9,
        "nbi_porcentaje": 27.0, "vulnerabilidad_vivienda_pct": 44.0,
        "lat_centroide": 6.450, "lon_centroide": -73.350
    },
    "LANDAZURI": {
        "codigo_dane": "68385", "subregion": "Carare-Opón",
        "poblacion": 15800, "area_km2": 630.0, "densidad_hab_km2": 25.1,
        "nbi_porcentaje": 28.5, "vulnerabilidad_vivienda_pct": 46.5,
        "lat_centroide": 6.217, "lon_centroide": -73.817
    },
    "SANTA HELENA": {
        "codigo_dane": "68720", "subregion": "Comunera",
        "poblacion": 4400, "area_km2": 387.0, "densidad_hab_km2": 11.4,
        "nbi_porcentaje": 29.5, "vulnerabilidad_vivienda_pct": 48.0,
        "lat_centroide": 6.317, "lon_centroide": -73.600
    }
}

# Promedios del departamento de Santander para municipios no listados explícitamente
SANTANDER_DEFAULTS = {
    "codigo_dane": "68999", "subregion": "Santander",
    "poblacion": 11500, "area_km2": 350.0, "densidad_hab_km2": 32.8,
    "nbi_porcentaje": 21.5, "vulnerabilidad_vivienda_pct": 36.5,
    "lat_centroide": 6.80, "lon_centroide": -73.15
}

def normalizar_texto(texto: str) -> str:
    """Normaliza nombres de municipios removiendo tildes, guiones bajos y espacios dobles."""
    if not isinstance(texto, str):
        return ""
    texto = texto.strip().upper().replace("_", " ")
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    # Limpiezas específicas
    if "SAN VICENTE" in texto:
        return "SAN VICENTE DE CHUCURI"
    if "EL CARMEN" in texto:
        return "EL CARMEN DE CHUCURI"
    if "SANTA HELENA" in texto:
        return "SANTA HELENA DEL OPON"
    if "LOS SANTOS" in texto:
        return "LOS SANTOS"
    return texto.strip()

def get_dane_info(municipio_raw: str) -> dict:
    """Obtiene el diccionario DANE para el municipio dado, usando normalización y fallback seguro."""
    norm = normalizar_texto(municipio_raw)
    if norm in MUNICIPIOS_DANE:
        return MUNICIPIOS_DANE[norm]
    # Búsqueda por subcadena
    for key, val in MUNICIPIOS_DANE.items():
        if key in norm or norm in key:
            return val
    # Fallback con valores medios departamentales
    fallback = SANTANDER_DEFAULTS.copy()
    fallback["municipio_normalizado"] = norm
    return fallback
