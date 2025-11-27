#!/usr/bin/env python3
"""
Gestionnaire de paquets INIT - Version corrigée avec animations
Commande: initl
"""

import os
import sys
import json
import shutil
import argparse
import urllib.request
import time
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
INITLANG_HOME = Path.home() / ".initlang"
PACKAGES_DIR = INITLANG_HOME / "packages"
CACHE_DIR = INITLANG_HOME / "cache"
CONFIG_FILE = INITLANG_HOME / "packages.json"

# Repository GitHub
GITHUB_REPO = "https://raw.githubusercontent.com/gopu-inc/initlang-packages/main"

class InitAnimations:
    """Animations stylisées pour INITLANG"""
    
    @staticmethod
    def show_banner():
        """Banner d'introduction"""
        print("\033[95m" + "✨" * 50)
        print("           🚀 INIT PACKAGE MANAGER 🚀")
        print("✨" * 50 + "\033[0m")
        print("📦 Gestionnaire de paquets officiel pour INITLANG")
        print("🔗 Repository: github.com/gopu-inc/initlang-packages")
        print("\033[96m" + "─" * 50 + "\033[0m")
    
    @staticmethod
    def loading_animation(texte: str, duree: int = 2):
        """Animation de chargement"""
        phases = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        
        start_time = time.time()
        while time.time() - start_time < duree:
            for phase in phases:
                if time.time() - start_time >= duree:
                    break
                sys.stdout.write(f"\r{phase} \033[96m{texte}\033[0m")
                sys.stdout.flush()
                time.sleep(0.1)
        
        print(f"\r✅ \033[92m{texte}\033[0m")
    
    @staticmethod
    def progress_bar(etape: str, progression: int, total: int):
        """Barre de progression"""
        pourcentage = int((progression / total) * 100) if total > 0 else 0
        largeur = 30
        blocs = int((progression / total) * largeur) if total > 0 else 0
        
        barre = "[" + "█" * blocs + "░" * (largeur - blocs) + "]"
        print(f"\r{etape} {barre} {pourcentage}%", end="", flush=True)
    
    @staticmethod
    def download_animation(package: str, etape: str):
        """Animation de téléchargement"""
        animations = ["📥", "📤", "🔍", "⚡"]
        anim = animations[int(time.time() * 2) % len(animations)]
        print(f"\r{anim} \033[94m{package}\033[0m - {etape}", end="", flush=True)

class PackageManager:
    def __init__(self):
        self.setup_directories()
        self.load_config()
        self.anim = InitAnimations()
    
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
            # Essayer d'abord le cache
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    return json.load(f)
            
            # Télécharger depuis GitHub
            url = f"{GITHUB_REPO}/index.json"
            self.anim.loading_animation("Connexion au repository GitHub", 1)
            
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
            
            # Sauvegarder dans le cache
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ \033[92mIndex mis à jour ({len(data)} paquets disponibles)\033[0m")
            return data
            
        except Exception as e:
            print(f"❌ \033[91mErreur de connexion: {e}\033[0m")
            print("💡 \033[93mUtilisation du cache local...\033[0m")
            return {}
    
    def download_package(self, package_name: str, package_info: Dict) -> bool:
        """Télécharge et installe un paquet depuis GitHub"""
        try:
            # URLs des fichiers sur GitHub
            main_url = f"{GITHUB_REPO}/packages/{package_name}/main.init"
            
            print(f"📦 \033[95mInstallation de {package_name} v{package_info.get('version', '1.0.0')}\033[0m")
            
            # Créer le répertoire du paquet
            package_dir = PACKAGES_DIR / package_name
            package_dir.mkdir(exist_ok=True)
            
            # Animation de téléchargement
            for i in range(10):
                self.anim.download_animation(package_name, f"Téléchargement... {i*10}%")
                time.sleep(0.1)
            
            # Télécharger le fichier principal
            try:
                with urllib.request.urlopen(main_url) as response:
                    package_content = response.read().decode()
                
                with open(package_dir / "main.init", 'w') as f:
                    f.write(package_content)
            except Exception as e:
                print(f"\r❌ \033[91mErreur téléchargement: {e}\033[0m")
                return False
            
            # Créer les métadonnées
            with open(package_dir / "package.json", 'w') as f:
                json.dump({
                    "name": package_name,
                    "version": package_info.get("version", "1.0.0"),
                    "description": package_info.get("description", ""),
                    "author": package_info.get("author", "gopu-inc")
                }, f, indent=2)
            
            # Mettre à jour la configuration
            self.config["installed_packages"][package_name] = {
                "version": package_info.get("version", "1.0.0"),
                "path": str(package_dir),
                "source": "github"
            }
            
            self.save_config()
            print(f"\r✅ \033[92m{package_name} installé avec succès!\033[0m")
            return True
            
        except Exception as e:
            print(f"\r❌ \033[91mÉchec installation: {e}\033[0m")
            return False
    
    def install(self, package_names: List[str]):
        """Installe un ou plusieurs paquets depuis GitHub"""
        self.anim.show_banner()
        
        index = self.fetch_package_index()
        
        if not index:
            print("❌ \033[91mImpossible de se connecter au repository\033[0m")
            print("💡 \033[93mVérifiez votre connexion internet\033[0m")
            return
        
        for i, package_name in enumerate(package_names):
            print(f"\n📊 \033[96mPaquet {i+1}/{len(package_names)}\033[0m")
            self._install_single(package_name, index)
    
    def _install_single(self, package_name: str, index: Dict):
        """Installe un paquet unique"""
        if package_name in self.config["installed_packages"]:
            print(f"ℹ️  \033[93m{package_name} est déjà installé\033[0m")
            return
        
        if package_name not in index:
            print(f"❌ \033[91m{package_name} non trouvé dans le repository\033[0m")
            print("📋 \033[94mPaquets disponibles:\033[0m", ", ".join(index.keys()))
            return
        
        package_info = index[package_name]
        
        if self.download_package(package_name, package_info):
            # Installer les dépendances
            dependencies = package_info.get("dependencies", [])
            if dependencies:
                print(f"🔗 \033[95mInstallation des dépendances: {', '.join(dependencies)}\033[0m")
                for dep in dependencies:
                    if dep not in self.config["installed_packages"]:
                        self._install_single(dep, index)
        else:
            print(f"❌ \033[91mÉchec de l'installation de {package_name}\033[0m")
    
    def create_package(self, package_name: str, version: str = "1.0.0"):
        """Crée un nouveau paquet local"""
        self.anim.show_banner()
        
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
        
        print(f"✅ \033[92mPaquet '{package_name}' créé dans {package_dir}\033[0m")
    
    def install_local(self, package_path: str):
        """Installe un paquet local"""
        self.anim.show_banner()
        
        source_dir = Path(package_path)
        package_name = source_dir.name
        
        if not (source_dir / "main.init").exists():
            print(f"❌ \033[91mAucun main.init trouvé dans {package_path}\033[0m")
            return
        
        print(f"📦 \033[95mInstallation locale de {package_name}\033[0m")
        
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
        
        print(f"✅ \033[92mPaquet '{package_name}' installé localement\033[0m")
    
    def list_installed(self):
        """Liste les paquets installés"""
        self.anim.show_banner()
        
        if not self.config["installed_packages"]:
            print("📭 \033[93mAucun paquet installé\033[0m")
            return
        
        print("📦 \033[96mPaquets installés:\033[0m")
        for name, info in self.config["installed_packages"].items():
            source = info.get("source", "inconnu")
            print(f"  ✅ {name} v{info['version']} (\033[94m{source}\033[0m)")
    
    def list_available(self):
        """Liste les paquets disponibles sur GitHub"""
        self.anim.show_banner()
        
        index = self.fetch_package_index()
        
        if not index:
            print("❌ \033[91mImpossible de récupérer les paquets disponibles\033[0m")
            return
        
        print("📚 \033[96mPaquets disponibles:\033[0m")
        for name, info in index.items():
            installed = "✅" if name in self.config["installed_packages"] else "  "
            print(f"  {installed} {name} v{info['version']} - {info.get('description', '')}")
    
    def search(self, query: str):
        """Recherche des paquets"""
        self.anim.show_banner()
        
        index = self.fetch_package_index()
        
        results = []
        for name, info in index.items():
            search_text = f"{name} {info.get('description', '')} {' '.join(info.get('keywords', []))}".lower()
            if query.lower() in search_text:
                results.append((name, info))
        
        if not results:
            print(f"🔍 \033[93mAucun paquet trouvé pour '{query}'\033[0m")
            return
        
        print(f"🔍 \033[96mRésultats pour '{query}':\033[0m")
        for name, info in results:
            installed = "✅" if name in self.config["installed_packages"] else "  "
            print(f"  {installed} {name} v{info['version']} - {info.get('description', '')}")
    
    def uninstall(self, package_name: str):
        """Désinstalle un paquet"""
        self.anim.show_banner()
        
        if package_name not in self.config["installed_packages"]:
            print(f"ℹ️  \033[93m{package_name} n'est pas installé\033[0m")
            return
        
        print(f"🗑️  \033[95mDésinstallation de {package_name}...\033[0m")
        
        package_dir = PACKAGES_DIR / package_name
        if package_dir.exists():
            shutil.rmtree(package_dir)
        
        del self.config["installed_packages"][package_name]
        self.save_config()
        
        print(f"✅ \033[92m{package_name} désinstallé avec succès\033[0m")
    
    def info(self, package_name: str):
        """Affiche les informations d'un paquet"""
        self.anim.show_banner()
        
        index = self.fetch_package_index()
        
        if package_name in index:
            info = index[package_name]
            print(f"📦 \033[96mPaquet: {package_name}\033[0m")
            print(f"📋 Version: {info['version']}")
            print(f"📝 Description: {info.get('description', 'Aucune description')}")
            print(f"👤 Auteur: {info.get('author', 'Inconnu')}")
            print(f"📄 Licence: {info.get('license', 'Inconnue')}")
            
            if 'repository' in info:
                print(f"🔗 Repository: {info['repository']}")
            
            if 'dependencies' in info and info['dependencies']:
                print(f"📦 Dépendances: {', '.join(info['dependencies'])}")
            
            if package_name in self.config["installed_packages"]:
                print("✅ Statut: Installé")
            else:
                print("📥 Statut: Non installé")
        else:
            print(f"❌ \033[91mPaquet '{package_name}' non trouvé\033[0m")
    
    def update_index(self):
        """Met à jour l'index des paquets"""
        self.anim.show_banner()
        
        cache_file = CACHE_DIR / "index.json"
        if cache_file.exists():
            cache_file.unlink()
        
        index = self.fetch_package_index()
        if index:
            print(f"✅ \033[92mIndex mis à jour ({len(index)} paquets disponibles)\033[0m")

def show_help():
    """Affiche l'aide"""
    InitAnimations.show_banner()
    print("""
\033[96mUsage:\033[0m
  initl [COMMANDE] [ARGUMENTS]

\033[96mCommandes:\033[0m
  install <paquet...>    Installe des paquets depuis GitHub
  uninstall <paquet...>  Désinstalle des paquets
  create <nom>           Crée un nouveau paquet local
  install-local <chemin> Installe un paquet local
  list                   Liste les paquets installés
  available              Liste les paquets disponibles sur GitHub
  search <requête>       Recherche des paquets
  info <paquet>          Affiche les informations d'un paquet
  update                 Met à jour l'index des paquets

\033[96mExemples:\033[0m
  initl install math strings
  initl search http
  initl list
  initl available
  initl info math
  initl create monpaquet

\033[93m💡 Astuce: Utilisez 'initl update' pour rafraîchir la liste des paquets\033[0m
    """)

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="INIT Package Manager", add_help=False)
    parser.add_argument('command', nargs='?', help='Commande à exécuter')
    parser.add_argument('args', nargs='*', help='Arguments de la commande')
    
    args = parser.parse_args()
    
    pm = PackageManager()
    
    if not args.command or args.command in ['-h', '--help']:
        show_help()
        return
    
    try:
        if args.command == 'install':
            if not args.args:
                print("❌ \033[91mErreur: Spécifiez les paquets à installer\033[0m")
                return
            pm.install(args.args)
        
        elif args.command == 'uninstall':
            if not args.args:
                print("❌ \033[91mErreur: Spécifiez les paquets à désinstaller\033[0m")
                return
            for package in args.args:
                pm.uninstall(package)
        
        elif args.command == 'create':
            if not args.args:
                print("❌ \033[91mErreur: Spécifiez le nom du paquet\033[0m")
                return
            pm.create_package(args.args[0])
        
        elif args.command == 'install-local':
            if not args.args:
                print("❌ \033[91mErreur: Spécifiez le chemin du paquet\033[0m")
                return
            pm.install_local(args.args[0])
        
        elif args.command == 'list':
            pm.list_installed()
        
        elif args.command == 'available':
            pm.list_available()
        
        elif args.command == 'search':
            if not args.args:
                print("❌ \033[91mErreur: Spécifiez la requête de recherche\033[0m")
                return
            pm.search(args.args[0])
        
        elif args.command == 'info':
            if not args.args:
                print("❌ \033[91mErreur: Spécifiez le nom du paquet\033[0m")
                return
            pm.info(args.args[0])
        
        elif args.command == 'update':
            pm.update_index()
        
        else:
            print(f"❌ \033[91mCommande inconnue: {args.command}\033[0m")
            show_help()
    
    except Exception as e:
        print(f"❌ \033[91mErreur: {e}\033[0m")

if __name__ == "__main__":
    main()
