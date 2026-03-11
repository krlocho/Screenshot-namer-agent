"""
Analizador de imágenes usando Ollama con modelo de visión (llava).
Detecta el contenido de las capturas y extrae información relevante.
"""
import base64
import io
import json
import logging
import requests
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llava-phi3"
MAX_IMAGE_SIZE = 800  # Tamaño máximo en pixels para acelerar análisis

ANALYSIS_PROMPT = """Analiza esta captura de pantalla y responde SOLO con un JSON válido (sin texto adicional).

Identifica el tipo de contenido y extrae información relevante:

Para FACTURAS o recibos:
{"tipo": "FACTURA", "proveedor": "nombre", "importe": "XX.XX", "moneda": "EUR/USD/$", "fecha": "YYYY-MM-DD"}

Para CÓDIGO de programación:
{"tipo": "CODIGO", "lenguaje": "Python/JavaScript/etc", "descripcion": "breve descripción de qué hace"}

Para CHATS o mensajería:
{"tipo": "CHAT", "aplicacion": "WhatsApp/Telegram/etc", "descripcion": "tema de la conversación"}

Para PÁGINAS WEB:
{"tipo": "WEB", "sitio": "nombre del sitio", "descripcion": "contenido principal"}

Para DOCUMENTOS:
{"tipo": "DOCUMENTO", "descripcion": "tipo y contenido del documento"}

Para cualquier OTRO contenido:
{"tipo": "OTRO", "descripcion": "descripción breve del contenido"}

Responde ÚNICAMENTE con el JSON, sin explicaciones adicionales."""


def encode_image_to_base64(image_path: str) -> str:
    """
    Codifica una imagen en base64 para enviar a Ollama.
    Redimensiona imágenes grandes para acelerar el análisis.
    """
    with Image.open(image_path) as img:
        # Convertir a RGB si es necesario (para PNGs con transparencia)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Redimensionar si es muy grande
        width, height = img.size
        # llava-phi3 procesa bien imágenes medianas
        if width > MAX_IMAGE_SIZE or height > MAX_IMAGE_SIZE:
            ratio = min(MAX_IMAGE_SIZE / width, MAX_IMAGE_SIZE / height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            logger.debug(f"Imagen redimensionada: {width}x{height} -> {new_size[0]}x{new_size[1]}")
        
        # Guardar en buffer como JPEG con calidad media
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=75)
        buffer.seek(0)
        
        return base64.b64encode(buffer.read()).decode("utf-8")


def analyze_screenshot(image_path: str) -> dict:
    """
    Analiza una captura de pantalla usando Ollama.
    
    Args:
        image_path: Ruta al archivo de imagen.
        
    Returns:
        dict con la información extraída de la imagen.
    """
    logger.info(f"Analizando imagen: {Path(image_path).name}")
    
    try:
        image_base64 = encode_image_to_base64(image_path)
        
        payload = {
            "model": MODEL_NAME,
            "prompt": ANALYSIS_PROMPT,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": 0.1,  # Baja temperatura para respuestas consistentes
                "num_predict": 300,   # Suficiente para JSON completo
            }
        }
        
        # llava-phi3 es mucho más ligero, timeout de 120s debería bastar
        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        
        result = response.json()
        response_text = result.get("response", "").strip()
        
        # Intentar parsear el JSON de la respuesta
        try:
            # Buscar el JSON en la respuesta
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                analysis = json.loads(json_str)
                logger.info(f"Análisis completado: tipo={analysis.get('tipo', 'DESCONOCIDO')}")
                return analysis
            else:
                logger.warning(f"No se encontró JSON válido en la respuesta: {response_text[:100]}")
                # Fallback manual simple si no devuelve JSON
                return {"tipo": "OTRO", "descripcion": "captura_analizada"}
                
        except json.JSONDecodeError as e:
            logger.warning(f"Error parseando JSON: {e}. Respuesta: {response_text[:100]}")
            return {"tipo": "OTRO", "descripcion": "captura_analizada"}
            
    except requests.exceptions.ConnectionError:
        logger.error("No se pudo conectar a Ollama. ¿Está el servicio corriendo?")
        raise RuntimeError("Ollama no está disponible. Ejecuta 'ollama serve' primero.")
        
    except requests.exceptions.Timeout:
        logger.error("Timeout al analizar la imagen")
        raise RuntimeError("Timeout analizando la imagen")
        
    except Exception as e:
        logger.error(f"Error inesperado analizando imagen: {e}")
        raise


def check_ollama_available() -> bool:
    """Verifica si Ollama está disponible y el modelo llava-phi3 está instalado."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        
        models = response.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        
        # Buscar modelo en cualquier variante
        has_model = any(MODEL_NAME in name.lower() for name in model_names)
        
        if not has_model:
            logger.warning(f"Modelo {MODEL_NAME} no encontrado. Instálalo con: ollama pull {MODEL_NAME}")
            return False
            
        return True
        
    except requests.exceptions.ConnectionError:
        logger.error("Ollama no está corriendo. Inicia con: ollama serve")
        return False
    except Exception as e:
        logger.error(f"Error verificando Ollama: {e}")
        return False
