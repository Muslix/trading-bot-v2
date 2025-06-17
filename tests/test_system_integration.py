#!/usr/bin/env python3
"""
Integrierte Test-Suite für das komplette System
Kombiniert Coin-Coverage und Duplikate-Vermeidung Tests
"""

import os
import subprocess
import sys
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))


class IntegratedTestSuite:
    """Integrierte Test-Suite für das gesamte System"""

    def __init__(self):
        self.results = {
            "start_time": datetime.now(),
            "tests_run": [],
            "total_passed": 0,
            "total_failed": 0,
            "system_healthy": False,
        }

    def run_test_script(self, script_path, test_name):
        """Führe ein Test-Script aus"""
        print(f"🚀 Starte {test_name}...")
        print("=" * 60)

        try:
            # Führe das Test-Script aus
            result = subprocess.run(
                [sys.executable, script_path], capture_output=False, text=True, timeout=300
            )  # 5 Minuten Timeout

            success = result.returncode == 0

            self.results["tests_run"].append(
                {
                    "name": test_name,
                    "script": script_path,
                    "success": success,
                    "return_code": result.returncode,
                }
            )

            if success:
                self.results["total_passed"] += 1
                print(f"✅ {test_name} BESTANDEN")
            else:
                self.results["total_failed"] += 1
                print(f"❌ {test_name} FEHLGESCHLAGEN (Exit Code: {result.returncode})")

            print()  # Leerzeile
            return success

        except subprocess.TimeoutExpired:
            print(f"⏰ {test_name} TIMEOUT (>5 Minuten)")
            self.results["total_failed"] += 1
            self.results["tests_run"].append(
                {
                    "name": test_name,
                    "script": script_path,
                    "success": False,
                    "return_code": -1,
                    "error": "Timeout",
                }
            )
            return False

        except Exception as e:
            print(f"💥 {test_name} CRASHED: {e}")
            self.results["total_failed"] += 1
            self.results["tests_run"].append(
                {
                    "name": test_name,
                    "script": script_path,
                    "success": False,
                    "return_code": -999,
                    "error": str(e),
                }
            )
            return False

    def check_system_prerequisites(self):
        """Überprüfe System-Voraussetzungen"""
        print("🔍 SYSTEM PREREQUISITES CHECK")
        print("=" * 60)

        checks = []

        # 1. Database verfügbar
        try:
            from src.modules.database import db

            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM performance_data")
                count = cursor.fetchone()[0]
                checks.append(("Database erreichbar", True, f"{count} Performance-Datensätze"))
        except Exception as e:
            checks.append(("Database erreichbar", False, str(e)))

        # 2. Web API erreichbar (optional)
        try:
            import requests

            response = requests.get("http://localhost:5000/api/performance-data", timeout=5)
            api_working = response.status_code == 200
            api_info = f"HTTP {response.status_code}" if not api_working else "API OK"
            checks.append(("Web API erreichbar", api_working, api_info))
        except Exception as e:
            checks.append(("Web API erreichbar", False, f"Nicht erreichbar: {e}"))

        # 3. Konfiguration geladen
        try:
            from config.config import get_config

            config = get_config()
            crypto_count = config.analysis_crypto_count
            checks.append(("Konfiguration geladen", True, f"Analysis Count: {crypto_count}"))
        except Exception as e:
            checks.append(("Konfiguration geladen", False, str(e)))

        # Ergebnisse anzeigen
        all_critical_passed = True
        for check_name, passed, info in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}: {info}")

            # API ist optional, aber Database und Config sind kritisch
            if not passed and check_name in ["Database erreichbar", "Konfiguration geladen"]:
                all_critical_passed = False

        print()
        return all_critical_passed

    def run_all_tests(self):
        """Führe alle Tests aus"""
        print("🚀 INTEGRIERTE SYSTEM TEST SUITE")
        print("=" * 60)
        print(f"Start Zeit: {self.results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Voraussetzungen prüfen
        if not self.check_system_prerequisites():
            print("❌ System-Voraussetzungen nicht erfüllt!")
            return False

        # Test-Scripts definieren
        test_scripts = [
            ("tests/test_coin_coverage.py", "Coin Coverage Test"),
            ("tests/test_duplicate_prevention.py", "Duplicate Prevention Test"),
        ]

        # Alle Tests ausführen
        all_passed = True
        for script_path, test_name in test_scripts:
            if os.path.exists(script_path):
                success = self.run_test_script(script_path, test_name)
                if not success:
                    all_passed = False
            else:
                print(f"⚠️ Test-Script nicht gefunden: {script_path}")
                all_passed = False

        # System-Gesundheit bewerten
        self.results["system_healthy"] = all_passed and self.results["total_failed"] == 0

        self.print_final_summary()
        return self.results["system_healthy"]

    def print_final_summary(self):
        """Drucke finale Zusammenfassung"""
        end_time = datetime.now()
        duration = end_time - self.results["start_time"]

        print("📊 FINAL TEST SUMMARY")
        print("=" * 60)
        print(f"⏱️ Gesamtdauer: {duration.total_seconds():.1f} Sekunden")
        print(f"✅ Tests bestanden: {self.results['total_passed']}")
        print(f"❌ Tests fehlgeschlagen: {self.results['total_failed']}")
        print(f"📊 Gesamt Tests: {len(self.results['tests_run'])}")

        print(
            f"\n🏥 System Status: {'✅ GESUND' if self.results['system_healthy'] else '❌ PROBLEME'}"
        )

        if self.results["tests_run"]:
            print("\n📋 Test Details:")
            for test in self.results["tests_run"]:
                status = "✅" if test["success"] else "❌"
                error_info = (
                    f" ({test.get('error', 'Exit ' + str(test['return_code']))})"
                    if not test["success"]
                    else ""
                )
                print(f"   {status} {test['name']}{error_info}")

        # Empfehlungen
        print(f"\n💡 EMPFEHLUNGEN:")
        if self.results["system_healthy"]:
            print("   • System läuft optimal! 🚀")
            print("   • Alle Coin-Coverage und Duplikate-Tests bestanden")
            print("   • Regelmäßige Tests empfohlen (täglich/wöchentlich)")
        else:
            print("   • Tests fehlgeschlagen - System überprüfen")
            if self.results["total_failed"] > 0:
                print("   • Fehlerhafte Tests einzeln ausführen für Details")
            print("   • Monitor-System neu starten kann helfen")
            print("   • Database-Integrität überprüfen")


def main():
    """Hauptfunktion"""
    suite = IntegratedTestSuite()
    success = suite.run_all_tests()

    # Exit code für CI/CD
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
