# Tello WiFi + Internet Access Solutions

The Tello drone creates its own WiFi network, which disconnects you from the internet needed for Azure AI Vision API calls. Here are practical solutions:

## Solution 1: Mobile Hotspot Bridge (Recommended)

### Setup Steps:
1. **Enable mobile hotspot** on your phone
2. **Connect your computer** to your phone's hotspot
3. **Connect to Tello WiFi** as secondary connection (if your OS supports it)
4. **Run the application** - you'll have both Tello access and internet

### Commands:
```bash
# Test this works by pinging both:
ping 192.168.10.1  # Tello drone
ping 8.8.8.8       # Internet

# Run the application
python src/main.py --vision-only --camera-source tello
```

## Solution 2: USB Tethering + Tello WiFi

### Setup Steps:
1. **Connect phone to computer via USB**
2. **Enable USB tethering** on phone
3. **Connect to Tello WiFi** on computer
4. **Run the application** - USB provides internet, WiFi connects to Tello

## Solution 3: Dual Network Interface (Advanced)

### macOS/Linux:
```bash
# Keep ethernet for internet, WiFi for Tello
# Connect ethernet cable to router
# Connect WiFi to Tello network
# Both connections will work simultaneously
```

### Windows:
```bash
# Use WiFi adapter for Tello
# Use ethernet for internet
# Set network priorities in adapter settings
```

## Solution 4: Router Bridge Mode

### Setup Steps:
1. **Configure a spare router** in bridge mode
2. **Connect it to your main internet**
3. **Connect computer to spare router**
4. **Connect to Tello WiFi** as secondary
5. **Run application** with dual connectivity

## Recommended Quick Setup

The **Mobile Hotspot** method is the easiest:

1. **Turn on mobile hotspot** on your phone
2. **Connect computer to phone hotspot**
3. **Connect to Tello WiFi** (TELLO-XXXXXX)
4. **Verify connectivity**:
   ```bash
   # Check internet
   curl -s https://www.google.com > /dev/null && echo "Internet: ✅" || echo "Internet: ❌"
   
   # Check Tello
   ping -c 1 192.168.10.1 > /dev/null && echo "Tello: ✅" || echo "Tello: ❌"
   ```

5. **Run the application**:
   ```bash
   python src/main.py --vision-only --camera-source tello
   ```

## Testing Your Setup

Use this simple test script to verify both connections work:

```bash
# Save as test_dual_connection.sh
#!/bin/bash

echo "🔍 Testing Network Connectivity..."

# Test internet
if curl -s --max-time 5 https://www.microsoft.com > /dev/null; then
    echo "✅ Internet connection: Working"
else
    echo "❌ Internet connection: Failed"
fi

# Test Tello
if ping -c 1 -W 2000 192.168.10.1 > /dev/null 2>&1; then
    echo "✅ Tello connection: Working"
else
    echo "❌ Tello connection: Failed"
fi

echo ""
echo "If both show ✅, you're ready to run:"
echo "python src/main.py --vision-only --camera-source tello"
```

## Alternative: Use Webcam for Development

While setting up dual connectivity, you can continue development with webcam:

```bash
# Use webcam for immediate testing
python src/main.py --vision-only --camera-source webcam

# Switch to Tello when network is configured
python src/main.py --vision-only --camera-source tello
```

The mobile hotspot solution works for most users and requires no special hardware or complex configuration.
