import serial
import serial.tools.list_ports
import time
from threading import Thread, Event
from queue import Queue

class SerialService:
    def __init__(self, logger, db, config, port=None, baudrate=9600):
        self.logger = logger
        self.db = db
        self.config = config
        self.port = port or self.config.get('default_com_port')
        self.baudrate = baudrate or self.config.get('default_baudrate', 9600)
        self.serial_conn = None
        self._stop_event = Event()
        self._thread = None
        self.data_queue = Queue()
        self.is_connected = False

    def start(self):
        """Start the serial service"""
        if self._thread and self._thread.is_alive():
            self.logger.warning("Serial service is already running")
            return

        self._stop_event.clear()
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        self.logger.info(f"Serial service started on {self.port}")

    def stop(self):
        """Stop the serial service"""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.is_connected = False
        self.logger.info("Serial service stopped")

    def _run(self):
        """Main serial communication loop"""
        while not self._stop_event.is_set():
            try:
                if not self.is_connected:
                    self._connect()
                
                if self.is_connected:
                    self._read_serial()
                else:
                    time.sleep(1)  # Wait before trying to reconnect
                    
            except Exception as e:
                self.logger.error(f"Serial error: {str(e)}", exc_info=True)
                self.is_connected = False
                if self.serial_conn:
                    self.serial_conn.close()
                time.sleep(1)

    def _connect(self):
        """Establish serial connection"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0,
                write_timeout=1.0
            )
            self.is_connected = True
            self.logger.info(f"Connected to {self.port} at {self.baudrate} baud")
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.port}: {str(e)}")
            self.is_connected = False
            raise

    def _read_serial(self):
        """Read data from serial port"""
        if not self.serial_conn or not self.serial_conn.is_open:
            self.is_connected = False
            return

        try:
            if self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode('ascii', errors='ignore').strip()
                if line:
                    self._process_reading(line)
        except Exception as e:
            self.logger.error(f"Error reading from serial: {str(e)}")
            self.is_connected = False
            if self.serial_conn:
                self.serial_conn.close()

    def _process_reading(self, data):
        """Process raw serial data"""
        try:
            # Parse the weight value from the scale
            # This is a simple example - adjust based on your scale's protocol
            weight = float(data)
            self.data_queue.put(weight)
            self.logger.info(f"Weight reading: {weight} kg")
            
            # Here you could add logic to determine if the reading is stable
            # and call appropriate callbacks or update the database
            # For example:
            # self.db.insert_reading(weight, stable=True)
            
        except ValueError:
            self.logger.warning(f"Invalid data received: {data}")

    def get_latest_reading(self):
        """Get the latest weight reading if available"""
        if not self.data_queue.empty():
            return self.data_queue.get()
        return None

    def is_alive(self):
        """Check if the service is running"""
        return self._thread and self._thread.is_alive()

    def list_ports(self):
        """List available serial ports"""
        return [port.device for port in serial.tools.list_ports.comports()]

    def change_port(self, port, baudrate=None):
        """Change the serial port and restart the service"""
        was_running = self.is_alive()
        if was_running:
            self.stop()
        
        self.port = port
        if baudrate:
            self.baudrate = baudrate
            
        if was_running:
            self.start()