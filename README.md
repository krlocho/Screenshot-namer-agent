# Agente Organizador de Capturas de Pantalla 📸

Agente inteligente que monitorea tu escritorio, analiza las capturas de pantalla usando IA con visión (Ollama + llava), y las renombra automáticamente según su contenido.

## Características

- 🔍 **Detección automática** de nuevas capturas en el Desktop
- 🤖 **Análisis con IA** usando Ollama llava (modelo de visión)
- 📝 **Renombrado inteligente** según el tipo de contenido:
  - `[FACTURA] Amazon - €59.99 - 2026-01-19.png`
  - `[CODIGO] Python - funcion_api.png`
  - `[CHAT] WhatsApp - reunion_trabajo.png`
  - `[WEB] GitHub - repositorio_proyecto.png`
- ⚡ **Servicio en segundo plano** que puedes iniciar/detener fácilmente

## Requisitos

- Python 3.8+
- [Ollama](https://ollama.ai) con modelo `llava` instalado

## Instalación

```bash
# 1. Instalar dependencias de Python
pip install -r requirements.txt

# 2. Asegurarse de que Ollama está corriendo
ollama serve

# 3. Instalar el modelo de visión (si no lo tienes)
ollama pull llava

# 4. Dar permisos de ejecución al script de servicio
chmod +x service.sh

# 5. Verificar configuración
python main.py --check
```

## Uso

### Modo Servicio (Recomendado)

```bash
# Iniciar el agente en segundo plano
./service.sh start

# Ver estado
./service.sh status

# Ver logs en tiempo real
./service.sh logs

# Detener el agente
./service.sh stop

# Reiniciar
./service.sh restart
```

### Modo Interactivo

```bash
# Ejecutar en primer plano (útil para debug)
python main.py

# Presiona Ctrl+C para detener
```

## Tipos de Contenido Detectados

| Tipo | Ejemplo de nombre | Información extraída |
|------|------------------|---------------------|
| FACTURA | `[FACTURA] Amazon - €59.99 - 2026-01-19.png` | Proveedor, importe, fecha |
| CODIGO | `[CODIGO] Python - funcion_api.png` | Lenguaje, descripción |
| CHAT | `[CHAT] WhatsApp - reunion.png` | App, tema conversación |
| WEB | `[WEB] GitHub - proyecto.png` | Sitio, contenido |
| DOCUMENTO | `[DOC] informe_ventas.png` | Tipo y contenido |
| OTRO | `[OTRO] captura_generica.png` | Descripción general |

## Estructura del Proyecto

```
Agente-organizador/
├── main.py              # Script principal
├── organizer/
│   ├── __init__.py
│   ├── watcher.py       # Monitoreo de archivos
│   ├── analyzer.py      # Análisis con Ollama
│   └── renamer.py       # Lógica de renombrado
├── service.sh           # Gestión del servicio
├── requirements.txt     # Dependencias
└── README.md           # Este archivo
```

## Logs

Los logs se guardan en `organizer.log` en el directorio del proyecto.

```bash
# Ver últimas líneas
tail -20 organizer.log

# Ver en tiempo real
./service.sh logs
```

## Solución de Problemas

### Ollama no está disponible
```bash
# Asegúrate de que Ollama está corriendo
ollama serve

# Verifica que llava está instalado
ollama list
```

### El agente no detecta capturas
- Las capturas deben tener el formato: `Captura de pantalla YYYY-MM-DD a las HH.MM.SS.png`
- Verifica que se están guardando en el Desktop

### Error de permisos
```bash
chmod +x service.sh
```
