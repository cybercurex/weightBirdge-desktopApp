import importlib
import threading
from typing import Dict, Any, Optional, Type
from dataclasses import dataclass
from enum import Enum, auto
import time

class ServiceStatus(Enum):
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    ERROR = auto()

@dataclass
class ServiceInfo:
    name: str
    service: Any
    status: ServiceStatus
    last_error: Optional[str] = None
    start_time: Optional[float] = None
    uptime: float = 0.0

class ServiceManager:
    """
    Manages the lifecycle of all services in the application.
    Handles service registration, initialization, starting, and stopping.
    """
    
    def __init__(self, logger, db, config):
        """
        Initialize the ServiceManager.
        
        Args:
            logger: Logger instance for service messages
            db: Database connection or session
            config: Configuration dictionary
        """
        self.logger = logger
        self.db = db
        self.config = config
        self._services: Dict[str, ServiceInfo] = {}
        self._lock = threading.RLock()
        self._service_registry = {
            'serial': {
                'module': 'services.serial_service',
                'class': 'SerialService',
                'config_key': 'serial'
            },
            'api': {
                'module': 'services.api_service',
                'class': 'ApiService',
                'config_key': 'api'
            }
        }
        self._running = False
        self._start_time = time.time()

    def register_service(self, service_id: str, module_path: str, class_name: str, config_key: str = None):
        """
        Register a new service type.
        
        Args:
            service_id: Unique identifier for the service
            module_path: Python module path (e.g., 'services.my_service')
            class_name: Name of the service class
            config_key: Key in config for service-specific settings
        """
        with self._lock:
            self._service_registry[service_id] = {
                'module': module_path,
                'class': class_name,
                'config_key': config_key or service_id
            }

    def start(self, service_id: str, **kwargs) -> Any:
        """
        Start a service by ID.
        
        Args:
            service_id: ID of the service to start
            **kwargs: Additional arguments to pass to the service
            
        Returns:
            The started service instance
            
        Raises:
            ValueError: If service_id is not registered
            RuntimeError: If service fails to start
        """
        with self._lock:
            if service_id in self._services:
                if self._services[service_id].status == ServiceStatus.RUNNING:
                    self.logger.warning(f"Service {service_id} is already running")
                    return self._services[service_id].service
                elif self._services[service_id].status == ServiceStatus.STARTING:
                    self.logger.warning(f"Service {service_id} is already starting")
                    return self._services[service_id].service

            if service_id not in self._service_registry:
                raise ValueError(f"Unknown service: {service_id}")

            service_info = self._service_registry[service_id]
            service_config = self.config.get(service_info['config_key'], {})
            
            try:
                # Dynamically import the service module
                module = importlib.import_module(service_info['module'])
                service_class = getattr(module, service_info['class'])
                
                # Create service instance
                service = service_class(
                    logger=self.logger,
                    db=self.db,
                    config=service_config,
                    **kwargs
                )
                
                # Update service info
                service_info = ServiceInfo(
                    name=service_id,
                    service=service,
                    status=ServiceStatus.STARTING,
                    start_time=time.time()
                )
                self._services[service_id] = service_info
                
                # Start the service
                if hasattr(service, 'start'):
                    if hasattr(service, 'is_alive') and not service.is_alive():
                        service.start()
                    elif not hasattr(service, 'is_alive'):
                        service.start()
                
                service_info.status = ServiceStatus.RUNNING
                self.logger.info(f"Service {service_id} started successfully")
                return service
                
            except Exception as e:
                error_msg = f"Failed to start service {service_id}: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                if service_id in self._services:
                    self._services[service_id].status = ServiceStatus.ERROR
                    self._services[service_id].last_error = error_msg
                raise RuntimeError(error_msg) from e

    def stop(self, service_id: str, force: bool = False) -> bool:
        """
        Stop a running service.
        
        Args:
            service_id: ID of the service to stop
            force: If True, force stop the service
            
        Returns:
            bool: True if service was stopped, False otherwise
        """
        with self._lock:
            if service_id not in self._services:
                self.logger.warning(f"Service {service_id} not found")
                return False
                
            service_info = self._services[service_id]
            
            if service_info.status != ServiceStatus.RUNNING:
                self.logger.warning(f"Service {service_id} is not running")
                return False
                
            try:
                service_info.status = ServiceStatus.STOPPING
                service = service_info.service
                
                if hasattr(service, 'stop'):
                    service.stop()
                elif hasattr(service, 'shutdown'):
                    service.shutdown()
                    
                if hasattr(service, 'is_alive'):
                    # Wait for the service to stop
                    timeout = 5.0  # 5 second timeout
                    start_time = time.time()
                    while service.is_alive() and (time.time() - start_time) < timeout:
                        time.sleep(0.1)
                        
                    if service.is_alive() and force:
                        if hasattr(service, 'terminate'):
                            service.terminate()
                            
                service_info.status = ServiceStatus.STOPPED
                service_info.uptime += (time.time() - (service_info.start_time or 0))
                service_info.start_time = None
                self.logger.info(f"Service {service_id} stopped")
                return True
                
            except Exception as e:
                error_msg = f"Error stopping service {service_id}: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                service_info.status = ServiceStatus.ERROR
                service_info.last_error = error_msg
                return False

    def get_service(self, service_id: str) -> Any:
        """
        Get a service instance by ID.
        
        Args:
            service_id: ID of the service to get
            
        Returns:
            The service instance or None if not found
        """
        with self._lock:
            service_info = self._services.get(service_id)
            return service_info.service if service_info else None

    def get_service_info(self, service_id: str) -> Optional[ServiceInfo]:
        """
        Get detailed information about a service.
        
        Args:
            service_id: ID of the service
            
        Returns:
            ServiceInfo or None if service not found
        """
        with self._lock:
            return self._services.get(service_id)

    def list_services(self) -> Dict[str, dict]:
        """
        Get status of all services.
        
        Returns:
            Dictionary mapping service IDs to status dictionaries
        """
        with self._lock:
            snapshot = {}
            for sid, info in self._services.items():
                status = {
                    'status': info.status.name,
                    'running': info.status == ServiceStatus.RUNNING,
                    'uptime': info.uptime + (time.time() - info.start_time if info.start_time else 0),
                    'error': info.last_error
                }
                snapshot[sid] = status
            return snapshot

    def stop_all(self, force: bool = False):
        """
        Stop all running services.
        
        Args:
            force: If True, force stop services
        """
        with self._lock:
            for service_id in list(self._services.keys()):
                self.stop(service_id, force)

    def restart(self, service_id: str) -> bool:
        """
        Restart a service.
        
        Args:
            service_id: ID of the service to restart
            
        Returns:
            bool: True if restart was successful
        """
        with self._lock:
            if self.stop(service_id):
                return self.start(service_id) is not None
            return False

    def is_service_running(self, service_id: str) -> bool:
        """
        Check if a service is running.
        
        Args:
            service_id: ID of the service to check
            
        Returns:
            bool: True if the service is running
        """
        with self._lock:
            if service_id not in self._services:
                return False
            return self._services[service_id].status == ServiceStatus.RUNNING

    def get_service_status(self, service_id: str) -> Optional[ServiceStatus]:
        """
        Get the status of a service.
        
        Args:
            service_id: ID of the service
            
        Returns:
            ServiceStatus or None if service not found
        """
        with self._lock:
            if service_id not in self._services:
                return None
            return self._services[service_id].status

    def __enter__(self):
        """Context manager entry point."""
        self._running = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point - stops all services."""
        self._running = False
        self.stop_all()
        return False