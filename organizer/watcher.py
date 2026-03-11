"""
Monitoreo de capturas de pantalla en el escritorio.
Detecta nuevos archivos que coincidan con el patrón de capturas de macOS.
"""
import os
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class ScreenshotHandler(FileSystemEventHandler):
    """Handler para eventos de nuevos archivos de captura de pantalla."""
    
    def __init__(self, callback):
        """
        Args:
            callback: Función a llamar cuando se detecta una nueva captura.
                      Recibe la ruta del archivo como argumento.
        """
        self.callback = callback
        self.processing = set()  # Evitar procesar el mismo archivo múltiples veces
        
    def is_screenshot(self, filename: str) -> bool:
        """Verifica si el archivo es una captura de pantalla de macOS."""
        # Patrón: "Captura de pantalla YYYY-MM-DD a las HH.MM.SS.png"
        return (
            filename.startswith("Captura de pantalla") and 
            filename.endswith(".png")
        )
    
    def on_created(self, event):
        """Se ejecuta cuando se crea un nuevo archivo."""
        if event.is_directory:
            return
            
        filepath = event.src_path
        filename = os.path.basename(filepath)
        
        if not self.is_screenshot(filename):
            return
            
        if filepath in self.processing:
            return
            
        self.processing.add(filepath)
        logger.info(f"Nueva captura detectada: {filename}")
        
        # Esperar a que el archivo termine de escribirse
        time.sleep(2)
        
        try:
            if os.path.exists(filepath):
                self.callback(filepath)
        except Exception as e:
            logger.error(f"Error procesando {filename}: {e}")
        finally:
            self.processing.discard(filepath)


class ScreenshotWatcher:
    """Observador del directorio Desktop para nuevas capturas."""
    
    def __init__(self, callback):
        """
        Args:
            callback: Función a llamar cuando se detecta una nueva captura.
        """
        self.desktop_path = str(Path.home() / "Desktop")
        self.handler = ScreenshotHandler(callback)
        self.observer = Observer()
        
    def start(self):
        """Inicia el monitoreo del Desktop."""
        logger.info(f"Monitoreando: {self.desktop_path}")
        self.observer.schedule(self.handler, self.desktop_path, recursive=False)
        self.observer.start()
        
    def stop(self):
        """Detiene el monitoreo."""
        self.observer.stop()
        self.observer.join()
        logger.info("Monitoreo detenido")
        
    def is_alive(self):
        """Verifica si el observador está activo."""
        return self.observer.is_alive()
