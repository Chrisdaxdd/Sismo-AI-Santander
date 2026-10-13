# %% [markdown]
# # PROYECTO HACKATHON: CATEGORÍA AVANZADA (SALA 307B)
# ## Priorización Exploratoria de Zonas de Riesgo Sísmico en Santander mediante Aprendizaje por Refuerzo
# 
# **Integrantes del Equipo:** Equipo Sala 307B  
# **Fuentes Oficiales Integradas:**  
# - Servicio Geológico Colombiano (SGC) - Catálogo Sísmico 1993 a Octubre 2026
# - Departamento Administrativo Nacional de Estadística (DANE) - Censo CNPV y NBI
# - Instituto Geográfico Agustín Codazzi (IGAC) - Cartografía y Áreas Municipales

# %%
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# %% [markdown]
# ### 1. Carga y Verificación del Dataset Unificado SGC + DANE

# %%
df = pd.read_csv("dataset_santander_unificado.csv")
df['fecha_hora_utc'] = pd.to_datetime(df['fecha_hora_utc'])
print(f"Dimensiones del dataset: {df.shape[0]:,} filas x {df.shape[1]} columnas")
print(f"Rango temporal: desde {df['fecha_hora_utc'].min()} hasta {df['fecha_hora_utc'].max()}")
df.head(3)

# %% [markdown]
# ### 2. Análisis Exploratorio de Variables Geo-Sismológicas y Vulnerabilidad

# %%
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# Distribución de Magnitudes
axes[0].hist(df['magnitud'], bins=30, color='#1f77b4', edgecolor='black', alpha=0.7)
axes[0].set_title("Distribución de Magnitudes (1993-2026)")
axes[0].set_xlabel("Magnitud")
axes[0].set_ylabel("Frecuencia")

# Distribución de Profundidades (Nido vs Cortical)
axes[1].hist(df['profundidad_km'], bins=30, color='#ff7f0e', edgecolor='black', alpha=0.7)
axes[1].axvline(70, color='red', linestyle='--', label='Límite Cortical (70 km)')
axes[1].set_title("Profundidad Focal Hipocentral (km)")
axes[1].set_xlabel("Profundidad (km)")
axes[1].legend()

# Categoría de Riesgo Socio-Sísmico
df['categoria_riesgo'].value_counts().plot(kind='bar', ax=axes[2], color='#2ca02c', edgecolor='black')
axes[2].set_title("Distribución de Categoría de Riesgo Territorial")
axes[2].set_ylabel("Conteo de Eventos")

plt.tight_layout()
plt.show()

# %% [markdown]
# ### 3. Configuración del Entorno de Aprendizaje por Refuerzo (Gymnasium)

# %%
from src.environment import SantanderSeismicEnv, ZONAS_SANTANDER
from src.rl_agent import BootstrappedEnsembleRLAgent

env_train = SantanderSeismicEnv(dataset_path="dataset_santander_unificado.csv", ventana_dias=30, split_date="2022-01-01", mode="train")
env_test = SantanderSeismicEnv(dataset_path="dataset_santander_unificado.csv", ventana_dias=30, split_date="2022-01-01", mode="test")

print(f"Macro-Zonas operativas de Santander:")
for k, v in ZONAS_SANTANDER.items():
    print(f"  Zona {k}: {v['nombre']} | Población: {v['poblacion_total']:,} hab")

# %% [markdown]
# ### 4. Entrenamiento del Agente con Ensamble Bootstrapped (B-DQN)

# %%
state_dim = env_train.observation_space.shape[0]
action_dim = env_train.action_space.n
agent = BootstrappedEnsembleRLAgent(state_dim=state_dim, action_dim=action_dim, num_models=5, lr=0.003)

# Breve demostración de entrenamiento
print("Entrenando agente en historial 1993-2021...")
for ep in range(5):
    obs, _ = env_train.reset()
    done = False
    ep_reward = 0.0
    while not done:
        dec = agent.act(obs, epsilon=0.1)
        next_obs, r, term, trunc, _ = env_train.step(dec["action"])
        agent.store_transition(obs, dec["action"], r, next_obs, term)
        agent.train_step(batch_size=32)
        ep_reward += r
        obs = next_obs
        done = term or trunc
    print(f"Episodio {ep+1} | Recompensa: {ep_reward:.2f}")

# %% [markdown]
# ### 5. Validación Temporal e Incertidumbre Cuantificada (2022 - 2026)

# %%
df_eval = pd.read_csv("resultados_validacion_temporal.csv")
print("Métricas de Validación Temporal:")
print(f"Recompensa Acumulada Final: {df_eval['recompensa_acumulada'].iloc[-1]:.2f}")
print(f"Incertidumbre Epistémica Promedio: {df_eval['incertidumbre_epistemica'].mean():.4f}")
print(f"Incertidumbre Aleatoria Promedio: {df_eval['incertidumbre_aleatoria'].mean():.4f}")

plt.figure(figsize=(10, 4))
plt.plot(df_eval['recompensa_acumulada'], color='#1f77b4', lw=2, label='Recompensa Acumulada Test')
plt.title("Desempeño del Agente en Periodo Futuro Ciego (2022-2026)")
plt.xlabel("Ventana Temporal (Meses)")
plt.ylabel("Recompensa")
plt.grid(True, alpha=0.3)
plt.legend()
plt.show()
