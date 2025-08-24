#!/bin/bash
# Network connectivity test for Tello + Internet setup

echo "🔍 Testing Network Connectivity for Tello + Azure AI Vision..."
echo ""

# Test internet connection
echo "Testing Internet Access..."
if curl -s --max-time 5 https://www.microsoft.com > /dev/null; then
    echo "✅ Internet connection: Working"
    INTERNET_OK=1
else
    echo "❌ Internet connection: Failed"
    INTERNET_OK=0
fi

# Test Tello connection
echo "Testing Tello Connection..."
if ping -c 1 -W 2000 192.168.10.1 > /dev/null 2>&1; then
    echo "✅ Tello connection: Working"
    TELLO_OK=1
else
    echo "❌ Tello connection: Failed"
    TELLO_OK=0
fi

echo ""
echo "📊 Network Status Summary:"
echo "=========================="

if [ $INTERNET_OK -eq 1 ] && [ $TELLO_OK -eq 1 ]; then
    echo "🎉 SUCCESS: Both connections working!"
    echo ""
    echo "You can now run:"
    echo "python src/main.py --vision-only --camera-source tello"
    exit 0
fi

echo "⚠️  Network setup incomplete"
echo ""

if [ $INTERNET_OK -eq 0 ]; then
    echo "🔧 Internet Connection Issues:"
    echo "   • Check if you're connected to a network with internet"
    echo "   • Try connecting to mobile hotspot"
    echo "   • Use ethernet + WiFi dual connection"
fi

if [ $TELLO_OK -eq 0 ]; then
    echo "🔧 Tello Connection Issues:"
    echo "   • Power on your Tello drone"
    echo "   • Connect to TELLO-XXXXXX WiFi network"
    echo "   • Wait for WiFi connection to establish"
    echo "   • Check if Tello LED is solid (not blinking)"
fi

echo ""
echo "💡 Recommended Solution: Mobile Hotspot"
echo "======================================="
echo "1. Enable mobile hotspot on your phone"
echo "2. Connect your computer to phone's hotspot"
echo "3. Also connect to Tello WiFi (dual connection)"
echo "4. Run this test again"
echo ""
echo "📖 For more solutions, see: NETWORK_SOLUTIONS.md"

exit 1
