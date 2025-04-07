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
                "port_ranges": {
                    "feature": {"start": 5000, "end": 5999},
                    "main": {"start": 7000, "end": 7999}
                },
                "assignments": {}
            })

    def get_port_range(self, branch_name):
        """Determine which port range to use based on branch name"""
        # Split branch name if it contains a slash
        if "/" in branch_name:
            _, branch = branch_name.split("/")
        else:
            branch = branch_name
        
        if branch == "main":
            return "main"
        return "feature"

    def get_next_available_port(self, branch_name):
        return self.with_retries(self._get_next_available_port)(branch_name)

    def _get_next_available_port(self, branch_name):
        self.create_backup()
        with open(self.ports_file, 'r') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                data = json.load(f)
                
                # Get appropriate port range
                port_range = self.get_port_range(branch_name)
                start_port = data["port_ranges"][port_range]["start"]
                end_port = data["port_ranges"][port_range]["end"]
                
                # Get used ports
                used_ports = set(data["assignments"].values())
                
                # Find next available port
                for port in range(start_port, end_port + 1):
                    if port not in used_ports:
                        # Assign port
                        data["assignments"][branch_name] = port
                        
                        # Write changes atomically
                        self.atomic_write(data)
                        return port
                
                raise PortManagerError(f"No available ports in {port_range} range {start_port}-{end_port}")
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def release_port(self, branch_name):
        return self.with_retries(self._release_port)(branch_name)

    def _release_port(self, branch_name):
        self.create_backup()
        with open(self.ports_file, 'r') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                data = json.load(f)
                
                # Remove port assignment if it exists
                if branch_name in data["assignments"]:
                    del data["assignments"][branch_name]
                    
                    # Write changes atomically
                    self.atomic_write(data)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def migrate_to_main(self, branch_name):
        """Migrate a feature branch's port to the main range"""
        return self.with_retries(self._migrate_to_main)(branch_name)

    def _migrate_to_main(self, branch_name):
        self.create_backup()
        with open(self.ports_file, 'r') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                data = json.load(f)
                
                # Get current port
                if branch_name not in data["assignments"]:
                    raise PortManagerError(f"No port assigned for branch {branch_name}")
                
                current_port = data["assignments"][branch_name]
                
                # Get main port range
                start_port = data["port_ranges"]["main"]["start"]
                end_port = data["port_ranges"]["main"]["end"]
                
                # Get used ports
                used_ports = set(data["assignments"].values())
                
                # Find next available port in main range
                for port in range(start_port, end_port + 1):
                    if port not in used_ports:
                        # Assign new port
                        data["assignments"][branch_name] = port
                        
                        # Write changes atomically
                        self.atomic_write(data)
                        return port
                
                raise PortManagerError(f"No available ports in main range {start_port}-{end_port}")
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: port_manager.py [assign|release|migrate] <branch_name>")
        sys.exit(1)

    action = sys.argv[1]
    branch_name = sys.argv[2]
    
    manager = PortManager()
    
    try:
        if action == "assign":
            print(f"Debug: Assigning port for {branch_name}", file=sys.stderr)
            port = manager.get_next_available_port(branch_name)
            print(f"Debug: Port assigned: {port}", file=sys.stderr)
            # Output in GitHub Actions environment format
            print(f"APP_PORT={port}")
            # Also output to stderr for debugging
            print(f"Debug: Setting APP_PORT={port}", file=sys.stderr)
        elif action == "release":
            manager.release_port(branch_name)
        elif action == "migrate":
            port = manager.migrate_to_main(branch_name)
            print(f"APP_PORT={port}")
        else:
            print(f"Unknown action: {action}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1) 