# DICCIONARIO DE DATOS OFICIAL: RIESGO SÍSMICO Y PRIORIZACIÓN TERRITORIAL EN SANTANDER

Este conjunto de datos unifica el **Catálogo Sísmico Oficial del Servicio Geológico Colombiano (SGC)** desde junio de 1993 hasta octubre de 2026, cruzado con las estadísticas oficiales del **DANE (Censo Nacional de Población y Vivienda CNPV)** y cartografía de **IGAC**.

El dataset resultante consta de **199,013 observaciones reales** y **39 variables** debidamente homogeneizadas, sin datos sintéticos ni ficticios.

---

## Tabla de Diccionario de Variables (28 Variables Principales Justificadas)

| # | Nombre de Variable | Tipo de Dato | Unidad de Medida | Fuente Oficial | Justificación Técnica y Sismológica / Territorial |
|---|---|---|---|---|---|
| 1 | `fecha_hora_utc` | Datetime (ISO 8601) | AAAA-MM-DD HH:MM:SS | SGC (Red Sismológica Nacional) | Marca temporal universal de ocurrencia del evento. Permite ordenar cronológicamente la serie y evitar fugas temporales (*data leakage*). |
| 2 | `latitud` | Float64 | Grados decimales (°N) | SGC | Coordenada geográfica del epicentro. Esencial para el posicionamiento espacial en Santander y el cálculo de distancias a centros poblados. |
| 3 | `longitud` | Float64 | Grados decimales (°W) | SGC | Coordenada geográfica del epicentro. Permite ubicar la traza respecto a las fallas activas de Bucaramanga-Santa Marta y Suárez. |
| 4 | `profundidad_km` | Float64 | Kilómetros (km) | SGC | Profundidad del foco hipocentral. Discrimina sismos profundos del Nido (~150 km) de sismos corticales (<30 km) de alta amenaza destructiva. |
| 5 | `magnitud` | Float64 | Escala Richter / Momento ($M_L$ / $M_w$) | SGC | Magnitud estimada del sismo. Representa la energía relativa liberada en la fuente sísmica. |
| 6 | `fases_estaciones` | Int64 | Conteo de fases | SGC | Número de arribos de ondas P y S registradas por la red. A mayor número de fases, mayor confiabilidad instrumental de la localización. |
| 7 | `rms_seg` | Float64 | Segundos (s) | SGC | Raíz del error cuadrático medio de los tiempos de viaje. Métrica de calidad del ajuste hipocentral (valores < 0.5 s indican excelente ajuste). |
| 8 | `gap_grados` | Float64 | Grados sexagesimales (°) | SGC | Brecha azimutal máxima entre estaciones sismológicas. Valores menores a 180° aseguran una localización epicentral bien constreñida. |
| 9 | `error_latitud_km` | Float64 | Kilómetros (km) | SGC | Incertidumbre formal en el semieje latitudinal de la elipse de error del epicentro. |
| 10 | `error_longitud_km` | Float64 | Kilómetros (km) | SGC | Incertidumbre formal en el semieje longitudinal de la elipse de error del epicentro. |
| 11 | `error_profundidad_km` | Float64 | Kilómetros (km) | SGC | Incertidumbre vertical en la localización del foco hipocentral. |
| 12 | `error_hipocentral_3d_km` | Float64 | Kilómetros (km) | Derivada (SGC) | Norma euclidiana del error tridimensional: $\sqrt{\Delta x^2 + \Delta y^2 + \Delta z^2}$. Cuantifica la incertidumbre instrumental global. |
| 13 | `municipio_normalizado` | String (Categórica) | Texto normalizado | SGC / DANE | Nombre estandarizado del municipio de Santander afectado, permitiendo la unión inequívoca con las tablas DIVIPOLA del DANE. |
| 14 | `codigo_dane` | String (Categórica) | Código DIVIPOLA de 5 dígitos | DANE | Identificador único municipal oficial según el Departamento Administrativo Nacional de Estadística (ej. 68001 Bucaramanga, 68418 Los Santos). |
| 15 | `subregion` | String (Categórica) | Nombre de provincia | Gobernación / DANE | Provincia administrativa de Santander (Metropolitana, Guanentá, Mares, Soto Norte, Comunera, Carare-Opón, García Rovira). |
| 16 | `poblacion` | Int64 | Número de habitantes | DANE (CNPV / Proyecciones) | Población total del municipio expuesta a la amenaza sísmica (factor directo de exposición humana). |
| 17 | `densidad_hab_km2` | Float64 | Habitantes por $\text{km}^2$ | DANE / IGAC | Concentración demográfica del municipio. Mayor densidad implica mayor riesgo de víctimas ante colapsos estructurales. |
| 18 | `nbi_porcentaje` | Float64 | Porcentaje (%) | DANE | Índice de Necesidades Básicas Insatisfechas. Mide la vulnerabilidad socioeconómica y capacidad de resiliencia comunitaria ante desastres. |
| 19 | `vulnerabilidad_vivienda_pct` | Float64 | Porcentaje (%) | DANE (CNPV) | Proporción de viviendas construidas en materiales vulnerables (tapia pisada, bahareque, mampostería no confinada sin norma NSR-10). |
| 20 | `distancia_nido_km` | Float64 | Kilómetros (km) | Derivada (Haversine) | Distancia geodésica al epicentro del Nido Sísmico de Bucaramanga ($6.80^\circ \text{N}, -73.12^\circ \text{W}$). Determina proximidad al foco principal. |
| 21 | `distancia_centroide_km` | Float64 | Kilómetros (km) | Derivada (IGAC) | Distancia epicentral a la cabecera municipal habitada. Clave para evaluar el radio de afectación directa en áreas urbanas. |
| 22 | `energia_sismica_joules` | Float64 | Joules ($J$) | Derivada (Gutenberg-Richter) | Energía sísmica radiada calculada como $10^{4.8 + 1.5 M}$. Expresa la potencia física liberada por la ruptura tectónica. |
| 23 | `benioff_strain` | Float64 | Unidades de deformación | Derivada (Benioff) | Deformación sísmica acumulada ($10^{0.75 M}$). Utilizada en sismología para vigilar ciclos de carga y relajación de esfuerzos corticales. |
| 24 | `es_sismo_profundo` | Int64 (Binaria) | 0 o 1 | Derivada (SGC) | Indicador binario ($1$ si profundidad $\ge 70\text{ km}$, $0$ si es cortical $< 70\text{ km}$). Los sismos corticales generan severas aceleraciones destructivas. |
| 25 | `aceleracion_suelo_estimada_pga` | Float64 | Fracción de gravedad ($g$) | Derivada (GMPE Campbell/SGC) | Aceleración pico del terreno estimada en la cabecera municipal mediante atenuación hipocentral. |
| 26 | `tiempo_inter_evento_horas` | Float64 | Horas ($h$) | Derivada temporal | Tiempo transcurrido desde el sismo anterior en Santander. Mide la cadencia de la actividad y alerta sobre silencios o enjambres anómalos. |
| 27 | `tasa_sismicidad_30d` | Float64 | Sismos en 30 días | Derivada rodante | Frecuencia de sismos registrados en la región durante los 30 días previos. Señala aceleración sísmica. |
| 28 | `energia_acumulada_30d` | Float64 | Joules ($J$) | Derivada rodante | Suma de energía sísmica liberada en los últimos 30 días. Revela liberación masiva o contención de energía en la corteza. |
| 29 | `b_value_local` | Float64 | Adimensional | Derivada (Aki ML) | Pendiente de la ley de Gutenberg-Richter estimada en ventana móvil. Caídas en $b$ preceden sismos de mayor magnitud por estrés de esfuerzos. |
| 30 | `prioridad_riesgo_socio_sismico` | Float64 | Escala continua [0 - 100] | **VARIABLE OBJETIVO** | Índice multidimensional no lineal que conjuga la aceleración física del suelo ($PGA$), factor de profundidad, vulnerabilidad física y NBI del DANE, y exposición demográfica. |
| 31 | `categoria_riesgo` | String (Ordinal) | Bajo / Medio / Alto / Crítico | **VARIABLE OBJETIVO CLASIF.** | Clasificación ordinal de riesgo territorial para la priorización operativa de recursos de prevención y protección civil. |
