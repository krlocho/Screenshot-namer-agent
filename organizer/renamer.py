"""
Renombrador de archivos basado en el análisis de contenido.
Genera nombres descriptivos según el tipo de contenido detectado.
"""
import os
import re
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def sanitize_filename(text: str, max_length: int = 50) -> str:
    """
    Limpia un texto para usarlo como nombre de archivo.
    
    Args:
        text: Texto a limpiar.
        max_length: Longitud máxima del resultado.
        
    Returns:
        Texto limpio y seguro para usar como nombre de archivo.
    """
    if not text:
        return "sin_descripcion"
    
    # Reemplazar caracteres problemáticos
    text = text.replace("/", "-").replace("\\", "-")
    text = text.replace(":", "-").replace("*", "")
    text = text.replace("?", "").replace('"', "")
    text = text.replace("<", "").replace(">", "")
    text = text.replace("|", "-")
    
    # Reemplazar espacios múltiples y guiones
    text = re.sub(r"\s+", "_", text.strip())
    text = re.sub(r"-+", "-", text)
    text = re.sub(r"_+", "_", text)
    
    # Truncar si es muy largo
    if len(text) > max_length:
        text = text[:max_length].rstrip("_").rstrip("-")
    
    return text


# Valores placeholder que llava puede devolver literalmente
PLACEHOLDER_VALUES = {
    "nombre", "proveedor", "XX.XX", "YYYY-MM-DD", "EUR/USD/$", 
    "Python/JavaScript/etc", "WhatsApp/Telegram/etc", "breve descripción",
    "tema de la conversación", "nombre del sitio", "contenido principal",
    "tipo y contenido del documento", "descripción breve del contenido"
}


def clean_analysis_value(value: str, default: str) -> str:
    """Limpia valores placeholder devueltos por llava."""
    if not value or value.lower() in [v.lower() for v in PLACEHOLDER_VALUES]:
        return default
    return value


def generate_new_name(analysis: dict, original_path: str) -> str:
    """
    Genera un nuevo nombre de archivo basado en el análisis.
    
    Args:
        analysis: Diccionario con el análisis de la imagen.
        original_path: Ruta original del archivo.
        
    Returns:
        Nuevo nombre de archivo (solo el nombre, no la ruta).
    """
    tipo = analysis.get("tipo", "OTRO").upper()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if tipo == "FACTURA":
        proveedor = clean_analysis_value(analysis.get("proveedor", ""), "factura")
        proveedor = sanitize_filename(proveedor, 20)
        importe = clean_analysis_value(analysis.get("importe", ""), "")
        moneda = clean_analysis_value(analysis.get("moneda", ""), "EUR")
        fecha = clean_analysis_value(analysis.get("fecha", ""), today)
        
        # Validar que la fecha tenga formato correcto, si no usar today
        if not re.match(r"\d{4}-\d{2}-\d{2}", fecha):
            fecha = today
        
        # Formatear moneda
        if moneda.lower() in ["eur", "euro", "euros", "€"]:
            moneda_sym = "€"
        elif moneda.lower() in ["usd", "dollar", "dollars", "$"]:
            moneda_sym = "$"
        else:
            moneda_sym = ""
        
        if importe and importe not in ["XX.XX", "0", "0.00"]:
            return f"[FACTURA] {proveedor} - {moneda_sym}{importe} - {fecha}.png"
        else:
            return f"[FACTURA] {proveedor} - {fecha}.png"
            
    elif tipo == "CODIGO":
        lenguaje = sanitize_filename(analysis.get("lenguaje", "codigo"), 15)
        descripcion = sanitize_filename(analysis.get("descripcion", "fragmento"), 30)
        return f"[CODIGO] {lenguaje} - {descripcion}.png"
        
    elif tipo == "CHAT":
        app = sanitize_filename(analysis.get("aplicacion", "chat"), 15)
        descripcion = sanitize_filename(analysis.get("descripcion", "conversacion"), 30)
        return f"[CHAT] {app} - {descripcion}.png"
        
    elif tipo == "WEB":
        sitio = sanitize_filename(analysis.get("sitio", "web"), 20)
        descripcion = sanitize_filename(analysis.get("descripcion", "pagina"), 25)
        return f"[WEB] {sitio} - {descripcion} - {today}.png"
        
    elif tipo == "DOCUMENTO":
        descripcion = sanitize_filename(analysis.get("descripcion", "documento"), 40)
        return f"[DOC] {descripcion} - {today}.png"
        
    else:
        descripcion = sanitize_filename(analysis.get("descripcion", "captura"), 40)
        return f"[OTRO] {descripcion} - {today}.png"


def rename_screenshot(original_path: str, analysis: dict) -> str:
    """
    Renombra una captura de pantalla basándose en su análisis.
    
    Args:
        original_path: Ruta original del archivo.
        analysis: Diccionario con el análisis de la imagen.
        
    Returns:
        Nueva ruta del archivo renombrado.
    """
    original_path = Path(original_path)
    directory = original_path.parent
    
    new_name = generate_new_name(analysis, str(original_path))
    new_path = directory / new_name
    
    # Manejar duplicados
    counter = 1
    base_name = new_name.rsplit(".", 1)[0]
    extension = ".png"
    
    while new_path.exists():
        new_name = f"{base_name} ({counter}){extension}"
        new_path = directory / new_name
        counter += 1
    
    try:
        os.rename(original_path, new_path)
        logger.info(f"Renombrado: {original_path.name} -> {new_name}")
        return str(new_path)
        
    except OSError as e:
        logger.error(f"Error renombrando archivo: {e}")
        raise
