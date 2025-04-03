#!/usr/bin/env python3

import os
import json
import shutil
import argparse
from datetime import datetime
from pathlib import Path

class EnvironmentManager:
    def __init__(self, workspace_root="."):
        self.workspace_root = Path(workspace_root)
        self.environments_dir = self.workspace_root / "environments"
        self.tracking_file = self.workspace_root / "environment_tracking.json"
        self.load_tracking_data()

    def load_tracking_data(self):
        """Load or initialize the environment tracking data."""
        if self.tracking_file.exists():
            with open(self.tracking_file, 'r') as f:
                self.tracking_data = json.load(f)
        else:
            self.tracking_data = {
                "feature_branches": {},
                "staging_references": {},
                "environment_states": {}
            }
            self.save_tracking_data()

    def save_tracking_data(self):
        """Save the current tracking data to file."""
        with open(self.tracking_file, 'w') as f:
            json.dump(self.tracking_data, f, indent=2)

    def track_feature_branch(self, branch_name, microservice_name):
        """Track a new feature branch environment."""
        timestamp = datetime.now().isoformat()
        self.tracking_data["feature_branches"][branch_name] = {
            "microservice": microservice_name,
            "created_at": timestamp,
            "last_updated": timestamp,
            "environment_path": f"environments/development/{microservice_name}/{branch_name}"
        }
        self.save_tracking_data()

    def link_to_staging(self, feature_branch, staging_path):
        """Create a link between a feature branch and its staging deployment."""
        if feature_branch not in self.tracking_data["feature_branches"]:
            raise ValueError(f"Feature branch {feature_branch} not found in tracking data")
        
        self.tracking_data["staging_references"][staging_path] = {
            "source_branch": feature_branch,
            "linked_at": datetime.now().isoformat()
        }
        self.save_tracking_data()

    def preserve_environment(self, source_path, target_path):
        """Preserve an environment by creating a reference instead of copying."""
        source_path = Path(source_path)
        target_path = Path(target_path)
        
        if not source_path.exists():
            raise ValueError(f"Source environment {source_path} does not exist")
        
        # Create parent directories if they don't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # If target already exists, back it up
        if target_path.exists():
            backup_path = target_path.parent / f"{target_path.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.move(target_path, backup_path)
        
        # Create symbolic link
        os.symlink(source_path.absolute(), target_path)
        
        # Update tracking data
        self.tracking_data["environment_states"][str(target_path)] = {
            "type": "symlink",
            "source": str(source_path),
            "created_at": datetime.now().isoformat()
        }
        self.save_tracking_data()

    def is_environment_preserved(self, env_path):
        """Check if an environment is preserved (has active references)."""
        env_path = str(Path(env_path))
        return (
            env_path in self.tracking_data["environment_states"] or
            any(ref["source_branch"] == env_path for ref in self.tracking_data["staging_references"].values())
        )

    def cleanup_environment(self, env_path):
        """Safely cleanup an environment if it's not preserved."""
        env_path = Path(env_path)
        if not self.is_environment_preserved(env_path):
            if env_path.is_symlink():
                env_path.unlink()
            elif env_path.exists():
                shutil.rmtree(env_path)
            
            # Clean up tracking data
            env_path_str = str(env_path)
            if env_path_str in self.tracking_data["environment_states"]:
                del self.tracking_data["environment_states"][env_path_str]
            self.save_tracking_data()

def main():
    parser = argparse.ArgumentParser(description="Manage microservice environments")
    parser.add_argument('action', choices=['track', 'link', 'preserve', 'cleanup'])
    parser.add_argument('--branch', help='Feature branch name')
    parser.add_argument('--microservice', help='Microservice name')
    parser.add_argument('--source', help='Source environment path')
    parser.add_argument('--target', help='Target environment path')
    
    args = parser.parse_args()
    manager = EnvironmentManager()
    
    try:
        if args.action == 'track':
            if not args.branch or not args.microservice:
                raise ValueError("Both --branch and --microservice are required for track action")
            manager.track_feature_branch(args.branch, args.microservice)
        
        elif args.action == 'link':
            if not args.branch or not args.target:
                raise ValueError("Both --branch and --target are required for link action")
            manager.link_to_staging(args.branch, args.target)
        
        elif args.action == 'preserve':
            if not args.source or not args.target:
                raise ValueError("Both --source and --target are required for preserve action")
            manager.preserve_environment(args.source, args.target)
        
        elif args.action == 'cleanup':
            if not args.target:
                raise ValueError("--target is required for cleanup action")
            manager.cleanup_environment(args.target)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main() 