import numpy as np
import matplotlib.pyplot as plt
from time import sleep

class MPPT_PO:
    def __init__(self, step_size=0.05, max_voltage=50, min_voltage=10, sample_time=0.1):
        """
        Initialise le régulateur MPPT P&O

        Paramètres:
            step_size: Taille du pas de perturbation (Volts)
            max_voltage: Tension maximale admissible (V)
            min_voltage: Tension minimale admissible (V)
            sample_time: Temps entre chaque mise à jour (s)
        """
        self.step_size = step_size
        self.max_voltage = max_voltage
        self.min_voltage = min_voltage
        self.sample_time = sample_time

        # Variables d'état
        self.v_prev = 0
        self.p_prev = 0
        self.v_ref = min_voltage  # Tension de référence initiale

        # Historique pour le débogage
        self.history = {'v': [], 'i': [], 'p': [], 'action': []}

    def update(self, v_measured, i_measured):
        """
        Met à jour le MPPT avec les nouvelles mesures

        Args:
            v_measured: Tension mesurée (V)
            i_measured: Courant mesuré (A)

        Returns:
            Nouvelle tension de référence (V)
        """
        # Calcul de la puissance actuelle
        p_measured = v_measured * i_measured

        # Sauvegarde des données pour analyse
        self.history['v'].append(v_measured)
        self.history['i'].append(i_measured)
        self.history['p'].append(p_measured)

        # Détection du premier échantillon
        if self.p_prev == 0:
            self.v_prev = v_measured
            self.p_prev = p_measured
            self.history['action'].append('init')
            return self.v_ref

        # Calcul des variations
        delta_v = v_measured - self.v_prev
        delta_p = p_measured - self.p_prev

        # Algorithme P&O
        if delta_p > 0:
            if delta_v > 0:
                self.v_ref += self.step_size  # Augmenter encore la tension
                action = 'increase'
            else:
                self.v_ref -= self.step_size  # Diminuer la tension
                action = 'decrease'
        else:
            if delta_v > 0:
                self.v_ref -= self.step_size  # Inverser: diminuer la tension
                action = 'decrease'
            else:
                self.v_ref += self.step_size  # Inverser: augmenter la tension
                action = 'increase'

        # Limitation de la tension de référence
        self.v_ref = np.clip(self.v_ref, self.min_voltage, self.max_voltage)

        # Mise à jour des valeurs précédentes
        self.v_prev = v_measured
        self.p_prev = p_measured
        self.history['action'].append(action)

        return self.v_ref

    def plot_history(self): # Affichage des résultats
        """Visualise les performances du MPPT"""
        plt.figure(figsize=(12, 8))

        # Courbe PV théorique pour référence
        v_range = np.linspace(self.min_voltage, self.max_voltage, 100)
        pv_power = [self._simulate_pv(v)*v for v in v_range]

        plt.subplot(2, 2, 1)
        plt.plot(v_range, pv_power, 'b-', label='Courbe PV')
        plt.plot(self.history['v'], self.history['p'], 'ro-', label='Trajectoire MPPT')
        plt.xlabel('Tension (V)')
        plt.ylabel('Puissance (W)')
        plt.title('Suivi du Point de Puissance Maximale')
        plt.legend()
        plt.grid(True)

        plt.subplot(2, 2, 2)
        plt.plot(self.history['p'], 'g-')
        plt.xlabel('Itérations')
        plt.ylabel('Puissance (W)')
        plt.title('Convergence de la puissance')
        plt.grid(True)

        plt.subplot(2, 2, 3)
        plt.plot(self.history['v'], 'r-')
        plt.xlabel('Itérations')
        plt.ylabel('Tension (V)')
        plt.title('Evolution de la tension')
        plt.grid(True)

        plt.subplot(2, 2, 4)
        action_num = [1 if a == 'increase' else -1 if a == 'decrease' else 0 for a in self.history['action']]
        plt.stem(action_num)
        plt.xlabel('Itérations')
        plt.ylabel('Action (+1/-1)')
        plt.title('Décisions du MPPT')
        plt.grid(True)

        plt.tight_layout()
        plt.show()

    def _simulate_pv(self, v):
        """Fonction pour simuler un panneau PV (utilisée pour la visualisation)"""
        # Courbe PV typique avec un MPP autour de 17V
        return 5 * np.exp(-0.05*(v-17)**2)

# Simulation en temps réel
def simulate_real_time(mppt, duration=10):
    """Simule le fonctionnement en temps réel avec un panneau PV virtuel"""
    print("Démarrage de la simulation MPPT en temps réel...")
    print(f"Paramètres: step={mppt.step_size}V, Vmin={mppt.min_voltage}V, Vmax={mppt.max_voltage}V")

    # Initialisation
    v_operating = mppt.min_voltage

    for step in range(int(duration/mppt.sample_time)):
        # Simulation de la mesure du panneau PV
        i = mppt._simulate_pv(v_operating) + np.random.normal(0, 0.05)  # Ajout de bruit

        # Mise à jour du MPPT
        v_ref = mppt.update(v_operating, i)

        # Simulation de la réponse du convertisseur DC-DC
        # (On suppose qu'il atteint la tension de référence en un pas)
        v_operating = v_ref

        # Affichage progressif
        if step % 10 == 0:
            print(f"Itération {step}: V={v_operating:.2f}V, I={i:.2f}A, P={v_operating*i:.2f}W")

        sleep(mppt.sample_time)

    print("Simulation terminée")
    mppt.plot_history()

# Exemple d'utilisation
if __name__ == "__main__":
    # Création du régulateur avec des paramètres réalistes
    mppt = MPPT_PO(step_size=0.5, max_voltage=45, min_voltage=10, sample_time=0.2)

    # Lancement de la simulation
    simulate_real_time(mppt, duration=20)
