"""
Módulo del Agente de Aprendizaje por Refuerzo con Cuantificación de Incertidumbre.
Implementa un Ensemble Bootstrapped Q-Learning Network (B-DQN) con M estimadores neuronales
independientes para estimar el valor Q, cuantificar incertidumbre epistémica (desacuerdo del ensamble)
e incertidumbre aleatoria (entropía de Boltzmann).
"""

import numpy as np

class EnsembleQNetwork:
    """Red Neuronal de 2 capas completamente conectadas en NumPy con optimizador Adam."""
    def __init__(self, state_dim, action_dim, hidden_dim=64, lr=0.003, seed=42):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.lr = lr
        rng = np.random.RandomState(seed)

        # Inicialización He (Kaiming) para ReLU
        self.W1 = rng.randn(state_dim, hidden_dim) * np.sqrt(2.0 / state_dim)
        self.b1 = np.zeros(hidden_dim)
        self.W2 = rng.randn(hidden_dim, action_dim) * np.sqrt(2.0 / hidden_dim)
        self.b2 = np.zeros(action_dim)

        # Parámetros del optimizador Adam
        self.mW1, self.vW1 = np.zeros_like(self.W1), np.zeros_like(self.W1)
        self.mb1, self.vb1 = np.zeros_like(self.b1), np.zeros_like(self.b1)
        self.mW2, self.vW2 = np.zeros_like(self.W2), np.zeros_like(self.W2)
        self.mb2, self.vb2 = np.zeros_like(self.b2), np.zeros_like(self.b2)
        self.beta1 = 0.9
        self.beta2 = 0.999
        self.eps = 1e-8
        self.t = 0

    def forward(self, state):
        """Forward pass que devuelve los valores Q para todas las acciones."""
        # estado: (batch_size, state_dim) o (state_dim,)
        s = np.atleast_2d(state)
        self.z1 = np.dot(s, self.W1) + self.b1
        self.a1 = np.maximum(0.0, self.z1) # ReLU
        q_vals = np.dot(self.a1, self.W2) + self.b2
        return q_vals

    def train_step(self, states, actions, targets):
        """Actualización de pesos por gradiente descendente con Adam."""
        s = np.atleast_2d(states)
        batch_size = s.shape[0]
        
        # Forward
        z1 = np.dot(s, self.W1) + self.b1
        a1 = np.maximum(0.0, z1)
        q_vals = np.dot(a1, self.W2) + self.b2

        # Error de predicción en la acción seleccionada
        grad_out = np.zeros_like(q_vals)
        for i in range(batch_size):
            grad_out[i, actions[i]] = (q_vals[i, actions[i]] - targets[i])

        # Backpropagation
        dW2 = np.dot(a1.T, grad_out) / batch_size
        db2 = np.sum(grad_out, axis=0) / batch_size
        
        da1 = np.dot(grad_out, self.W2.T)
        dz1 = da1 * (z1 > 0.0) # Derivada de ReLU
        dW1 = np.dot(s.T, dz1) / batch_size
        db1 = np.sum(dz1, axis=0) / batch_size

        # Actualización Adam
        self.t += 1
        for param, grad, m, v in [
            (self.W1, dW1, self.mW1, self.vW1),
            (self.b1, db1, self.mb1, self.vb1),
            (self.W2, dW2, self.mW2, self.vW2),
            (self.b2, db2, self.mb2, self.vb2)
        ]:
            m[:] = self.beta1 * m + (1.0 - self.beta1) * grad
            v[:] = self.beta2 * v + (1.0 - self.beta2) * (grad ** 2)
            m_hat = m / (1.0 - self.beta1 ** self.t)
            v_hat = v / (1.0 - self.beta2 ** self.t)
            param -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

class BootstrappedEnsembleRLAgent:
    """
    Agente de Aprendizaje por Refuerzo con Ensamble Bootstrapped (B-DQN).
    Integra M redes neuronales para estimar:
    1. Política óptima pi*(a|s)
    2. Incertidumbre Epistémica (Varianza inter-modelos en Q)
    3. Incertidumbre Aleatoria (Entropía Softmax de la acción)
    """
    def __init__(self, state_dim=40, action_dim=5, num_models=5, gamma=0.92, lr=0.003, seed=42):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.num_models = num_models
        self.gamma = gamma
        self.rng = np.random.RandomState(seed)

        # Ensamble de M estimadores Q independientes
        self.models = [
            EnsembleQNetwork(state_dim, action_dim, hidden_dim=64, lr=lr, seed=seed + i * 17)
            for i in range(num_models)
        ]
        
        # Buffer de experiencia con máscaras bootstrap
        self.buffer = []
        self.buffer_size = 2000

    def act(self, state, epsilon=0.05, temperature=1.0):
        """
        Selecciona una acción y computa las incertidumbres de predicción.
        Retorna:
          - action: acción elegida (argmax Q o exploración)
          - q_mean: vector de valores Q medios para cada acción
          - epistemic_unc: varianza de Q entre modelos para la acción elegida
          - aleatoric_unc: entropía de la distribución softmax de acciones
          - q_all: predicciones individuales de cada red en el ensamble
        """
        # Evaluar cada modelo del ensamble
        q_preds = np.array([m.forward(state)[0] for m in self.models]) # Forma: (M, action_dim)
        q_mean = np.mean(q_preds, axis=0) # (action_dim,)
        q_var = np.var(q_preds, axis=0)   # (action_dim,)

        # Cálculo de Incertidumbre Aleatoria (Entropía Softmax)
        scaled_q = (q_mean - np.max(q_mean)) / max(temperature, 0.01)
        exp_q = np.exp(scaled_q)
        probs = exp_q / np.sum(exp_q)
        aleatoric_entropy = -np.sum(probs * np.log(np.maximum(probs, 1e-9)))

        # Selección de acción epsilon-greedy sobre la media del ensamble
        if self.rng.rand() < epsilon:
            action = self.rng.randint(0, self.action_dim)
        else:
            action = int(np.argmax(q_mean))

        epistemic_variance = float(q_var[action])

        return {
            "action": action,
            "q_mean": q_mean,
            "q_variance_action": epistemic_variance,
            "q_variance_all": q_var,
            "aleatoric_entropy": float(aleatoric_entropy),
            "probs": probs,
            "q_all_models": q_preds
        }

    def store_transition(self, state, action, reward, next_state, done):
        """Almacena una transición con máscara bootstrap (cada modelo muestrea con prob p=0.7)."""
        mask = self.rng.binomial(1, 0.7, size=self.num_models)
        self.buffer.append((state, action, reward, next_state, done, mask))
        if len(self.buffer) > self.buffer_size:
            self.buffer.pop(0)

    def train_step(self, batch_size=32):
        """Actualiza el ensamble usando muestras del buffer de repetición."""
        if len(self.buffer) < batch_size:
            return 0.0

        indices = self.rng.choice(len(self.buffer), batch_size, replace=False)
        batch = [self.buffer[idx] for idx in indices]

        states = np.array([b[0] for b in batch])
        actions = np.array([b[1] for b in batch])
        rewards = np.array([b[2] for b in batch])
        next_states = np.array([b[3] for b in batch])
        dones = np.array([b[4] for b in batch])
        masks = np.array([b[5] for b in batch]) # (batch_size, num_models)

        # Actualizar cada modelo con su subconjunto bootstrap
        for m_idx, model in enumerate(self.models):
            # Q-learning TD Target: y = r + gamma * max Q(s')
            next_q = model.forward(next_states)
            max_next_q = np.max(next_q, axis=1)
            targets = rewards + (1.0 - dones) * self.gamma * max_next_q

            # Filtrar por máscara bootstrap
            m_mask = masks[:, m_idx] == 1
            if np.sum(m_mask) > 0:
                model.train_step(states[m_mask], actions[m_mask], targets[m_mask])

    def evaluate_temporal(self, env):
        """
        Ejecuta la evaluación respetando estrictamente el orden temporal.
        Retorna la trayectoria de decisiones, recompensas e incertidumbres.
        """
        obs, info = env.reset()
        done = False
        
        historial = []
        recompensa_acumulada = 0.0
        
        while not done:
            decision = self.act(obs, epsilon=0.0) # Modo inferencia pura
            action = decision["action"]
            
            next_obs, reward, terminated, truncated, step_info = env.step(action)
            recompensa_acumulada += reward
            
            historial.append({
                "step": env.current_step,
                "fecha": step_info["fecha_evaluacion"],
                "accion_zona_id": action,
                "zona_priorizada": step_info["zona_priorizada"],
                "reward": reward,
                "recompensa_acumulada": recompensa_acumulada,
                "riesgo_zona_elegida": step_info["riesgo_zona_elegida"],
                "max_mag_elegida": step_info["max_mag_elegida"],
                "incertidumbre_epistemica": decision["q_variance_action"],
                "incertidumbre_aleatoria": decision["aleatoric_entropy"],
                "q_mean_elegida": float(decision["q_mean"][action])
            })
            
            obs = next_obs
            done = terminated or truncated

        return historial
