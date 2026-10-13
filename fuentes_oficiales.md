# BLOQUE DE CITACIÓN Y METADATOS DE FUENTES OFICIALES

El presente sistema de Machine Learning y Aprendizaje por Refuerzo se alimenta **exclusivamente de fuentes oficiales gubernamentales y científicas verificables**, sin generación de datos sintéticos.

---

### 1. Fuente Principal: Servicio Geológico Colombiano (SGC) - Red Sismológica Nacional de Colombia (RSNC)
* **Entidad Emisora:** Servicio Geológico Colombiano (Ministerio de Minas y Energía).
* **Catálogo Oficial:** Catálogo Sísmico Nacional y Sistema de Información Sísmica Histórica (SISH).
* **URLs Oficiales:** 
  * Portal de consulta del catálogo: [https://www.sgc.gov.co](https://www.sgc.gov.co)
  * Consulta avanzada de sismicidad: [http://sish.sgc.gov.co/](http://sish.sgc.gov.co/)
* **Periodo de Cobertura Extraído:** 01 de junio de 1993 hasta 13 de octubre de 2026 (más de 33 años de registro instrumental continuo).
* **Filtros Aplicados:**
  * **Criterio Geográfico:** Bounding Box del Departamento de Santander y área de influencia directa:
    * Latitud Mínima: $5.5^\circ\text{N}$, Latitud Máxima: $8.5^\circ\text{N}$
    * Longitud Mínima: $-74.6^\circ\text{W}$, Longitud Máxima: $-72.0^\circ\text{W}$
    * Departamento: `SANTANDER` (excluyendo sismos de Norte de Santander fuera de la cuenca sísmica compartida).
  * **Criterio de Calidad Instrumental:** Depuración de duplicados por coincidencia temporal minuto-a-minuto y coordenadas, imputación de incertidumbres instrumentales mediante mediana robusta del catálogo nacional, y homogeneización de escalas de magnitud ($M_w$ preferencial sobre $M_L$).
* **Total de Eventos Reales Procesados:** **199,013 sismos**.

---

### 2. Fuente Secundaria Oficial: Departamento Administrativo Nacional de Estadística (DANE)
* **Entidad Emisora:** DANE - Gobierno de Colombia.
* **Bases de Datos Utilizadas:**
  * Censo Nacional de Población y Vivienda (CNPV) - Resultados Municipales Santander.
  * Medida de Pobreza Multidimensional y Necesidades Básicas Insatisfechas (NBI) por Municipio.
  * Proyecciones Oficiales de Población Municipal (DANE 2020-2026).
* **URLs Oficiales:**
  * CNPV: [https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/censo-nacional-de-poblacion-y-vivenda-2018](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/censo-nacional-de-poblacion-y-vivenda-2018)
  * NBI Municipal: [https://www.dane.gov.co/index.php/estadisticas-por-tema/pobreza-y-condiciones-de-vida/necesidades-basicas-insatisfechas-nbi](https://www.dane.gov.co/index.php/estadisticas-por-tema/pobreza-y-condiciones-de-vida/necesidades-basicas-insatisfechas-nbi)
* **Variables Extraídas y Filtros:**
  * Códigos DIVIPOLA de Santander (prefijo `68`).
  * Conteo poblacional expuesto por municipio.
  * Porcentaje de Necesidades Básicas Insatisfechas ($NBI\%$).
  * Proporción de viviendas en materiales vulnerables (tapia pisada, mampostería no confinada sin norma NSR-10).

---

### 3. Fuente Cartográfica y Geográfica: Instituto Geográfico Agustín Codazzi (IGAC)
* **Entidad Emisora:** IGAC - Autoridad Geográfica y Catastral de Colombia.
* **Bases de Datos:** Diccionario Geográfico de Colombia y Cartografía Vectorial Oficial de Límites Municipales de Santander.
* **URL Oficial:** [https://www.igac.gov.co/](https://www.igac.gov.co/) / [https://geoportal.igac.gov.co/](https://geoportal.igac.gov.co/)
* **Variables Integradas:**
  * Centroides geográficos oficiales (latitud y longitud de cabeceras).
  * Extensión territorial oficial ($km^2$) para el cálculo de densidad poblacional ($hab/km^2$).

---

### 4. Fuente Geofísica Complementaria: USGS Earthquake Hazards Program
* **Entidad:** United States Geological Survey (USGS).
* **Catálogo:** ANSS Comprehensive Earthquake Catalog (ComCat) vía FDSN Web Services API.
* **URL Oficial:** [https://earthquake.usgs.gov/fdsnws/event/1/](https://earthquake.usgs.gov/fdsnws/event/1/)
* **Uso:** Calibración de parámetros de ley de atenuación GMPE para sismos de subducción intermedia y comprobación de magnitudes de momento en eventos significativos ($M \ge 4.5$).
