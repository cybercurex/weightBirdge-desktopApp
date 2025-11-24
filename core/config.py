class Config:
    def __init__(self):
        # Default configuration values
        self._config = {
            'admin_password': 'admin123',
            'db_file': 'weighbridge_local.db',
            'flask_host': '127.0.0.1',
            'flask_port': 5000,
            'default_com_port': 'SIM',
            'default_baudrate': 9600,
            'stable_window': 5,
            'stable_threshold': 0.3
        }
    
    def get(self, key, default=None):
        """Get a configuration value by key with an optional default."""
        return self._config.get(key.lower(), default)
    
    def __getattr__(self, name):
        """Allow attribute-style access to config values."""
        name = name.lower()
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"'Config' object has no attribute '{name}'")
    
    def __setattr__(self, name, value):
        """Allow attribute-style setting of config values."""
        name = name.lower()
        if name == '_config':
            super().__setattr__('_config', value)
        else:
            self._config[name] = value
    
    def update(self, config_dict):
        """Update multiple config values from a dictionary."""
        for key, value in config_dict.items():
            self._config[key.lower()] = value
    
    def to_dict(self):
        """Return the configuration as a dictionary."""
        return self._config.copy()