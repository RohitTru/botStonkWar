#!/usr/bin/env python3
import sys
import json
import os
import fcntl
import time
import shutil
import tempfile
from datetime import datetime

class PortManagerError(Exception):
    """Custom exception for PortManager errors"""
    pass

class PortManager:
    def __init__(self, ports_file="ports.json", max_retries=3, retry_delay=1):
        self.ports_file = ports_file
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backup_dir = os.path.join(os.path.dirname(ports_file), '.port_manager_backups')
        os.makedirs(self.backup_dir, exist_ok=True)
        self.ensure_ports_file_exists()

    def create_backup(self):
        """Create a backup of the ports file"""
        if not os.path.exists(self.ports_file):
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(self.backup_dir, f'ports_{timestamp}.json')
        shutil.copy2(self.ports_file, backup_file)
        
        # Keep only last 5 backups
        backups = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('ports_')])
        for old_backup in backups[:-5]:
            os.remove(os.path.join(self.backup_dir, old_backup))

    def atomic_write(self, data):
        """Write data atomically using a temporary file"""
        # Create a temporary file in the same directory
        temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(self.ports_file))
        try:
            with os.fdopen(temp_fd, 'w') as temp_file:
                json.dump(data, temp_file, indent=2)
            # Atomic rename
            os.replace(temp_path, self.ports_file)
        except Exception:
            # Clean up the temporary file if something goes wrong
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def with_retries(self, func):
        """Decorator to implement retry logic"""
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    continue
            raise PortManagerError(f"Operation failed after {self.max_retries} attempts: {last_error}")
        return wrapper

    def ensure_ports_file_exists(self):
        if not os.path.exists(self.ports_file):
            self.atomic_write({
                "environments": {
                    "development": {
                        "port_range": {"start": 5000, "end": 5999},
                        "assignments": {}
                    },
                    "staging": {
                        "port_range": {"start": 6000, "end": 6999},
                        "assignments": {}
                    },
                    "production": {
                        "port_range": {"start": 7000, "end": 7999},
                        "assignments": {}
                    }
                }
            })

    def get_environment_for_branch(self, branch_name):
        if branch_name.endswith("/master"):
            return "production"
        elif branch_name.endswith("/staging"):
            return "staging"
        else:
            return "development"

    @property
    def lock_file(self):
        """Get the path to the lock file"""
        return f"{self.ports_file}.lock"

    def get_next_available_port(self, branch_name, target_env=None):
        return self.with_retries(self._get_next_available_port)(branch_name, target_env)

    def _get_next_available_port(self, branch_name, target_env=None):
        self.create_backup()
        with open(self.ports_file, 'r') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                data = json.load(f)
                
                # Determine environment
                env = target_env or self.get_environment_for_branch(branch_name)
                if env not in data["environments"]:
                    raise PortManagerError(f"Invalid environment: {env}")
                
                env_data = data["environments"][env]
                
                # Get port range for environment
                start_port = env_data["port_range"]["start"]
                end_port = env_data["port_range"]["end"]
                
                # Get used ports
                used_ports = set(env_data["assignments"].values())
                
                # Find next available port
                for port in range(start_port, end_port + 1):
                    if port not in used_ports:
                        # Assign port
                        env_data["assignments"][branch_name] = port
                        
                        # Write changes atomically
                        self.atomic_write(data)
                        return port
                
                raise PortManagerError(f"No available ports in range {start_port}-{end_port}")
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def release_port(self, branch_name, environment=None):
        return self.with_retries(self._release_port)(branch_name, environment)

    def _release_port(self, branch_name, environment=None):
        self.create_backup()
        with open(self.ports_file, 'r') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                data = json.load(f)
                
                # Determine environment
                env = environment or self.get_environment_for_branch(branch_name)
                if env not in data["environments"]:
                    raise PortManagerError(f"Invalid environment: {env}")
                
                # Remove port assignment if it exists
                if branch_name in data["environments"][env]["assignments"]:
                    del data["environments"][env]["assignments"][branch_name]
                    
                    # Write changes atomically
                    self.atomic_write(data)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def migrate_port(self, branch_name, from_env, to_env):
        return self.with_retries(self._migrate_port)(branch_name, from_env, to_env)

    def _migrate_port(self, branch_name, from_env, to_env):
        self.create_backup()
        with open(self.ports_file, 'r') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                data = json.load(f)
                
                # Validate environments
                if from_env not in data["environments"] or to_env not in data["environments"]:
                    raise PortManagerError(f"Invalid environment(s): {from_env} and/or {to_env}")
                
                # Get target environment port range
                target_env_data = data["environments"][to_env]
                start_port = target_env_data["port_range"]["start"]
                end_port = target_env_data["port_range"]["end"]
                
                # Get used ports in target environment
                used_ports = set(target_env_data["assignments"].values())
                
                # Find next available port in target environment
                for port in range(start_port, end_port + 1):
                    if port not in used_ports:
                        # Assign new port in target environment
                        target_env_data["assignments"][branch_name] = port
                        
                        # Write changes atomically
                        self.atomic_write(data)
                        return port
                
                raise PortManagerError(f"No available ports in target environment range {start_port}-{end_port}")
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: port_manager.py [assign|release|migrate] <branch_name> [from_env] [to_env]")
        sys.exit(1)

    action = sys.argv[1]
    branch_name = sys.argv[2]
    
    manager = PortManager()
    
    try:
        if action == "assign":
            target_env = sys.argv[3] if len(sys.argv) > 3 else None
            port = manager.get_next_available_port(branch_name, target_env)
            # Output in GitHub Actions environment format
            print(f"APP_PORT={port}")
        elif action == "release":
            environment = sys.argv[3] if len(sys.argv) > 3 else None
            manager.release_port(branch_name, environment)
        elif action == "migrate":
            if len(sys.argv) < 5:
                print("Error: migrate requires from_env and to_env parameters")
                sys.exit(1)
            from_env = sys.argv[3]
            to_env = sys.argv[4]
            new_port = manager.migrate_port(branch_name, from_env, to_env)
            print(f"APP_PORT={new_port}")
        else:
            print(f"Unknown action: {action}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1) 