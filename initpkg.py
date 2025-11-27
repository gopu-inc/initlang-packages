#!/usr/bin/env python3
"""
Gestionnaire de paquets INIT - Avec support repository online
"""

import os
import sys
import json
import shutil
import argparse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
INITLANG_HOME = Path.home() / ".initlang"
PACKAGES_DIR = INITLANG_HOME / "packages"
CACHE_DIR = INITLANG_HOME / "cache"
CONFIG_FILE = INITLANG_HOME / "packages.json"

# Repository par défaut
DEFAULT_REPOSITORY = "https://raw.githubusercontent.com/gopu-inc/initlang-packages/main"

class PackageManager:
    def __init__(self):
        self.setup_directories()
        self.load_config()
    
    def setup_directories(self):
        """Crée les répertoires nécessaires"""
        for directory in [INITLANG_HOME, PACKAGES_DIR, CACHE_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def load_config(self):
        """Charge la configuration"""
        self.config = {
            "repository": DEFAULT_REPOSITORY,
            "installed_packages": {}
        }
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.config.update(json.load(f))
            except:
                pass
    
    def save_config(self):
        """Sauvegarde la configuration"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def fetch_package_index(self) -> Dict:
        """Récupère l'index des paquets depuis le repository"""
        cache_file = CACHE_DIR / "index.json"
        
        try:
            url = f"{self.config['repository']}/index.json"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
            
            # Sauvegarder dans le cache
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return data
        except Exception as e:
            print(f"Warning: Could not fetch online index ({e})")
            # Retourner un index vide si échec
            return {}
    
    def install(self, package_names: List[str]):
        """Installe un ou plusieurs paquets depuis le repository"""
        index = self.fetch_package_index()
        
        if not index:
            print("Error: Cannot connect to package repository")
            return
        
        for package_name in package_names:
            self._install_single(package_name, index)
    
    def _install_single(self, package_name: str, index: Dict):
        """Installe un paquet unique depuis le repository"""
        if package_name in self.config["installed_packages"]:
            print(f"Package '{package_name}' is already installed")
            return
        
        if package_name not in index:
            print(f"Package '{package_name}' not found in repository")
            return
        
        package_info = index[package_name]
        print(f"Installing {package_name} v{package_info['version']}...")
        
        try:
            # Télécharger le paquet
            package_url = f"{self.config['repository']}/packages/{package_name}/main.init"
            with urllib.request.urlopen(package_url) as response:
                package_content = response.read().decode()
            
            # Créer le répertoire du paquet
            package_dir = PACKAGES_DIR / package_name
            package_dir.mkdir(exist_ok=True)
            
            # Sauvegarder le fichier principal
            main_file = package_dir / "main.init"
            with open(main_file, 'w') as f:
                f.write(package_content)
            
            # Sauvegarder les métadonnées
            meta_file = package_dir / "package.json"
            with open(meta_file, 'w') as f:
                json.dump(package_info, f, indent=2)
            
            # Mettre à jour la configuration
            self.config["installed_packages"][package_name] = {
                "version": package_info["version"],
                "path": str(package_dir)
            }
            
            self.save_config()
            print(f"✓ {package_name} v{package_info['version']} installed successfully")
            
        except Exception as e:
            print(f"✗ Failed to install {package_name}: {e}")
    
    def create_package(self, package_name: str, version: str = "1.0.0"):
        """Crée un nouveau paquet local"""
        package_dir = PACKAGES_DIR / package_name
        package_dir.mkdir(exist_ok=True)
        
        # Fichier principal
        main_file = package_dir / "main.init"
        if not main_file.exists():
            with open(main_file, 'w') as f:
                f.write(f"""# Package {package_name}

init.log("Package {package_name} loaded!")

fi hello() {{
    init.ger("Hello from {package_name}!")
}}

let version ==> "{version}"
""")
        
        # Métadonnées
        meta_file = package_dir / "package.json"
        with open(meta_file, 'w') as f:
            json.dump({
                "name": package_name,
                "version": version,
                "description": f"Package {package_name} for INITLANG"
            }, f, indent=2)
        
        print(f"✓ Package '{package_name}' created at {package_dir}")
    
    def install_local(self, package_path: str):
        """Installe un paquet local"""
        source_dir = Path(package_path)
        package_name = source_dir.name
        
        if not (source_dir / "main.init").exists():
            print(f"✗ No main.init found in {package_path}")
            return
        
        # Copier le paquet
        target_dir = PACKAGES_DIR / package_name
        if target_dir.exists():
            shutil.rmtree(target_dir)
        
        shutil.copytree(source_dir, target_dir)
        
        # Mettre à jour la configuration
        self.config["installed_packages"][package_name] = {
            "version": "1.0.0",
            "path": str(target_dir)
        }
        self.save_config()
        
        print(f"✓ Package '{package_name}' installed")
    
    def list_installed(self):
        """Liste les paquets installés"""
        if not self.config["installed_packages"]:
