#!/usr/bin/env python3
"""
Agente Organizador de Capturas de Pantalla
==========================================

Este agente monitorea el escritorio en busca de nuevas capturas de pantalla,
las analiza usando Ollama con visión (llava), y las renombra automáticamente
según su contenido.

Uso:
    python main.py          # Ejecutar en primer plano
    python main.py --check  # Verificar configuración
"""
import argparse
import logging
import signal
import sys
import time

from pathlib import Path

from organizer.watcher import ScreenshotWatcher
from organizer.analyzer import analyze_screenshot, check_ollama_available
from organizer.renamer import rename_screenshot

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("organizer.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


def process_screenshot(filepath: str):
    """
    Procesa una captura de pantalla: analiza y renombra.
    
    Args:
        filepath: Ruta al archivo de captura.
    """
    try:
        logger.info(f"Procesando: {filepath}")
        
        # Analizar contenido con Ollama
        analysis = analyze_screenshot(filepath)
        
        # Renombrar según el análisis
        new_path = rename_screenshot(filepath, analysis)
        
        logger.info(f"✅ Completado: {new_path}")
        
    except Exception as e:
        logger.error(f"❌ Error procesando {filepath}: {e}")


def process_existing_screenshots():
    """
    Procesa todas las capturas de pantalla existentes en el Desktop.
    Busca archivos que coincidan con el patrón de capturas de macOS.
    """
    desktop = Path.home() / "Desktop"
    pattern = "Captura de pantalla*.png"
    
    existing_screenshots = list(desktop.glob(pattern))
    
    if not existing_screenshots:
        logger.info("📂 No hay capturas existentes para procesar")
        return
    
    logger.info(f"📂 Procesando {len(existing_screenshots)} capturas existentes...")
    
    for filepath in existing_screenshots:
        process_screenshot(str(filepath))


def check_configuration():
    """Verifica que todo esté configurado correctamente."""
    print("🔍 Verificando configuración...\n")
    
    # Verificar Ollama
    print("1. Verificando Ollama...")
    if check_ollama_available():
        print("   ✅ Ollama está corriendo y llava está instalado")
    else:
        print("   ❌ Problema con Ollama. Asegúrate de que:")
        print("      - Ollama esté corriendo: ollama serve")
        print("      - llava esté instalado: ollama pull llava")
        return False
    
    # Verificar Desktop
    print("\n2. Verificando acceso al Desktop...")
    from pathlib import Path
    desktop = Path.home() / "Desktop"
    if desktop.exists():
        print(f"   ✅ Desktop accesible: {desktop}")
    else:
        print(f"   ❌ No se encontró Desktop: {desktop}")
        return False
    
    print("\n✅ Todo configurado correctamente!")
    print("   Ejecuta 'python main.py' para iniciar el agente")
    print("   o usa './service.sh start' para ejecutar en segundo plano")
    return True


def main():
    """Punto de entrada principal del agente."""
    parser = argparse.ArgumentParser(
        description="Agente Organizador de Capturas de Pantalla"
    )
    parser.add_argument(
        "--check", 
        action="store_true",
        help="Verificar configuración sin iniciar el agente"
    )
    args = parser.parse_args()
    
    if args.check:
        sys.exit(0 if check_configuration() else 1)
    
    # Verificar Ollama antes de iniciar
    if not check_ollama_available():
        logger.error("Ollama no está disponible. Ejecuta primero: ollama serve")
        sys.exit(1)
    
    logger.info("🚀 Iniciando Agente Organizador de Capturas")
    logger.info("   Presiona Ctrl+C para detener")
    
    # Procesar capturas existentes primero
    process_existing_screenshots()
    
    # Crear el watcher
    watcher = ScreenshotWatcher(callback=process_screenshot)
    
    # Manejar señales de terminación
    def signal_handler(signum, frame):
        logger.info("\n🛑 Deteniendo agente...")
        watcher.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Iniciar monitoreo
    watcher.start()
    
    # Mantener el proceso vivo
    try:
        while watcher.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
