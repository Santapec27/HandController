from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject
from config import Config, get_resource_path
import os

class TrayApp(QObject):
    def __init__(self, on_exit_callback, on_settings_callback):
        super().__init__()
        self.on_exit_callback = on_exit_callback
        self.on_settings_callback = on_settings_callback
        
        self.icon = QSystemTrayIcon()
        
        # Load icon
        icon_path = get_resource_path('assets/icon.ico')
        if os.path.exists(icon_path):
            self.icon.setIcon(QIcon(icon_path))
        else:
            # Fallback if no icon
            pass
            
        self.icon.setToolTip("HandController")
        
        # Create menu
        self.menu = QMenu()
        
        self.toggle_action = QAction("Tracking Activo", self.menu)
        self.toggle_action.setCheckable(True)
        self.toggle_action.setChecked(Config.is_tracking())
        self.toggle_action.triggered.connect(self.toggle_tracking)
        self.menu.addAction(self.toggle_action)
        
        self.settings_action = QAction("Panel de Evolución", self.menu)
        self.settings_action.triggered.connect(self.on_settings_callback)
        self.menu.addAction(self.settings_action)
        
        self.exit_action = QAction("Salir", self.menu)
        self.exit_action.triggered.connect(self.exit_app)
        self.menu.addAction(self.exit_action)
        
        self.icon.setContextMenu(self.menu)
        self.icon.show()
        
        self.icon.showMessage("Hand Controller", "Iniciado en segundo plano", QSystemTrayIcon.MessageIcon.Information, 2000)

    def toggle_tracking(self, checked):
        Config.set_tracking(checked)
        state_str = "activado" if checked else "pausado"
        self.icon.showMessage("Hand Controller", f"El seguimiento de gestos ha sido {state_str}.", QSystemTrayIcon.MessageIcon.Information, 2000)

    def exit_app(self):
        self.icon.hide()
        if self.on_exit_callback:
            self.on_exit_callback()
