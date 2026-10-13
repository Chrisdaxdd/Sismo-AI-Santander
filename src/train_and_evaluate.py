"""
Script de Entrenamiento, Validación Temporal y Evaluación Comparativa del Agente RL.
Respeta el orden cronológico estricto:
- Entrenamiento: 1993 a 2021 (~28.5 años de sismicidad histórica).
- Test Temporal: 2022 a Octubre 2026 (~4.8 años de prueba ciega al futuro).
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.environment import SantanderSeismicEnv, ZONAS_SANTANDER
from src.rl_agent import BootstrappedEnsembleRLAgent

def entrenar_agente(env_train, num_episodios=15, batch_size=32):
    """Entrena el agente RL en el entorno temporal histórico."""
    print("Iniciando entrenamiento del Agente de Refuerzo en serie temporal histórica (1993 - 2021)...")
    state_dim = env_train.observation_space.shape[0]
    action_dim = env_train.action_space.n
    agent = BootstrappedEnsembleRLAgent(state_dim=state_dim, action_dim=action_dim, num_models=5, lr=0.003)

    historial_episodios = []
    
    for ep in range(num_episodios):
        obs, _ = env_train.reset()
        done = False
        recompensa_ep = 0.0
        steps = 0
        epsilon = max(0.05, 0.50 * (0.85 ** ep)) # Decaimiento de exploración

        while not done:
            decision = agent.act(obs, epsilon=epsilon)
            action = decision["action"]
            next_obs, reward, terminated, truncated, _ = env_train.step(action)
            
            agent.store_transition(obs, action, reward, next_obs, terminated)
            agent.train_step(batch_size=batch_size)
            
            recompensa_ep += reward
            obs = next_obs
            steps += 1
            done = terminated or truncated

        historial_episodios.append(recompensa_ep)
        print(f"  Episodio {ep+1:2d}/{num_episodios:2d} | Pasos: {steps:3d} | Recompensa Total: {recompensa_ep:8.2f} | Epsilon: {epsilon:.3f}")

    return agent, historial_episodios

def evaluar_baselines(env_test):
    """Evalúa dos políticas de referencia (Baseline Aleatorio y Heurístico 'Siempre Los Santos')."""
    # 1. Baseline Aleatorio
    obs, _ = env_test.reset()
    done = False
    reward_aleatorio = 0.0
    hist_aleatorio = []
    while not done:
        a = np.random.randint(0, env_test.action_space.n)
        _, r, term, trunc, info = env_test.step(a)
        reward_aleatorio += r
        hist_aleatorio.append(reward_aleatorio)
        done = term or trunc

    # 2. Baseline Heurístico (Siempre priorizar Zona 0: Mesa de Los Santos)
    obs, _ = env_test.reset()
    done = False
    reward_heuristico = 0.0
    hist_heuristico = []
    while not done:
        a = 0 # Zona 0
        _, r, term, trunc, info = env_test.step(a)
        reward_heuristico += r
        hist_heuristico.append(reward_heuristico)
        done = term or trunc

    return hist_aleatorio, hist_heuristico

def ejecutar_pipeline_completo():
    """Ejecuta el ciclo de vida completo de entrenamiento y validación temporal."""
    dataset_file = "dataset_santander_unificado.csv"
    if not os.path.exists(dataset_file):
        raise FileNotFoundError(f"Dataset '{dataset_file}' no encontrado. Ejecuta primero src.data_unification.")

    # 1. Crear entornos con división temporal estricta (Split 2022-01-01)
    env_train = SantanderSeismicEnv(dataset_path=dataset_file, ventana_dias=30, split_date="2022-01-01", mode="train")
    env_test = SantanderSeismicEnv(dataset_path=dataset_file, ventana_dias=30, split_date="2022-01-01", mode="test")

    print(f"Entorno configurado:")
    print(f"  - Ventanas de entrenamiento (1993-2021): {len(env_train.ventanas)} pasos")
    print(f"  - Ventanas de test temporal (2022-2026): {len(env_test.ventanas)} pasos")

    # 2. Entrenar el agente
    agente, historial_train = entrenar_agente(env_train, num_episodios=12)

    # 3. Validación temporal estricta en el conjunto de prueba (2022-2026)
    print("\nEvaluando en el periodo ciego futuro (2022 - 2026)...")
    eval_historial = agente.evaluate_temporal(env_test)
    df_eval = pd.DataFrame(eval_historial)
    df_eval.to_csv("resultados_validacion_temporal.csv", index=False)
    print(f"Resultados de validación temporal guardados en 'resultados_validacion_temporal.csv'.")

    # 4. Evaluación de Baselines para comparación
    hist_rand, hist_heur = evaluar_baselines(env_test)

    # 5. Métricas de desempeño final
    recompensa_final_rl = df_eval['recompensa_acumulada'].iloc[-1]
    recompensa_final_rand = hist_rand[-1] if hist_rand else 0.0
    recompensa_final_heur = hist_heur[-1] if hist_heur else 0.0

    print("\n" + "="*60)
    print("RESULTADOS DE LA VALIDACIÓN TEMPORAL (2022 - 2026):")
    print(f"  - Agente RL (Ensemble B-DQN) Recompensa Acumulada : {recompensa_final_rl:8.2f}")
    print(f"  - Baseline Heurístico (Fijo Los Santos)         : {recompensa_final_heur:8.2f}")
    print(f"  - Baseline Aleatorio                             : {recompensa_final_rand:8.2f}")
    print(f"  - Incertidumbre Epistémica Media (Varianza Q)    : {df_eval['incertidumbre_epistemica'].mean():8.4f}")
    print(f"  - Incertidumbre Aleatoria Media (Entropía Softmax): {df_eval['incertidumbre_aleatoria'].mean():8.4f}")
    print("="*60)

    # 6. Generación de Gráficos de Validación e Incertidumbre con la Paleta Oficial
    print("\nGenerando figuras de validación temporal e incertidumbre con la paleta oficial...")
    plt.figure(figsize=(12, 5), facecolor="#ECFFD3")
    
    # Subplot 1: Trayectoria de Recompensa Temporal
    ax1 = plt.subplot(1, 2, 1)
    ax1.set_facecolor("#FFFFFF")
    pasos_test = range(len(df_eval))
    ax1.plot(pasos_test, df_eval['recompensa_acumulada'], label="Agente RL (Ensemble B-DQN)", color="#2D7D21", lw=2.8)
    ax1.plot(range(len(hist_heur)), hist_heur, label="Baseline Heurístico (Los Santos)", color="#5D9E4E", linestyle="--", lw=2.0)
    ax1.plot(range(len(hist_rand)), hist_rand, label="Baseline Aleatorio", color="#7A7A7A", linestyle=":", lw=1.5)
    ax1.set_title("Validación Temporal: Recompensa Acumulada (2022-2026)", fontsize=11, fontweight="bold", color="#153311")
    ax1.set_xlabel("Ventana Temporal (Meses)", fontweight="bold")
    ax1.set_ylabel("Recompensa Acumulada", fontweight="bold")
    ax1.grid(True, alpha=0.3, color="#8DBE7A")
    ax1.legend()

    # Subplot 2: Incertidumbre Epistémica vs Aleatoria
    ax2 = plt.subplot(1, 2, 2)
    ax2.set_facecolor("#FFFFFF")
    ax2.plot(pasos_test, df_eval['incertidumbre_epistemica'], label="Incertidumbre Epistémica (Var Q)", color="#2D7D21", lw=2.4)
    ax2.plot(pasos_test, df_eval['incertidumbre_aleatoria'], label="Incertidumbre Aleatoria (Entropía)", color="#8DBE7A", lw=2.0, linestyle="-.")
    ax2.set_title("Evolución Temporal de la Incertidumbre", fontsize=11, fontweight="bold", color="#153311")
    ax2.set_xlabel("Ventana Temporal (Meses)", fontweight="bold")
    ax2.set_ylabel("Nivel de Incertidumbre", fontweight="bold")
    ax2.grid(True, alpha=0.3, color="#8DBE7A")
    ax2.legend()

    plt.tight_layout()
    plt.savefig("grafica_validacion_temporal_incertidumbre.png", dpi=200)
    plt.close()
    print("Figura guardada exitosamente como 'grafica_validacion_temporal_incertidumbre.png'.")

    # Guardar pesos del ensamble
    pesos = []
    for m in agente.models:
        pesos.append({"W1": m.W1.tolist(), "b1": m.b1.tolist(), "W2": m.W2.tolist(), "b2": m.b2.tolist()})
    with open("modelo_rl_ensemble_pesos.json", "w") as fp:
        json.dump(pesos, fp)
    print("Pesos del ensamble guardados en 'modelo_rl_ensemble_pesos.json'.")

if __name__ == '__main__':
    ejecutar_pipeline_completo()
