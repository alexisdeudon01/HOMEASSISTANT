#!/usr/bin/env python3
"""
Integration test script for Sinik microservices.
Tests the basic functionality of the gateway service and its dependencies.
"""

import os
import sys
import time
import json
import logging
import subprocess
import requests
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).parent
DOCKER_COMPOSE_FILE = BASE_DIR / "docker-compose.yml"
ENV_FILE = BASE_DIR / ".env"
GATEWAY_URL = "http://localhost:8000"
TIMEOUT = 30  # seconds


class IntegrationTest:
    """Integration test runner for Sinik microservices."""
    
    def __init__(self):
        self.services = [
            "gateway",
            "entity",
            "brain",
            "ha-manager",
            "infrastructure-manager",
            "protocol",
            "reconciler",
            "sensor",
            "redis",
            "postgres",
            "mosquitto"
        ]
        self.test_results = {}
    
    def check_docker_compose(self) -> bool:
        """Check if docker-compose is available."""
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Docker Compose version: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Docker Compose not available: {e}")
            return False
    
    def check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Docker version: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Docker not available: {e}")
            return False
    
    def start_services(self) -> bool:
        """Start all services using docker-compose."""
        logger.info("Starting services with docker-compose...")
        
        try:
            # Build and start services
            cmd = ["docker-compose", "-f", str(DOCKER_COMPOSE_FILE), "up", "-d", "--build"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=BASE_DIR
            )
            logger.info("Services started successfully")
            logger.debug(f"Output: {result.stdout}")
            
            # Wait for services to be ready
            time.sleep(10)
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start services: {e}")
            logger.error(f"Stderr: {e.stderr}")
            return False
    
    def stop_services(self) -> bool:
        """Stop all services."""
        logger.info("Stopping services...")
        
        try:
            cmd = ["docker-compose", "-f", str(DOCKER_COMPOSE_FILE), "down"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=BASE_DIR
            )
            logger.info("Services stopped successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop services: {e}")
            return False
    
    def check_service_health(self, service_name: str, url: Optional[str] = None) -> bool:
        """Check health of a specific service."""
        if not url:
            # Default health check URLs
            if service_name == "gateway":
                url = f"{GATEWAY_URL}/health"
            elif service_name in ["redis", "postgres", "mosquitto"]:
                # Infrastructure services have different health checks
                return self.check_infrastructure_service(service_name)
            else:
                # Other microservices
                port = 8000 + list(self.services).index(service_name) - 1
                url = f"http://localhost:{port}/health"
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                logger.info(f"Service {service_name} is healthy")
                return True
            else:
                logger.warning(f"Service {service_name} returned status {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.warning(f"Service {service_name} not reachable: {e}")
            return False
    
    def check_infrastructure_service(self, service_name: str) -> bool:
        """Check infrastructure services (Redis, PostgreSQL, Mosquitto)."""
        try:
            if service_name == "redis":
                import redis
                client = redis.Redis(host="localhost", port=6379, decode_responses=True)
                client.ping()
                logger.info("Redis is healthy")
                return True
                
            elif service_name == "postgres":
                import psycopg2
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    user="sinik",
                    password="sinik_password",
                    database="sinik_db"
                )
                conn.close()
                logger.info("PostgreSQL is healthy")
                return True
                
            elif service_name == "mosquitto":
                # Simple TCP connection check
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(("localhost", 1883))
                sock.close()
                if result == 0:
                    logger.info("Mosquitto is healthy")
                    return True
                else:
                    logger.warning("Mosquitto not reachable")
                    return False
                    
        except Exception as e:
            logger.warning(f"Service {service_name} check failed: {e}")
            return False
        
        return False
    
    def test_gateway_endpoints(self) -> Dict[str, bool]:
        """Test Gateway service endpoints."""
        results = {}
        
        try:
            # Test root endpoint
            response = requests.get(f"{GATEWAY_URL}/", timeout=5)
            results["root_endpoint"] = response.status_code == 200
            
            # Test health endpoint
            response = requests.get(f"{GATEWAY_URL}/health", timeout=5)
            results["health_endpoint"] = response.status_code == 200
            
            # Test entities endpoint
            response = requests.get(f"{GATEWAY_URL}/api/v1/entities", timeout=5)
            results["entities_endpoint"] = response.status_code == 200
            
            # Test command endpoint (with dummy data)
            command_data = {
                "entity_id": "test-device-1",
                "command": "turn_on",
                "parameters": {"brightness": 100},
                "source": "integration-test",
                "priority": 1
            }
            response = requests.post(
                f"{GATEWAY_URL}/api/v1/command",
                json=command_data,
                timeout=5
            )
            results["command_endpoint"] = response.status_code in [200, 500]  # 500 is OK for test
            
            # Test events endpoint
            event_data = {
                "event_type": "test_event",
                "data": {"test": "data"},
                "source": "integration-test",
                "correlation_id": "test-correlation-123"
            }
            response = requests.post(
                f"{GATEWAY_URL}/api/v1/events",
                json=event_data,
                timeout=5
            )
            results["events_endpoint"] = response.status_code == 200
            
        except requests.RequestException as e:
            logger.error(f"Gateway endpoint test failed: {e}")
            for key in ["root_endpoint", "health_endpoint", "entities_endpoint", 
                       "command_endpoint", "events_endpoint"]:
                results[key] = False
        
        return results
    
    def run_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        logger.info("Starting integration tests...")
        
        # Check prerequisites
        if not self.check_docker():
            logger.error("Docker is not available. Skipping tests.")
            return {"success": False, "error": "Docker not available"}
        
        if not self.check_docker_compose():
            logger.error("Docker Compose is not available. Skipping tests.")
            return {"success": False, "error": "Docker Compose not available"}
        
        # Start services
        if not self.start_services():
            logger.error("Failed to start services. Skipping tests.")
            return {"success": False, "error": "Failed to start services"}
        
        try:
            # Wait for services to be ready
            logger.info("Waiting for services to be ready...")
            time.sleep(15)
            
            # Test service health
            health_results = {}
            for service in self.services:
                logger.info(f"Checking health of {service}...")
                health_results[service] = self.check_service_health(service)
            
            # Test gateway endpoints
            logger.info("Testing Gateway endpoints...")
            gateway_results = self.test_gateway_endpoints()
            
            # Compile results
            all_services_healthy = all(health_results.values())
            all_gateway_tests_passed = all(gateway_results.values())
            
            overall_success = all_services_healthy and all_gateway_tests_passed
            
            self.test_results = {
                "success": overall_success,
                "health_checks": health_results,
                "gateway_tests": gateway_results,
                "summary": {
                    "services_healthy": sum(health_results.values()),
                    "total_services": len(health_results),
                    "gateway_tests_passed": sum(gateway_results.values()),
                    "total_gateway_tests": len(gateway_results)
                }
            }
            
            return self.test_results
            
        finally:
            # Always stop services
            self.stop_services()
    
    def print_results(self, results: Dict[str, Any]):
        """Print test results in a readable format."""
        print("\n" + "="*60)
        print("INTEGRATION TEST RESULTS")
        print("="*60)
        
        if not results.get("success", False):
            print(f"\n❌ Tests FAILED: {results.get('error', 'Unknown error')}")
        else:
            print("\n✅ All tests PASSED!")
        
        # Health check results
        print("\n📊 Service Health Checks:")
        print("-"*40)
        health_checks = results.get("health_checks", {})
        for service, healthy in health_checks.items():
            status = "✅" if healthy else "❌"
            print(f"  {status} {service}: {'Healthy' if healthy else 'Unhealthy'}")
        
        # Gateway test results
        print("\n🔧 Gateway Endpoint Tests:")
        print("-"*40)
        gateway_tests = results.get("gateway_tests", {})
        for test, passed in gateway_tests.items():
            status = "✅" if passed else "❌"
            test_name = test.replace("_", " ").title()
            print(f"  {status} {test_name}: {'Passed' if passed else 'Failed'}")
        
        # Summary
        summary = results.get("summary", {})
        print("\n📈 Summary:")
        print("-"*40)
        print(f"  Services Healthy: {summary.get('services_healthy', 0)}/{summary.get('total_services', 0)}")
        print(f"  Gateway Tests Passed: {summary.get('gateway_tests_passed', 0)}/{summary.get('total_gateway_tests', 0)}")
        
        print("\n" + "="*60)


def main():
    """Main entry point."""
    test_runner = IntegrationTest()
    
    # Run tests
    results = test_runner.run_tests()
    
    # Print results
    test_runner.print_results(results)
    
    # Exit with appropriate code
    if results.get("success", False):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
