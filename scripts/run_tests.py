#!/usr/bin/env python3
"""
Test Runner für Crypto Trading Bot v2.0
Führe alle Tests aus und zeige Ergebnisse
"""

import subprocess
import sys
import os


def run_pytest():
    """Führe pytest mit verschiedenen Optionen aus"""
    
    print("🧪 CRYPTO TRADING BOT v2.0 - TEST SUITE")
    print("="*60)
    
    # Wechsle ins Hauptverzeichnis für Tests
    original_dir = os.getcwd()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    # Basis pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Prüfe ob pytest installiert ist
    try:
        result = subprocess.run(["python", "-m", "pytest", "--version"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ pytest ist nicht installiert!")
            print("Installiere mit: pip install pytest pytest-asyncio")
            os.chdir(original_dir)
            return False
    except FileNotFoundError:
        print("❌ Python ist nicht verfügbar!")
        os.chdir(original_dir)
        return False
    
    print("✅ pytest gefunden, starte Tests...\n")
    
    # Führe verschiedene Test-Kategorien aus
    test_configs = [
        {
            "name": "🔧 Unit Tests - Utils",
            "path": "tests/test_utils/",
            "description": "Tests für Decorators und Hilfsfunktionen"
        },
        {
            "name": "📦 Unit Tests - Modules", 
            "path": "tests/test_modules/",
            "description": "Tests für Portfolio Analyzer, Price Monitor, Arbitrage Detector"
        },
        {
            "name": "🔗 Integration Tests",
            "path": "tests/test_integration.py",
            "description": "Tests für Zusammenspiel aller Module"
        }
    ]
    
    all_passed = True
    
    for config in test_configs:
        print(f"\n{config['name']}")
        print("-" * len(config['name']))
        print(f"📋 {config['description']}")
        print()
        
        # Führe spezifische Tests aus
        test_cmd = cmd + [config['path'], "-v"]
        
        result = subprocess.run(test_cmd)
        
        if result.returncode == 0:
            print(f"✅ {config['name']} - ALLE TESTS BESTANDEN!")
        else:
            print(f"❌ {config['name']} - TESTS FEHLGESCHLAGEN!")
            all_passed = False
        
        print()
    
    # Gesamtergebnis
    print("="*60)
    if all_passed:
        print("🎉 ALLE TESTS ERFOLGREICH!")
        print("✅ Crypto Trading Bot ist bereit für Production")
    else:
        print("❌ EINIGE TESTS FEHLGESCHLAGEN!")
        print("🔧 Überprüfe die Fehler und behebe sie")
    print("="*60)
    
    # Wechsle zurück ins ursprüngliche Verzeichnis
    os.chdir(original_dir)
    
    return all_passed


def run_coverage_tests():
    """Führe Tests mit Coverage-Report aus"""
    
    print("\n📊 COVERAGE ANALYSIS")
    print("="*30)
    
    # Prüfe ob coverage installiert ist
    try:
        subprocess.run(["python", "-m", "coverage", "--version"], 
                      capture_output=True, text=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("ℹ️ Coverage nicht installiert - überspringe Coverage-Report")
        print("Installiere mit: pip install coverage")
        return
    
    # Führe Tests mit Coverage aus
    cmd = [
        "python", "-m", "coverage", "run", 
        "-m", "pytest", "tests/", "-v"
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        # Zeige Coverage Report
        print("\n📈 COVERAGE REPORT:")
        subprocess.run(["python", "-m", "coverage", "report"])
        
        # Generiere HTML Report
        subprocess.run(["python", "-m", "coverage", "html"])
        print("\n📄 HTML Coverage Report generiert in htmlcov/")
    else:
        print("❌ Coverage Tests fehlgeschlagen")


def run_performance_tests():
    """Führe Performance-Tests aus"""
    
    print("\n⚡ PERFORMANCE TESTS")
    print("="*25)
    
    # Performance-spezifische Tests
    cmd = [
        "python", "-m", "pytest", 
        "tests/", "-v", 
        "-k", "performance or timing",
        "--durations=0"
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("✅ Performance Tests bestanden!")
    else:
        print("❌ Performance Tests fehlgeschlagen!")


def main():
    """Hauptfunktion"""
    
    # Wechsle ins Projektverzeichnis
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Führe Tests aus
    tests_passed = run_pytest()
    
    # Optional: Coverage und Performance Tests
    if len(sys.argv) > 1:
        if "--coverage" in sys.argv:
            run_coverage_tests()
        
        if "--performance" in sys.argv:
            run_performance_tests()
    
    # Exit code für CI/CD
    sys.exit(0 if tests_passed else 1)


if __name__ == "__main__":
    main()