# SISMO-AI: Priorización Territorial del Riesgo Sísmico en Santander mediante Aprendizaje por Refuerzo

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![Gymnasium](https://img.shields.io/badge/Gymnasium-RL%20Env-green.svg)](https://gymnasium.farama.org/)
[![Datos Oficiales](https://img.shields.io/badge/Fuentes-SGC%20%7C%20DANE%20%7C%20IGAC-00D9FF.svg)](#fuentes-oficiales)

Repositorio oficial del proyecto desarrollado para la **Categoría Avanzada (Sala 307B)** del Reto Universitario de Sismicidad y Analítica Territorial en el departamento de Santander, Colombia.

El sistema implementa un agente autónomo de **Aprendizaje por Refuerzo (Reinforcement Learning)** que optimiza la toma de decisiones secuenciales para la priorización y despliegue preventivo de recursos de protección civil y monitoreo acelerográfico alrededor del **Nido Sísmico de Bucaramanga (Mesa de Los Santos)** y fallas corticales activas.

---

## Aspectos Destacados del Sistema

1. **100% Datos Oficiales Reales (Cero Datos Sintéticos):**
   - **Catálogo Sísmico Principal:** 199,013 eventos sísmicos registrados por el **Servicio Geológico Colombiano (SGC)** desde el 01 de junio de 1993 hasta el 13 de octubre de 2026.
   - **Unificación de 2 Periodos:** Integración y homogeneización estructural de los periodos 1993–Feb 2018 y Mar 2018–Oct 2026 mediante un parser robusto XML que supera fallos de librerías convencionales.
   - **Integración Multifuente Secundaria:** Cruce de cada sismo con los 87 municipios de Santander del **DANE (Censo CNPV, NBI % y vulnerabilidad de vivienda en tapia/bahareque)** y centroides cartográficos del **IGAC**.
2. **Modelo Obligatorio de Aprendizaje por Refuerzo (Categoría Avanzada):**
   - Entorno estocástico personalizado conforme al estándar de **Farama Gymnasium** (`SantanderSeismicEnv`).
   - Espacio de estados continuo $S_t \in \mathbb{R}^{40}$ (8 variables sismológicas y demográficas por macro-zona).
   - Espacio de acciones discretas $A_t \in \{0, 1, 2, 3, 4\}$ (Asignación territorial de recursos).
   - Ingeniería de recompensas con penalizaciones por falsas alarmas y desatención, e incentivos por protección de eventos destructivos ($M \ge 3.8$) y exploración de lagunas sísmicas.
3. **Variable Objetivo No-Lineal y Compuesta:**
   - Cumplimiento de la restricción de la rúbrica: no es calculable mediante una ecuación simple cerrada.
   - A nivel de control: la variable es la **política secuencial óptima $\pi^*(s)$**.
   - A nivel de dataset: el índice `prioridad_riesgo_socio_sismico` acopla leyes de atenuación física GMPE (Campbell), amortiguamiento exponencial de foco hipocentral $\exp(-h/70)$, deformación de Benioff y la curva de vulnerabilidad socioeconómica del DANE.
4. **Cuantificación Matemática de Incertidumbre:**
   - **Incertidumbre Epistémica ($\sigma^2_Q$):** Varianza del ensamble **Bootstrapped DQN ($M=5$ cabezas neuronales)** por escasez de datos en fallas lentas.
   - **Incertidumbre Aleatoria ($\mathcal{H}$):** Entropía de Boltzmann de la política ante la naturaleza estocástica intrínseca de la litosfera.
5. **Validación Cronológica Ciega (Walk-Forward Zero Data Leakage):**
   - **Entrenamiento:** Ventanas de 30 días de 1993 a 2021 (349 ventanas).
   - **Prueba Ciega:** 59 ventanas de 2022 a 2026.
   - **Resultado:** Ensamble RL (+1,326.93 de recompensa acumulada) vs Baseline Heurístico (+1,326.93) vs Baseline Aleatorio (-693.89).

---

## Estructura del Repositorio

```text
├── app.py                                    # Dashboard interactivo Streamlit con visor geoespacial y RL en vivo
├── dashboard_seismico_ai.html                # Interfaz gráfica standalone completa (HTML5 + Tailwind + SVG)
├── cuaderno_interactivo_analisis.py          # Cuaderno reproducible con celdas ejecutables (# %%)
├── dataset_santander_unificado.csv           # Dataset unificado oficial (199,013 filas x 39 columnas)
├── diccionario_datos.md                      # Diccionario oficial detallado de las 28 variables justificadas
├── fuentes_oficiales.md                      # Metadatos, URLs oficiales, periodos y filtros aplicados
├── modelo_rl_ensemble_pesos.json             # Pesos entrenados de las 5 cabezas del ensamble Bootstrapped DQN
├── resultados_validacion_temporal.csv        # Bitácora cronológica paso a paso de las 59 ventanas de test
├── grafica_validacion_temporal_incertidumbre.png # Gráfico científico de alta resolución de la validación
├── requirements.txt                          # Dependencias reproducibles del entorno Python
├── .gitignore                                # Exclusiones de archivos temporales y entornos virtuales
└── src/
    ├── dane_santander.py                     # Diccionario DIVIPOLA, población CNPV y NBI de Santander
    ├── data_unification.py                   # Pipeline ETL de unificación de los dos esquemas del SGC
    ├── environment.py                        # Entorno MDP Gymnasium (SantanderSeismicEnv)
    ├── rl_agent.py                           # Agente BootstrappedEnsembleRLAgent (M=5) con incertidumbre
    └── train_and_evaluate.py                 # Script de entrenamiento y evaluación cronológica ciega
```

---

## Formulación del Proceso de Decisión de Markov (MDP)

El territorio santandereano se discretiza en 5 macro-zonas geoeconómicas:
- **Zona 0:** Mesa de Los Santos / Guanentá (Epicentro del Nido Sísmico, sismicidad profunda a ~150 km).
- **Zona 1:** Área Metropolitana de Bucaramanga (Mayor densidad demográfica y concentración de infraestructura).
- **Zona 2:** Magdalena Medio / Mares (Falla cortical La Salina, refinería y sector petrolero).
- **Zona 3:** Soto Norte (Falla Bucaramanga-Santa Marta, cuencas mineras e hidrográficas).
- **Zona 4:** Comunera / Carare / Vélez (Falla del Suárez, alta vulnerabilidad habitacional en tapia pisada).

### 1. Vector de Estados ($S_t \in \mathbb{R}^{40}$)
En cada ventana temporal $t$ (30 días), el estado condensa 8 variables por cada una de las 5 zonas:
$$\mathbf{s}_{t, i} = \left[ \log(1 + N_i), \; \max(M_i), \; \log_{10}(\Sigma E_i), \; \frac{h_{\text{mean}, i}}{150}, \; b_{\text{GR}, i}, \; \text{Silencio}_i, \; \text{Vuln}_i, \; \frac{\log_{10}(\text{Pob}_i)}{6} \right]$$

### 2. Función de Recompensa
$$R_t = R_{\text{protección}}(M \ge 3.8) - C_{\text{falsa\_alarma}} - C_{\text{desatención}}(M_{\text{crítico}}) + B_{\text{exploración}}(\text{silencio})$$

Donde:
- **Protección:** $+15.0 \times (M - 3.0)$ si la zona elegida sufre un sismo de magnitud relevante.
- **Desatención:** $-20.0 \times (M - 3.5)$ por no proteger otra zona que registró un sismo crítico.
- **Falsa Alarma:** $-3.0$ por movilización innecesaria de recursos si no hubo actividad sísmica.
- **Exploración de Brecha:** $+2.5 \times \text{Silencio}$ por inspeccionar zonas con silencio sísmico anómalo.

---

## Instalación y Reproducción Local

### Prerrequisitos
- Python 3.10 o superior instalado.

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Chrisdaxdd/Sismo-AI-Santander.git
cd Sismo-AI-Santander
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar el Pipeline de Datos (Opcional - el dataset ya viene unificado)
```bash
python src/data_unification.py
```

### 4. Entrenar y Validar el Agente RL
```bash
python src/train_and_evaluate.py
```

### 5. Lanzar la Plataforma Web Interactiva
```bash
python -m streamlit run app.py
```
La aplicación se abrirá en `http://localhost:8501`.

Alternativamente, puede abrir directamente el dashboard visual en su navegador sin dependencias:
```bash
start dashboard_seismico_ai.html
```

---

## Fuentes Oficiales y Citas
1. **Servicio Geológico Colombiano (SGC) - RSNC:** Catálogo Sísmico Nacional (1993 a 2026). [https://www.sgc.gov.co](https://www.sgc.gov.co) | [http://sish.sgc.gov.co/](http://sish.sgc.gov.co/)
2. **DANE:** Censo Nacional de Población y Vivienda (CNPV), NBI Municipal y Proyecciones 2026. [https://www.dane.gov.co](https://www.dane.gov.co)
3. **IGAC:** Geoportal oficial de cartografía vectorial y áreas municipales. [https://www.igac.gov.co](https://www.igac.gov.co)
4. **USGS:** ANSS Comprehensive Earthquake Catalog (ComCat) vía FDSN API. [https://earthquake.usgs.gov](https://earthquake.usgs.gov)

Para consultar el diccionario completo de las 28 variables justificadas, revise [`diccionario_datos.md`](diccionario_datos.md).  
Para consultar los filtros geográficos y criterios de calidad, revise [`fuentes_oficiales.md`](fuentes_oficiales.md).

---

## Licencia
Este proyecto fue desarrollado con fines académicos y de investigación científica bajo Licencia MIT.
