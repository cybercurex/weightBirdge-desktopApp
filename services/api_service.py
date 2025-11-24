from flask import Flask, jsonify, request
import threading
from datetime import datetime
import json
from functools import wraps

from core.config import Config

class ApiService(threading.Thread):
    def __init__(self, logger, service_manager, host=None, port=None):
        super().__init__(daemon=True)
        self.logger = logger
        self.service_manager = service_manager
        self.host = host or Config.FLASK_HOST
        self.port = port or Config.FLASK_PORT
        self.app = Flask('weighbridge_api')
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route('/api/weight', methods=['GET'])
        def get_weight():
            """Get the current stable weight reading"""
            reader = self.service_manager.get_service('serial')
            if not reader or not reader.is_alive():
                return jsonify({
                    'status': 'error',
                    'message': 'Serial service not running'
                }), 503
                
            weight = reader.get_last_stable()
            if weight is None:
                return jsonify({
                    'status': 'no_reading',
                    'message': 'No stable reading available'
                }), 200
                
            self.logger.info(f'API: Weight requested - {weight} kg')
            return jsonify({
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat(),
                'weight_kg': weight
            })

        @self.app.route('/api/readings', methods=['GET'])
        def get_readings():
            """Get recent weight readings"""
            reader = self.service_manager.get_service('serial')
            if not reader or not reader.is_alive():
                return jsonify({
                    'status': 'error',
                    'message': 'Serial service not running'
                }), 503
                
            limit = request.args.get('limit', default=10, type=int)
            readings = getattr(reader, '_readings', [])[-limit:]
            return jsonify({
                'status': 'success',
                'count': len(readings),
                'readings': readings
            })

        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get service status"""
            services = self.service_manager.list_services()
            return jsonify({
                'status': 'success',
                'services': services,
                'timestamp': datetime.utcnow().isoformat()
            })

    def run(self):
        self.logger.info(f'Starting API service on {self.host}:{self.port}')
        try:
            self.app.run(
                host=self.host,
                port=self.port,
                threaded=True,
                use_reloader=False
            )
        except Exception as e:
            self.logger.error(f'API service error: {str(e)}')
            raise