"""
Weighbridge Services Package

This package contains all the service modules for the Weighbridge application.
Services handle the core business logic and external communications.
"""

from .serial_service import SerialService
from .api_service import ApiService
from .service_manager import ServiceManager

# Version of the services package
__version__ = '1.0.0'

# List of services that should be available for import
__all__ = ['SerialService', 'ApiService', 'ServiceManager']

def init_services(logger, config, db):
    """
    Initialize and return all services with their dependencies.
    
    Args:
        logger: The application logger instance
        config: Configuration dictionary
        db: Database connection or session
        
    Returns:
        dict: Dictionary of initialized services
    """
    from .service_manager import ServiceManager
    
    # Initialize service manager
    service_manager = ServiceManager(logger, db, config)
    
    # Initialize and register services
    services = {
        'serial': service_manager.start('serial'),
        'api': service_manager.start('api')
    }
    
    return services

def stop_services(services):
    """
    Stop all running services.
    
    Args:
        services: Dictionary of services to stop
    """
    for service_name, service in services.items():
        if hasattr(service, 'stop'):
            try:
                service.stop()
            except Exception as e:
                if 'logger' in globals():
                    logger.error(f"Error stopping {service_name}: {str(e)}")
                else:
                    print(f"Error stopping {service_name}: {str(e)}")

# Clean up when the module is unloaded
def _cleanup():
    # This will be called when the module is unloaded
    pass

import atexit
atexit.register(_cleanup)