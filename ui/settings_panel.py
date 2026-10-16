import sys
import json
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import get_resource_path

class EvolutionPanel(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Panel de Evolución - HandController")
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        title = QLabel("PERFIL DE MOVIMIENTO")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        self.stats_label = QLabel("Cargando estadísticas...")
        self.stats_label.setFont(QFont("Arial", 12))
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_label)
        
        # Heatmap mock
        heatmap_lbl = QLabel("[Heatmap de precisión generado por ML - Próximamente]")
        heatmap_lbl.setStyleSheet("background-color: #333; color: white; padding: 50px;")
        heatmap_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heatmap_lbl)
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.load_profile()
        
    def load_profile(self):
        profile_path = get_resource_path('.agprofile')
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                data = json.load(f)
                
            optimized = data.get('optimized_gestures_count', 0)
            avg_v = data.get('avg_velocity', 0)
            alpha = data.get('ema_alpha', 0.5)
            
            text = (
                f"Gestos Optimizados: {optimized}\n"
                f"Velocidad Promedio: {avg_v:.2f} px/s\n"
                f"Suavizado Adaptativo (Alpha): {alpha:.2f}"
            )
            self.stats_label.setText(text)
        else:
            self.stats_label.setText("No hay suficientes datos de perfil aún.")

def show_evolution_panel():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    panel = EvolutionPanel()
    panel.show()
    # Don't exec if we are in a background thread without a main event loop,
    # but we will likely run this via a subprocess or emit a signal to the tray app.
    # For a tray app, it's safer to spawn it as a separate process or in the main loop.
    app.exec()
