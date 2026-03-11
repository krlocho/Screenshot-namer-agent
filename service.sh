#!/bin/bash
#
# Script de gestión del servicio del Agente Organizador
# Uso: ./service.sh [start|stop|status|logs|restart]
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/.organizer.pid"
LOG_FILE="$SCRIPT_DIR/organizer.log"
PYTHON_SCRIPT="$SCRIPT_DIR/main.py"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  El agente ya está corriendo (PID: $PID)${NC}"
            return 1
        else
            rm "$PID_FILE"
        fi
    fi
    
    echo -e "${GREEN}🚀 Iniciando Agente Organizador...${NC}"
    
    # Verificar que Python esté disponible
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 no encontrado${NC}"
        return 1
    fi
    
    # Iniciar en segundo plano
    cd "$SCRIPT_DIR"
    nohup python3 "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    sleep 2
    
    if ps -p "$(cat "$PID_FILE")" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Agente iniciado (PID: $(cat "$PID_FILE"))${NC}"
        echo -e "   📁 Monitoreando: ~/Desktop"
        echo -e "   📄 Logs: $LOG_FILE"
    else
        echo -e "${RED}❌ Error al iniciar el agente. Revisa los logs:${NC}"
        tail -10 "$LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}⚠️  El agente no está corriendo${NC}"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}🛑 Deteniendo agente (PID: $PID)...${NC}"
        kill "$PID"
        
        # Esperar a que termine
        for i in {1..10}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                break
            fi
            sleep 0.5
        done
        
        # Forzar si sigue corriendo
        if ps -p "$PID" > /dev/null 2>&1; then
            kill -9 "$PID"
        fi
        
        echo -e "${GREEN}✅ Agente detenido${NC}"
    else
        echo -e "${YELLOW}⚠️  El proceso ya no existe${NC}"
    fi
    
    rm -f "$PID_FILE"
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Agente corriendo (PID: $PID)${NC}"
            echo -e "   📁 Monitoreando: ~/Desktop"
            echo ""
            echo "Últimas líneas del log:"
            tail -5 "$LOG_FILE" 2>/dev/null || echo "   (sin logs aún)"
            return 0
        else
            echo -e "${RED}❌ El proceso ha terminado inesperadamente${NC}"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo -e "${YELLOW}⏹️  Agente no está corriendo${NC}"
        return 1
    fi
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        echo -e "${GREEN}📄 Mostrando logs (Ctrl+C para salir):${NC}"
        echo ""
        tail -f "$LOG_FILE"
    else
        echo -e "${YELLOW}⚠️  No hay archivo de logs aún${NC}"
    fi
}

restart() {
    stop
    sleep 1
    start
}

# Menú principal
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    restart)
        restart
        ;;
    *)
        echo "Agente Organizador de Capturas de Pantalla"
        echo ""
        echo "Uso: $0 {start|stop|status|logs|restart}"
        echo ""
        echo "Comandos:"
        echo "  start   - Iniciar el agente en segundo plano"
        echo "  stop    - Detener el agente"
        echo "  status  - Ver estado actual"
        echo "  logs    - Ver logs en tiempo real"
        echo "  restart - Reiniciar el agente"
        exit 1
        ;;
esac
