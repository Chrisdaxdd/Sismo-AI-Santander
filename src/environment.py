"""
Entorno de Refuerzo Sismo-Territorial: SantanderSeismicEnv.
Implementa la interfaz estándar de Gymnasium para modelar el proceso de decisión de Markov (MDP)
de priorización exploratoria y preventiva de recursos ante riesgo sísmico en Santander.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

# Definición de macro-zonas operativas de gestión del riesgo en Santander
ZONAS_SANTANDER = {
    0: {
        "nombre": "Mesa de Los Santos / Guanentá",
        "municipios": ["LOS SANTOS", "CEPITA", "JORDAN", "ARATOCA", "SAN GIL", "VILLANUEVA", "CURITI", "BARICHARA", "PINCHOTE", "MOGOTES"],
        "centroide": [6.75, -73.08],
        "vulnerabilidad_base": 0.32,
        "poblacion_total": 135000,
        "descripcion": "Epicentro del Nido Sísmico de Bucaramanga; altísima tasa de sismicidad intermedia (~150 km)."
    },
    1: {
        "nombre": "Área Metropolitana de Bucaramanga",
        "municipios": ["BUCARAMANGA", "FLORIDABLANCA", "GIRON", "PIEDECUESTA", "LEBRIJA"],
        "centroide": [7.09, -73.13],
        "vulnerabilidad_base": 0.18,
        "poblacion_total": 1386100,
        "descripcion": "Máxima concentración demográfica e infraestructura crítica; vulnerable a sismos corticales y amplificación de ondas."
    },
    2: {
        "nombre": "Magdalena Medio / Mares",
        "municipios": ["BARRANCABERMEJA", "SAN VICENTE DE CHUCURI", "BETULIA", "SABANA DE TORRES", "PUERTO PARRA"],
        "centroide": [7.05, -73.65],
        "vulnerabilidad_base": 0.38,
        "poblacion_total": 314000,
        "descripcion": "Complejo petrolero y energético; fallamiento cortical activo (Falla La Salina) y depósitos aluviales."
    },
    3: {
        "nombre": "Soto Norte",
        "municipios": ["CALIFORNIA", "VETAS", "MATANZA", "SURATA", "CHARTA", "TONA"],
        "centroide": [7.31, -72.98],
        "vulnerabilidad_base": 0.34,
        "poblacion_total": 24100,
        "descripcion": "Zona montañosa minera de alta pendiente; Falla Bucaramanga-Santa Marta con riesgo de remoción en masa."
    },
    4: {
        "nombre": "Comunera / Carare-Opón / Vélez",
        "municipios": ["SOCORRO", "BARBOSA", "VELEZ", "CIMITARRA", "EL CARMEN DE CHUCURI", "SANTA HELENA DEL OPON", "OIBA", "CONTRATACION", "SIMACOTA", "LANDAZURI", "LA BELLEZA"],
        "centroide": [6.35, -73.55],
        "vulnerabilidad_base": 0.42,
        "poblacion_total": 185000,
        "descripcion": "Falla del Suárez; alta vulnerabilidad en viviendas de tapia pisada y adobe no reforzado."
    }
}

class SantanderSeismicEnv(gym.Env):
    """
    Entorno de Simulación de Decisiones Territoriales de Riesgo Sísmico en Santander.
    
    Estado (S_t): Vector continuo de características espaciotemporales de las 5 macro-zonas:
      [tasa_sismos_30d_i, max_mag_30d_i, energia_acum_log_i, prof_media_i, b_value_i, silencio_dias_i, vulnerabilidad_i, poblacion_log_i] para i en [0..4]
      Dimensión = 5 zonas * 8 variables = 40 dimensiones continuas.
      
    Acción (A_t): Selección discreta de la macro-zona a priorizar para inspección y alerta (0 a 4).
    
    Recompensa (R_t):
      Premia proteger zonas donde ocurren sismos de alto impacto en la ventana t+1.
      Penaliza falsas alarmas (recursos desperdiciados) y penaliza severamente desatenciones de sismos críticos.
      Añade un bono intrínseco de exploración para zonas con acumulación de silencio sísmico.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, dataset_path="dataset_santander_unificado.csv", ventana_dias=30, split_date=None, mode="train"):
        super().__init__()
        self.num_zonas = 5
        self.features_per_zone = 8
        self.ventana_dias = ventana_dias
        self.mode = mode

        # Cargar y preparar dataset
        df = pd.read_csv(dataset_path)
        df['fecha_hora_utc'] = pd.to_datetime(df['fecha_hora_utc'])
        df = df.sort_values('fecha_hora_utc').reset_index(drop=True)

        # Mapear cada evento a una macro-zona
        df['zona_id'] = df['municipio_normalizado'].apply(self._asignar_zona)
        
        # Filtro temporal para Train / Test sin fugas
        split_dt = pd.to_datetime(split_date if split_date else "2022-01-01")
        if mode == "train":
            df = df[df['fecha_hora_utc'] < split_dt].reset_index(drop=True)
        else:
            df = df[df['fecha_hora_utc'] >= split_dt].reset_index(drop=True)

        self.df = df
        
        # Construir secuencia de ventanas temporales
        fecha_min = df['fecha_hora_utc'].min()
        fecha_max = df['fecha_hora_utc'].max()
        self.ventanas = pd.date_range(start=fecha_min, end=fecha_max, freq=f"{ventana_dias}D")
        
        # Espacio de Estados: 40 variables continuas normalizadas
        self.observation_space = spaces.Box(
            low=-5.0, high=10.0, shape=(self.num_zonas * self.features_per_zone,), dtype=np.float32
        )
        
        # Espacio de Acciones: Priorizar una de las 5 macro-zonas
        self.action_space = spaces.Discrete(self.num_zonas)
        
        self.current_step = 0
        self.max_steps = max(len(self.ventanas) - 2, 1)

    def _asignar_zona(self, municipio):
        """Asigna un municipio normalizado a una de las 5 macro-zonas de Santander."""
        for z_id, data in ZONAS_SANTANDER.items():
            if municipio in data["municipios"]:
                return z_id
        # Fallback geográfico: Mesa de Los Santos si no coincide
        return 0

    def _construir_estado(self, fecha_inicio, fecha_fin):
        """Construye el vector de estado para la ventana temporal dada."""
        mask = (self.df['fecha_hora_utc'] >= fecha_inicio) & (self.df['fecha_hora_utc'] < fecha_fin)
        df_win = self.df[mask]

        estado = []
        for z_id in range(self.num_zonas):
            z_data = ZONAS_SANTANDER[z_id]
            df_z = df_win[df_win['zona_id'] == z_id]
            
            # 1. Tasa de sismos (log1p)
            tasa = np.log1p(len(df_z))
            
            # 2. Magnitud máxima reciente
            max_mag = df_z['magnitud'].max() if len(df_z) > 0 else 1.0
            
            # 3. Energía sísmica acumulada en escala logarítmica
            energia_log = np.log10(df_z['energia_sismica_joules'].sum() + 1e3) if len(df_z) > 0 else 3.0
            
            # 4. Profundidad focal media normalizada (0 = superficial, 1 = profundo)
            prof_media = (df_z['profundidad_km'].mean() / 150.0) if len(df_z) > 0 else 0.5
            
            # 5. b-value local promedio
            b_val = df_z['b_value_local'].mean() if len(df_z) > 0 else 1.0
            
            # 6. Silencio sísmico en días desde el último sismo en la zona
            if len(df_z) > 0:
                silencio_dias = (fecha_fin - df_z['fecha_hora_utc'].max()).total_seconds() / 86400.0
            else:
                silencio_dias = self.ventana_dias
            silencio_norm = min(silencio_dias / 30.0, 5.0)
            
            # 7. Vulnerabilidad física base DANE
            vuln = z_data["vulnerabilidad_base"]
            
            # 8. Población expuesta en escala logarítmica
            pob_log = np.log10(z_data["poblacion_total"]) / 6.0
            
            estado.extend([tasa, max_mag, energia_log, prof_media, b_val, silencio_norm, vuln, pob_log])
            
        return np.array(estado, dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        fecha_inicio = self.ventanas[self.current_step]
        fecha_fin = self.ventanas[self.current_step + 1]
        obs = self._construir_estado(fecha_inicio, fecha_fin)
        info = {
            "fecha_inicio": str(fecha_inicio),
            "fecha_fin": str(fecha_fin),
            "step": self.current_step
        }
        return obs, info

    def step(self, action):
        """
        Ejecuta una acción de priorización territorial y evalúa el impacto en la ventana siguiente (t+1).
        """
        assert self.action_space.contains(action), f"Acción inválida: {action}"
        
        # Ventana de evaluación futura (t+1)
        fecha_eval_inicio = self.ventanas[self.current_step + 1]
        fecha_eval_fin = self.ventanas[self.current_step + 2]
        
        mask_futuro = (self.df['fecha_hora_utc'] >= fecha_eval_inicio) & (self.df['fecha_hora_utc'] < fecha_eval_fin)
        df_futuro = self.df[mask_futuro]
        
        # Métricas reales de sismicidad ocurrida en cada zona durante la ventana futura
        riesgos_reales = {}
        max_mags_reales = {}
        for z_id in range(self.num_zonas):
            df_fz = df_futuro[df_futuro['zona_id'] == z_id]
            if len(df_fz) > 0:
                riesgos_reales[z_id] = df_fz['prioridad_riesgo_socio_sismico'].mean()
                max_mags_reales[z_id] = df_fz['magnitud'].max()
            else:
                riesgos_reales[z_id] = 0.0
                max_mags_reales[z_id] = 0.0
        
        # Cálculo de la Recompensa (Reward Engineering con fundamentación geofísica):
        # 1. Protección de la zona elegida:
        riesgo_elegido = riesgos_reales[action]
        mag_elegida = max_mags_reales[action]
        
        reward = 0.0
        
        # Recompensa por detección de amenaza y protección preventiva
        if mag_elegida >= 3.8:
            reward += 15.0 * (mag_elegida - 3.0) + (riesgo_elegido / 5.0)
        elif mag_elegida >= 2.5:
            reward += 5.0 + (riesgo_elegido / 10.0)
        else:
            # Penalización por falsa alarma (costo de movilización preventiva innecesaria)
            reward -= 3.0
            
        # 2. Penalización severa por desatención de eventos críticos en zonas NO priorizadas
        for z_id in range(self.num_zonas):
            if z_id != action:
                mag_otro = max_mags_reales[z_id]
                riesgo_otro = riesgos_reales[z_id]
                if mag_otro >= 4.0:
                    reward -= 20.0 * (mag_otro - 3.5)
                elif riesgo_otro >= 50.0:
                    reward -= 8.0

        # 3. Bono de exploración por atender zonas con silencio sísmico acumulado
        estado_prev = self._construir_estado(self.ventanas[self.current_step], self.ventanas[self.current_step + 1])
        # Indice de silencio para la zona action está en pos: action * 8 + 5
        silencio_action = estado_prev[action * self.features_per_zone + 5]
        if silencio_action > 2.0:
            reward += 2.5 * silencio_action

        # Avanzar el paso
        self.current_step += 1
        terminated = (self.current_step >= self.max_steps)
        truncated = False
        
        # Siguiente estado (S_t+1)
        next_obs = self._construir_estado(fecha_eval_inicio, fecha_eval_fin)
        
        info = {
            "zona_priorizada": ZONAS_SANTANDER[action]["nombre"],
            "riesgo_zona_elegida": float(riesgo_elegido),
            "max_mag_elegida": float(mag_elegida),
            "fecha_evaluacion": str(fecha_eval_inicio)[:10],
            "reward": float(reward)
        }
        
        return next_obs, reward, terminated, truncated, info
