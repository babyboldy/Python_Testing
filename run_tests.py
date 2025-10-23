#!/usr/bin/env python3
"""
Script de lancement des tests avec différentes configurations
"""
import subprocess
import sys
import os


def run_command(command, description):
    """Exécute une commande et affiche le résultat"""
    print(f"\n{'='*60}")
    print(f"LANCEMENT: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Erreur lors de l'exécution: {e}")
        return False


def main():
    """Fonction principale"""
    print("Lancement des tests pour le projet Python Testing")
    
    # Vérifier que nous sommes dans le bon répertoire
    if not os.path.exists("server.py"):
        print("ERREUR: server.py non trouve. Assurez-vous d'être dans le bon répertoire.")
        sys.exit(1)
    
    # Tests unitaires
    success = run_command(
        "python -m pytest tests/unit/ -v --tb=short",
        "Tests unitaires"
    )
    
    if not success:
        print("ECHEC des tests unitaires")
        return False
    
    # Tests d'intégration
    success = run_command(
        "python -m pytest tests/integration/ -v --tb=short",
        "Tests d'intégration"
    )
    
    if not success:
        print("ECHEC des tests d'integration")
        return False
    
    # Tests fonctionnels
    success = run_command(
        "python -m pytest tests/functional/ -v --tb=short",
        "Tests fonctionnels"
    )
    
    if not success:
        print("ECHEC des tests fonctionnels")
        return False
    
    # Tous les tests avec couverture
    success = run_command(
        "python -m pytest tests/ -v --cov=server --cov-report=html --cov-report=term-missing",
        "Tous les tests avec couverture de code"
    )
    
    if success:
        print("\nSUCCES: Tous les tests sont passes avec succes!")
        print("Rapport de couverture genere dans htmlcov/index.html")
    else:
        print("\nECHEC: Certains tests ont echoue")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)