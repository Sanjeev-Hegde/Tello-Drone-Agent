"""
Simple Tello SDK based on official DJI Tello-Python SDK
Modernized for Python 3.9+ compatibility
"""
import socket
import threading
import time
import logging
from typing import Optional


class SimpleTello:
    """Simple Tello drone controller based on official DJI SDK."""
    
    def __init__(self, host: str = '192.168.10.1', port: int = 8889):
        self.logger = logging.getLogger(__name__)
        
        # Network configuration
        self.local_ip = ''
        self.local_port = 8889
        self.tello_ip = host
        self.tello_port = port
        self.tello_address = (self.tello_ip, self.tello_port)
        
        # Socket setup - try different approaches
        self.socket = None
        self._setup_socket()
        
        # Response handling
        self.response = None
        self.response_condition = threading.Condition()
        
        # Start response thread
        self.receive_thread = threading.Thread(target=self._receive_thread)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
        # Connection state
        self.is_connected = False
        self.max_timeout = 15.0
        
        self.logger.info(f"SimpleTello initialized for {self.tello_ip}:{self.tello_port}")

    def _setup_socket(self):
        """Setup UDP socket with multiple fallback approaches."""
        approaches = [
            # Approach 1: Bind to any port (most compatible)
            lambda: self._bind_socket('', 0),
            # Approach 2: Bind to specific port (like official DJI SDK)
            lambda: self._bind_socket('', 8889),
            # Approach 3: Don't bind, just create socket
            lambda: self._create_socket_only(),
            # Approach 4: Try different socket options
            lambda: self._setup_socket_with_broadcast()
        ]
        
        for i, approach in enumerate(approaches, 1):
            try:
                self.logger.debug(f"Trying socket setup approach {i}")
                approach()
                self.logger.info(f"Socket setup successful (approach {i})")
                return
            except Exception as e:
                self.logger.warning(f"Socket setup approach {i} failed: {e}")
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                    self.socket = None
        
        raise RuntimeError("Failed to setup UDP socket with any approach")

    def _bind_socket(self, ip: str, port: int):
        """Bind socket to specific IP and port."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # For macOS compatibility
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass  # SO_REUSEPORT not available on all systems
        self.socket.bind((ip, port))
        self.local_port = port if port != 0 else self.socket.getsockname()[1]

    def _create_socket_only(self):
        """Create socket without binding."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass
        self.local_port = 0  # System will assign port

    def _setup_socket_with_broadcast(self):
        """Create socket with broadcast enabled."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass
        # Try binding to any available port
        self.socket.bind(('', 0))
        self.local_port = self.socket.getsockname()[1]

    def connect(self) -> bool:
        """Connect to Tello drone."""
        try:
            self.logger.info("Connecting to Tello...")
            
            # First check if we can reach the Tello IP
            if not self._test_network_connectivity():
                return False
            
            response = self.send_command("command")
            if response and b'ok' in response.lower():
                self.is_connected = True
                self.logger.info("✅ Tello connected successfully!")
                return True
            else:
                self.logger.error(f"❌ Tello connection failed. Response: {response}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Tello connection error: {e}")
            return False

    def _test_network_connectivity(self) -> bool:
        """Test if we can reach Tello IP."""
        import subprocess
        
        try:
            self.logger.debug(f"Testing connectivity to {self.tello_ip}")
            
            # Try ping first (macOS syntax)
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2000', self.tello_ip],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.logger.debug("✅ Ping successful")
                
                # Additional network diagnostics
                self._log_network_info()
                return True
            else:
                self.logger.warning("❌ Ping failed - check if connected to Tello WiFi")
                self.logger.warning("🔧 Make sure you're connected to TELLO-XXXXXX WiFi network")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.warning("⏰ Ping timeout - network might be slow")
            return True  # Continue trying, might still work
        except Exception as e:
            self.logger.warning(f"⚠️  Network test failed: {e}")
            return True  # Continue trying anyway

    def _log_network_info(self):
        """Log additional network information for debugging."""
        try:
            # Get local IP info
            import subprocess
            result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Look for WiFi interface
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'en0:' in line or 'en1:' in line:  # Common WiFi interfaces on macOS
                        # Check next few lines for IP address
                        for j in range(i, min(i+10, len(lines))):
                            if 'inet ' in lines[j] and '192.168.10.' in lines[j]:
                                self.logger.debug(f"Found Tello network interface: {lines[j].strip()}")
                                break
            
            # Log socket details
            if self.socket:
                local_addr = self.socket.getsockname()
                self.logger.debug(f"Local socket bound to: {local_addr}")
                
        except Exception as e:
            self.logger.debug(f"Could not get network info: {e}")

    def send_command(self, command: str, timeout: float = None) -> Optional[bytes]:
        """
        Send a command to Tello and wait for response.
        
        Args:
            command: Command string to send
            timeout: Maximum time to wait for response
            
        Returns:
            Response bytes from Tello, or None if timeout/error
        """
        if timeout is None:
            timeout = self.max_timeout
            
        if not self.socket:
            self.logger.error("Socket not initialized")
            return None
            
        try:
            self.logger.debug(f"Sending command: '{command}' to {self.tello_ip}")
            
            # Clear previous response
            with self.response_condition:
                self.response = None
            
            # Send command with retry
            for attempt in range(3):
                try:
                    self.socket.sendto(command.encode('utf-8'), self.tello_address)
                    self.logger.debug(f"Command sent (attempt {attempt + 1})")
                    break
                except OSError as e:
                    if attempt == 2:  # Last attempt
                        self.logger.error(f"Failed to send command after 3 attempts: {e}")
                        return None
                    self.logger.warning(f"Send attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(0.5)
            
            # Wait for response
            start_time = time.time()
            with self.response_condition:
                while self.response is None:
                    elapsed = time.time() - start_time
                    if elapsed > timeout:
                        self.logger.warning(f"Command '{command}' timed out after {timeout}s")
                        return None
                    
                    self.response_condition.wait(timeout=0.1)
            
            self.logger.debug(f"Command '{command}' response: {self.response}")
            return self.response
            
        except Exception as e:
            self.logger.error(f"Error sending command '{command}': {e}")
            return None

    def _receive_thread(self):
        """Listen for responses from Tello."""
        self.logger.debug("Response thread started")
        
        while True:
            try:
                response, ip = self.socket.recvfrom(1024)
                self.logger.debug(f"Received from {ip}: {response}")
                
                with self.response_condition:
                    self.response = response
                    self.response_condition.notify_all()
                    
            except socket.error as e:
                self.logger.error(f"Socket error in receive thread: {e}")
                break

    def get_battery(self) -> int:
        """Get battery level."""
        try:
            response = self.send_command("battery?")
            if response:
                battery = int(response.decode('utf-8').strip())
                return battery
        except Exception as e:
            self.logger.error(f"Error getting battery: {e}")
        return 0

    def streamon(self) -> bool:
        """Start video stream."""
        try:
            response = self.send_command("streamon")
            if response and b'ok' in response.lower():
                self.logger.info("📹 Video stream started")
                return True
            else:
                self.logger.error(f"Failed to start video stream: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Error starting video stream: {e}")
            return False

    def streamoff(self) -> bool:
        """Stop video stream."""
        try:
            response = self.send_command("streamoff")
            if response and b'ok' in response.lower():
                self.logger.info("📹 Video stream stopped")
                return True
            else:
                self.logger.error(f"Failed to stop video stream: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Error stopping video stream: {e}")
            return False

    def takeoff(self) -> bool:
        """Take off."""
        try:
            response = self.send_command("takeoff", timeout=20.0)
            if response and b'ok' in response.lower():
                self.logger.info("🚁 Takeoff successful")
                return True
            else:
                self.logger.error(f"Takeoff failed: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Takeoff error: {e}")
            return False

    def land(self) -> bool:
        """Land."""
        try:
            response = self.send_command("land", timeout=20.0)
            if response and b'ok' in response.lower():
                self.logger.info("🚁 Landing successful")
                return True
            else:
                self.logger.error(f"Landing failed: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Landing error: {e}")
            return False

    def get_frame_read(self):
        """Return a frame reader object for video streaming."""
        return TelloFrameReader(self.tello_ip)

    def close(self):
        """Close connection."""
        try:
            if self.is_connected:
                self.streamoff()
            self.socket.close()
            self.logger.info("Tello connection closed")
        except Exception as e:
            self.logger.error(f"Error closing connection: {e}")


class TelloFrameReader:
    """Simple frame reader for Tello video stream."""
    
    def __init__(self, tello_ip: str):
        self.logger = logging.getLogger(__name__)
        self.tello_ip = tello_ip
        self.video_port = 11111
        
        # Video socket
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.video_socket.bind(('', self.video_port))
        
        self.frame = None
        self.running = False
        
        self.logger.info(f"TelloFrameReader initialized for {tello_ip}:{self.video_port}")

    def start(self):
        """Start frame reading."""
        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_video)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        self.logger.info("Video frame reading started")

    def stop(self):
        """Stop frame reading."""
        self.running = False
        try:
            self.video_socket.close()
        except:
            pass
        self.logger.info("Video frame reading stopped")

    def _receive_video(self):
        """Receive video data (simplified - returns dummy data for now)."""
        # This is a simplified implementation
        # For full video decoding, you'd need additional libraries
        import numpy as np
        
        while self.running:
            try:
                # Receive video packet
                data, addr = self.video_socket.recvfrom(1518)
                
                # For now, create a dummy frame
                # In a full implementation, you'd decode H.264 data
                dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                dummy_frame[:] = [64, 128, 192]  # Gray-blue color
                
                self.frame = dummy_frame
                time.sleep(1/30)  # 30 FPS simulation
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error receiving video: {e}")
                break
