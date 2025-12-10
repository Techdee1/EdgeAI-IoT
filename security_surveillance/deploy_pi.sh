#!/bin/bash
# EcoGuard Raspberry Pi 3 Deployment Script
# Optimizes system for production deployment

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║     EcoGuard Pi 3 Optimization & Deployment Script               ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Warning: Not detected as Raspberry Pi. Proceeding anyway...${NC}"
fi

echo "📋 Pre-Deployment Checklist"
echo "================================"

# 1. Check RAM
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
echo -e "1. System RAM: ${TOTAL_RAM}MB"
if [ "$TOTAL_RAM" -lt 900 ]; then
    echo -e "   ${RED}✗ RAM too low for Pi 3 (expected ~900MB)${NC}"
else
    echo -e "   ${GREEN}✓ RAM sufficient${NC}"
fi

# 2. Check Swap
SWAP_SIZE=$(free -m | awk '/^Swap:/{print $2}')
echo "2. Swap Memory: ${SWAP_SIZE}MB"
if [ "$SWAP_SIZE" -lt 1024 ]; then
    echo -e "   ${YELLOW}⚠️  Swap < 1GB. Recommend 2GB for stability${NC}"
    read -p "   Would you like to increase swap to 2GB? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   Configuring swap..."
        sudo dphys-swapfile swapoff
        sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
        sudo dphys-swapfile setup
        sudo dphys-swapfile swapon
        echo -e "   ${GREEN}✓ Swap increased to 2GB${NC}"
    fi
else
    echo -e "   ${GREEN}✓ Swap adequate${NC}"
fi

# 3. Check CPU Governor
GOVERNOR=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "unknown")
echo "3. CPU Governor: ${GOVERNOR}"
if [ "$GOVERNOR" != "performance" ]; then
    echo -e "   ${YELLOW}⚠️  Not in performance mode${NC}"
    read -p "   Set CPU governor to performance? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
        echo -e "   ${GREEN}✓ CPU governor set to performance${NC}"
        
        # Make permanent
        if ! grep -q "scaling_governor" /etc/rc.local 2>/dev/null; then
            sudo sed -i '/^exit 0/i echo "performance" | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor' /etc/rc.local
            echo "   ${GREEN}✓ Made permanent in /etc/rc.local${NC}"
        fi
    fi
else
    echo -e "   ${GREEN}✓ Performance mode enabled${NC}"
fi

# 4. Check TFLite Configuration
echo "4. TFLite Model Configuration"
if grep -q "use_tflite: true" config/config.yaml; then
    echo -e "   ${GREEN}✓ TFLite enabled in config${NC}"
else
    echo -e "   ${YELLOW}⚠️  TFLite disabled - will use slower Keras model${NC}"
    echo "   Edit config/config.yaml and set use_tflite: true"
fi

# 5. Check Models
echo "5. AI Models"
if [ -f "data/models/mobilenet_plantvillage.tflite" ]; then
    SIZE=$(ls -lh data/models/mobilenet_plantvillage.tflite | awk '{print $5}')
    echo -e "   ${GREEN}✓ TFLite model found (${SIZE})${NC}"
else
    echo -e "   ${RED}✗ TFLite model missing${NC}"
    echo "   Run: python3 download_health_model.py"
fi

if [ -f "data/models/yolov8n.pt" ]; then
    SIZE=$(ls -lh data/models/yolov8n.pt | awk '{print $5}')
    echo -e "   ${GREEN}✓ YOLOv8n model found (${SIZE})${NC}"
else
    echo -e "   ${RED}✗ YOLOv8n model missing${NC}"
    echo "   Run: python3 download_model.py"
fi

# 6. Check MQTT Broker
echo "6. MQTT Broker (Mosquitto)"
if systemctl is-active --quiet mosquitto; then
    echo -e "   ${GREEN}✓ Mosquitto running${NC}"
else
    echo -e "   ${YELLOW}⚠️  Mosquitto not running${NC}"
    read -p "   Start Mosquitto service? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl start mosquitto
        sudo systemctl enable mosquitto
        echo -e "   ${GREEN}✓ Mosquitto started and enabled${NC}"
    fi
fi

# 7. Check Firewall
echo "7. Firewall Configuration"
if command -v ufw &> /dev/null; then
    if sudo ufw status | grep -q "8080.*ALLOW"; then
        echo -e "   ${GREEN}✓ Port 8080 (Dashboard) open${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Port 8080 not configured${NC}"
        echo "   Run: sudo ufw allow 8080/tcp"
    fi
    
    if sudo ufw status | grep -q "1883.*ALLOW"; then
        echo -e "   ${GREEN}✓ Port 1883 (MQTT) open${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Port 1883 not configured${NC}"
        echo "   Run: sudo ufw allow 1883/tcp"
    fi
else
    echo -e "   ${YELLOW}⚠️  UFW not installed (firewall disabled)${NC}"
fi

# 8. Check Python Dependencies
echo "8. Python Dependencies"
if python3 -c "import tensorflow, cv2, fastapi, paho.mqtt.client" 2>/dev/null; then
    echo -e "   ${GREEN}✓ Core dependencies installed${NC}"
else
    echo -e "   ${YELLOW}⚠️  Some dependencies missing${NC}"
    read -p "   Install dependencies from requirements.txt? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install -r requirements.txt
        echo -e "   ${GREEN}✓ Dependencies installed${NC}"
    fi
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                     Optimization Summary                          ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"

# Performance Test
echo ""
echo "🧪 Running Performance Test..."
echo "================================"

# Test TFLite inference speed
if [ -f "data/models/mobilenet_plantvillage.tflite" ]; then
    python3 -c "
import tensorflow as tf
import numpy as np
import time
import sys

try:
    interpreter = tf.lite.Interpreter(model_path='data/models/mobilenet_plantvillage.tflite')
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    
    # Warmup
    dummy = np.random.random((1, 224, 224, 3)).astype(np.float32)
    for _ in range(3):
        interpreter.set_tensor(input_details[0]['index'], dummy)
        interpreter.invoke()
    
    # Benchmark
    times = []
    for _ in range(10):
        start = time.time()
        interpreter.set_tensor(input_details[0]['index'], dummy)
        interpreter.invoke()
        times.append(time.time() - start)
    
    avg = np.mean(times) * 1000
    fps = 1000 / avg
    
    print(f'TFLite Inference: {avg:.2f}ms per image')
    print(f'Throughput: {fps:.2f} FPS')
    
    if avg < 100:
        print('Status: ✓ EXCELLENT - Ready for real-time processing')
    elif avg < 300:
        print('Status: ✓ GOOD - Suitable for periodic scanning')
    else:
        print('Status: ⚠️  SLOW - Consider optimization')
        
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                    Deployment Instructions                        ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "To start EcoGuard:"
echo ""
echo "  1. Test manually:"
echo "     python3 launch_integrated.py --mode health"
echo ""
echo "  2. Run as systemd service:"
echo "     sudo systemctl start ecoguard"
echo "     sudo systemctl enable ecoguard"
echo ""
echo "  3. Access dashboard:"
echo "     http://[raspberry-pi-ip]:8080"
echo ""
echo "  4. Monitor logs:"
echo "     tail -f data/logs/system.log"
echo "     journalctl -u ecoguard -f"
echo ""
echo "📚 For detailed optimization guide, see: PI_OPTIMIZATION_GUIDE.md"
echo ""
