#!/bin/bash
# Monitoramento da Lucy

echo "================================================================"
echo "MONITORAMENTO DA LUCY FRANKENSTEIN"
echo "================================================================"

echo ""
echo "--- Status do serviço ---"
sudo systemctl status lucy-frankenstein --no-pager | head -5

echo ""
echo "--- Modelos em RAM ---"
ollama ps

echo ""
echo "--- Uso de recursos ---"
echo "CPU:"
top -bn1 | grep "Cpu" | head -1
echo ""
echo "RAM:"
free -h | grep Mem

echo ""
echo "--- Logs recentes ---"
sudo journalctl -u lucy-frankenstein --no-pager -n 10
