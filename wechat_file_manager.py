import os
import hashlib
from pathlib import Path
import shutil
from collections import defaultdict
import yaml
from datetime import datetime
import sqlite3
from typing import List, Tuple
from tqdm import tqdm  # Add this import at the top
import argparse

def wfm_init():
    """Initialize WeChat File Manager folders and configuration"""
    default_config_path = Path(__file__).parent / 'config.yaml'
    config_path = Path.home() / 'config_wechat_file_manager.yaml'
    
    if not config_path.exists():
        shutil.copy2(default_config_path, config_path)
        print(f"Created configuration file at: {config_path}")
    
    # Load config to create storage directory
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

class WeChatFileManager:
    """
    A class to manage WeChat files by deduplicating and organizing them efficiently.
    
    This class scans WeChat directories for media files, identifies duplicates using MD5 hashes,
    and creates a centralized storage with symbolic links to save disk space.
    """

    def __init__(self, config_path):
        """
        Initialize the WeChat file manager.

        Args:
            config_path (str or Path): Path to the YAML configuration file
        """
        self.config_path = config_path
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize paths and storage
        self.wechat_path = Path(self.config['paths']['wechat']).expanduser()
        self.storage_path = Path(self.config['paths']['storage']).expanduser()
        self.db_path = self.storage_path / 'file_hashes.db'
        self.last_run = self.config.get('state', {}).get('last_run')
        self.min_file_size = self.config['settings'].get('min_file_size', 0) * 1024 * 1024
        self.skip_patterns = self.config['settings'].get('skip_patterns', [])
        self.preserve_originals = self.config['settings'].get('preserve_originals', False)
        self.target_folders = self.config['settings'].get('target_folders', ['FileStorage', 'Image', 'Video'])
        self.init_database()
        self.file_hashes = defaultdict(list)
        self.db_conn = sqlite3.connect(self.db_path)  # Create persistent connection

    def __del__(self):
        """Cleanup database connection when object is destroyed"""
        if hasattr(self, 'db_conn'):
            self.db_conn.close()

    def init_database(self):
        """Initialize SQLite database for file hashes"""
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS file_hashes (
                    hash TEXT,
                    file_path TEXT,
                    mtime FLOAT,
                    PRIMARY KEY (hash, file_path)
                )
            ''')

    def load_existing_hashes(self) -> List[Tuple[str, Path, float]]:
        """Load existing hashes from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT hash, file_path, mtime FROM file_hashes')
            return [(row[0], Path(row[1]), row[2]) for row in cursor.fetchall()]

    def save_file_hash(self, file_hash: str, file_path: Path):
        """Save file hash to database"""
        mtime = file_path.stat().st_mtime
        self.db_conn.execute(
            'INSERT OR REPLACE INTO file_hashes (hash, file_path, mtime) VALUES (?, ?, ?)',
            (file_hash, str(file_path), mtime)
        )
        self.db_conn.commit()  # Commit changes periodically

    def should_process_directory(self, dir_path):
        """
        Check if a directory needs to be processed based on its modification time.

        Args:
            dir_path (Path): Directory path to check

        Returns:
            bool: True if directory should be processed, False otherwise
        """
        if not self.last_run:
            return True
        try:
            dir_mtime = datetime.fromtimestamp(dir_path.stat().st_mtime)
            last_run_time = datetime.fromisoformat(self.last_run)
            return dir_mtime > last_run_time
        except:
            return True

    def should_process_file(self, file_path):
        try:
            # Check file size requirement
            file_size = file_path.stat().st_size
            if file_size < self.min_file_size:
                return False

            # Skip files matching any of the patterns
            for pattern in self.skip_patterns:
                if pattern in file_path.name:
                    return False

            return True
        except:
            return True

    def clean_filename(self, filename: str, file_hash: str) -> str:
        """Remove duplicate indicators and append hash prefix to filename"""
        import re
        base_name = re.sub(r' \(\d+\)(?=\.[^.]+$)', '', filename)
        name_parts = base_name.rsplit('.', 1)
        return f"{name_parts[0]}_{file_hash[:5]}.{name_parts[1]}"

    def process_files(self):
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Get list of valid user directories first
        user_dirs = [d for d in self.wechat_path.iterdir() if d.is_dir()]
        
        # Create progress bar for user directories
        for user_dir in tqdm(user_dirs, desc="Processing WeChat users"):
            if not self.should_process_directory(user_dir):
                continue
            
            for target in self.target_folders:
                target_dir = user_dir / target
                if not target_dir.exists() or not self.should_process_directory(target_dir):
                    continue
                
                storage_target_dir = self.storage_path / target
                storage_target_dir.mkdir(exist_ok=True)
                
                for file_path in target_dir.rglob('*'):
                    if file_path.is_file() and not file_path.is_symlink() and self.should_process_file(file_path):
                        file_hash = self.calculate_md5(file_path)
                        
                        # Check if this hash already exists in database
                        cursor = self.db_conn.execute('SELECT file_path FROM file_hashes WHERE hash = ? AND file_path LIKE ?',
                                                    (file_hash, str(self.storage_path) + '%'))
                        stored_file = cursor.fetchone()
                        
                        if stored_file:
                            new_path = Path(stored_file[0])
                        else:
                            clean_name = self.clean_filename(file_path.name, file_hash)
                            new_path = storage_target_dir / clean_name
                            if self.preserve_originals:
                                shutil.copy2(str(file_path), str(new_path))
                            else:
                                shutil.move(str(file_path), str(new_path))
                        
                        if not self.preserve_originals:
                            if file_path.exists():
                                file_path.unlink()
                            os.symlink(str(new_path), str(file_path))
                        
                        self.save_file_hash(file_hash, file_path)

    def update_last_run(self):
        """Update the last run timestamp in config file"""
        self.config['state'] = self.config.get('state', {})
        self.config['state']['last_run'] = datetime.now().isoformat()
        
        with open(self.config_path, 'w') as f:
            yaml.safe_dump(self.config, f)

    def calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file."""
        return hashlib.md5(file_path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description='WeChat File Manager')
    parser.add_argument('command', choices=['init', 'run'], help='Command to execute')
    args = parser.parse_args()
    
    if args.command == 'init':
        wfm_init()
    elif args.command == 'run':
        config_path = Path.home() / 'config_wechat_file_manager.yaml'
        if not config_path.exists():
            print("Configuration not found. Please run 'wfm init' first.")
            return
        
        manager = WeChatFileManager(config_path)
        manager.process_files()
        manager.update_last_run()

if __name__ == "__main__":
    main()