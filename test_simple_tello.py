#!/usr/bin/env python3
"""
Simple test script for SimpleTello SDK
"""
import sys
import logging
import time

# Add the src directory to path
sys.path.insert(0, 'src')

from drone.simple_tello import SimpleTello

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Test SimpleTello connection."""
    print("🔍 Testing SimpleTello SDK...")
    print("")
    
    # First check network connectivity
    print("🌐 Checking network status...")
    import subprocess
    try:
        result = subprocess.run(['ping', '-c', '1', '-W', '2000', '192.168.10.1'], 
                              capture_output=True, timeout=3)
        if result.returncode == 0:
            print("✅ Connected to Tello network (192.168.10.1 reachable)")
            tello_reachable = True
        else:
            print("❌ Not connected to Tello network")
            tello_reachable = False
    except:
        print("⚠️  Cannot test network connectivity")
        tello_reachable = False
    
    if not tello_reachable:
        print("")
        print("🔧 NETWORK SETUP REQUIRED:")
        print("   1. Power on your Tello drone")
        print("   2. Connect your computer to TELLO-XXXXXX WiFi network")
        print("   3. Run this test again")
        print("")
        print("💡 ALTERNATIVE: Test with webcam first:")
        print("   python src/main.py --vision-only --camera-source webcam")
        print("")
        return 1
    
    print("")
    print("📋 TELLO SETUP CHECKLIST:")
    print("   1. Power on your Tello drone")
    print("   2. Connect your computer to the Tello WiFi network (TELLO-XXXXXX)")
    print("   3. Wait for the WiFi connection to establish")
    print("   4. Make sure no other apps are connected to the Tello")
    print("")
    
    try:
        # Create Tello instance
        tello = SimpleTello()
        print("✅ SimpleTello instance created")
        
        # Test connection
        print("🔌 Testing connection...")
        connected = tello.connect()
        
        if connected:
            print("🎉 SUCCESS: Tello connection working!")
            
            # Test battery
            battery = tello.get_battery()
            print(f"🔋 Battery level: {battery}%")
            
            # Test video stream
            print("📹 Testing video stream...")
            stream_ok = tello.streamon()
            if stream_ok:
                print("✅ Video stream started successfully")
                time.sleep(2)
                tello.streamoff()
                print("✅ Video stream stopped successfully")
            else:
                print("❌ Video stream failed")
            
            print("")
            print("🎉 ALL TESTS PASSED!")
            print("You can now run:")
            print("python src/main.py --vision-only --camera-source tello")
            
        else:
            print("❌ Connection failed")
            print("")
            print("🔧 TROUBLESHOOTING:")
            print("   1. Check if Tello is powered on (LED should be solid)")
            print("   2. Connect to Tello WiFi: TELLO-XXXXXX (check drone sticker)")
            print("   3. Verify network connection: ping 192.168.10.1")
            print("   4. Close other Tello apps (DJI GO, etc.)")
            print("   5. Try restarting the Tello drone")
        
        # Clean up
        tello.close()
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
