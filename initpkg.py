#!/usr/bin/env python3
"""
Gestionnaire de paquets INIT - Version corrigée avec téléchargement GitHub
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

# Repository GitHub
GITHUB_REPO = "https://raw.githubusercontent.com/gopu-inc/initlang-packages/main"

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
            "repository": GITHUB_REPO,
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
        """Récupère l'index des paquets depuis GitHub"""
        cache_file = CACHE_DIR / "index.json"
        
        try:
            url = f"{GITHUB_REPO}/index.json"
            print(f"Fetching package index from {url}...")
            
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
            
            # Sauvegarder dans le cache
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✓ Found {len(data)} packages in repository")
            return data
            
        except Exception as e:
            print(f"✗ Error fetching package index: {e}")
            return {}
    
    def download_package(self, package_name: str, package_info: Dict) -> bool:
        """Télécharge et installe un paquet depuis GitHub"""
        try:
            # URLs des fichiers sur GitHub
            main_url = f"{GITHUB_REPO}/packages/{package_name}/main.init"
            meta_url = f"{GITHUB_REPO}/packages/{package_name}/package.json"
            
            print(f"Downloading {package_name} from GitHub...")
            
            # Créer le répertoire du paquet
            package_dir = PACKAGES_DIR / package_name
            package_dir.mkdir(exist_ok=True)
            
            # Télécharger le fichier principal
            try:
                with urllib.request.urlopen(main_url) as response:
                    package_content = response.read().decode()
                
                with open(package_dir / "main.init", 'w') as f:
                    f.write(package_content)
            except Exception as e:
                print(f"✗ Could not download main.init: {e}")
                return False
            
            # Télécharger les métadonnées
            try:
                with urllib.request.urlopen(meta_url) as response:
                    meta_content = response.read().decode()
                
                with open(package_dir / "package.json", 'w') as f:
                    f.write(meta_content)
            except:
                # Créer des métadonnées basiques si non disponibles
                with open(package_dir / "package.json", 'w') as f:
                    json.dump({
                        "name": package_name,
                        "version": package_info.get("version", "1.0.0"),
                        "description": package_info.get("description", "")
                    }, f, indent=2)
            
            # Mettre à jour la configuration
            self.config["installed_packages"][package_name] = {
                "version": package_info.get("version", "1.0.0"),
                "path": str(package_dir),
                "source": "github"
            }
            
            self.save_config()
            return True
            
        except Exception as e:
            print(f"✗ Download failed: {e}")
            return False
    
    def install(self, package_names: List[str]):
        """Installe un ou plusieurs paquets depuis GitHub"""
        index = self.fetch_package_index()
        
        if not index:
            print("✗ Cannot connect to package repository")
            return
        
        for package_name in package_names:
            self._install_single(package_name, index)
    
    def _install_single(self, package_name: str, index: Dict):
        """Installe un paquet unique"""
        if package_name in self.config["installed_packages"]:
            print(f"ℹ Package '{package_name}' is already installed")
            return
        
        if package_name not in index:
            print(f"✗ Package '{package_name}' not found in repository")
            print("Available packages:", ", ".join(index.keys()))
            return
        
        package_info = index[package_name]
        print(f"📦 Installing {package_name} v{package_info['version']}...")
        
        if self.download_package(package_name, package_info):
            print(f"✅ {package_name} v{package_info['version']} installed successfully")
            
            # Installer les dépendances
            dependencies = package_info.get("dependencies", [])
            if dependencies:
                print(f"📦 Installing dependencies: {', '.join(dependencies)}")
                for dep in dependencies:
                    if dep not in self.config["installed_packages"]:
                        self._install_single(dep, index)
        else:
            print(f"❌ Failed to install {package_name}")
    
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
        
        print(f"✅ Package '{package_name}' created at {package_dir}")
    
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
            "path": str(target_dir),
            "source": "local"
        }
        self.save_config()
        
        print(f"✅ Package '{package_name}' installed")
    
    def list_installed(self):
        """Liste les paquets installés"""
        if not self.config["installed_packages"]:
            print("📭 No packages installed")
            return
        
        print("📦 Installed packages:")
        for name, info in self.config["installed_packages"].items():
            source = info.get("source", "unknown")
            print(f"  {name} v{info['version']} ({source})")
    
    def list_available(self):
        """Liste les paquets disponibles sur GitHub"""
        index = self.fetch_package_index()
        
        if not index:
            print("❌ Cannot fetch available packages")
            return
        
        print("📚 Available packages:")
        for name, info in index.items():
            installed = "✅" if name in self.config["installed_packages"] else "  "
            print(f"  {installed} {name} v{info['version']} - {info.get('description', '')}")
    
    def search(self, query: str):
        """Recherche des paquets"""
        index = self.fetch_package_index()
        
        results = []
        for name, info in index.items():
            search_text = f"{name} {info.get('description', '')} {' '.join(info.get('keywords', []))}".lower()
            if query.lower() in search_text:
                results.append((name, info))
        
        if not results:
            print(f"🔍 No packages found for '{query}'")
            return
        
        print(f"🔍 Search results for '{query}':")
        for name, info in results:
            installed = "✅" if name in self.config["installed_packages"] else "  "
            print(f"  {installed} {name} v{info['version']} - {info.get('description', '')}")
    
    def uninstall(self, package_name: str):
        """Désinstalle un paquet"""
        if package_name not in self.config["installed_packages"]:
            print(f"ℹ Package '{package_name}' is not installed")
            return
        
        package_dir = PACKAGES_DIR / package_name
        if package_dir.exists():
            shutil.rmtree(package_dir)
        
        del self.config["installed_packages"][package_name]
        self.save_config()
        
        print(f"✅ Package '{package_name}' uninstalled")
    
    def info(self, package_name: str):
        """Affiche les informations d'un paquet"""
        index = self.fetch_package_index()
        
        if package_name in index:
            info = index[package_name]
            print(f"📦 Package: {package_name}")
            print(f"📋 Version: {info['version']}")
            print(f"📝 Description: {info.get('description', 'No description')}")
            print(f"👤 Author: {info.get('author', 'Unknown')}")
            print(f"📄 License: {info.get('license', 'Unknown')}")
            
            if 'repository' in info:
                print(f"🔗 Repository: {info['repository']}")
            
            if 'dependencies' in info and info['dependencies']:
                print(f"📦 Dependencies: {', '.join(info['dependencies'])}")
            
            if 'keywords' in info and info['keywords']:
                print(f"🏷️ Keywords: {', '.join(info['keywords'])}")
            
            if 'features' in info:
                print("✨ Features:")
                for feature in info['features']:
                    print(f"  • {feature}")
            
            if package_name in self.config["installed_packages"]:
                print("✅ Status: Installed")
            else:
                print("📥 Status: Not installed")
        else:
            print(f"❌ Package '{package_name}' not found")
    
    def update_index(self):
        """Met à jour l'index des paquets"""
        cache_file = CACHE_DIR / "index.json"
        if cache_file.exists():
            cache_file.unlink()
        
        index = self.fetch_package_index()
        if index:
            print(f"✅ Package index updated ({len(index)} packages available)")

def show_help():
    print("""
🎯 INIT Package Manager

Usage:
  initpkg [COMMAND] [ARGS]

Commands:
  install <package...>    Install packages from GitHub
  uninstall <package...>  Uninstall packages
  create <name>           Create a new local package
  install-local <path>    Install local package
  list                    List installed packages
  available               List available packages on GitHub
  search <query>          Search packages
  info <package>          Show package information
  update                  Update package index

Examples:
  initpkg install math strings
  initpkg search http
  initpkg list
  initpkg available
  initpkg info math
  initpkg create mypackage
    """)

def main():
    parser = argparse.ArgumentParser(description="INIT Package Manager", add_help=False)
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('args', nargs='*', help='Command arguments')
    
    args = parser.parse_args()
    
    pm = PackageManager()
    
    if not args.command or args.command in ['-h', '--help']:
        show_help()
        return
    
    try:
        if args.command == 'install':
            if not args.args:
                print("❌ Error: Please specify packages to install")
                return
            pm.install(args.args)
        
        elif args.command == 'uninstall':
            if not args.args:
                print("❌ Error: Please specify packages to uninstall")
                return
            for package in args.args:
                pm.uninstall(package)
        
        elif args.command == 'create':
            if not args.args:
                print("❌ Error: Please specify package name")
                return
            pm.create_package(args.args[0])
        
        elif args.command == 'install-local':
            if not args.args:
                print("❌ Error: Please specify package path")
                return
            pm.install_local(args.args[0])
        
        elif args.command == 'list':
            pm.list_installed()
        
        elif args.command == 'available':
            pm.list_available()
        
        elif args.command == 'search':
            if not args.args:
                print("❌ Error: Please specify search query")
                return
            pm.search(args.args[0])
        
        elif args.command == 'info':
            if not args.args:
                print("❌ Error: Please specify package name")
                return
            pm.info(args.args[0])
        
        elif args.command == 'update':
            pm.update_index()
        
        else:
            print(f"❌ Unknown command: {args.command}")
            show_help()
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
