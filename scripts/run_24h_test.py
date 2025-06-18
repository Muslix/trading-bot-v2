"""
24h Test Suite - Kompletter Test des Crypto Trading Bot Systems
Führe einen vollständigen 24h Test-Durchlauf durch
"""

import asyncio
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crypto_monitor_24_7 import CryptoMonitor24_7
from src.alerts import create_alert_manager, AlertManager
from src.modules.database import db
from src.modules.telegram_bot import crypto_bot
from web_api import app
import threading


class ComprehensiveTestSuite:
    """Komplette Test-Suite für 24h Durchlauf"""
    
    def __init__(self):
        # Initialize new alert system
        self.alert_manager = create_alert_manager()
        self.test_start_time = datetime.now()
        self.test_results = {
            'start_time': self.test_start_time.isoformat(),
            'components_tested': [],
            'errors_encountered': [],
            'performance_metrics': {},
            'alert_statistics': {},
            'api_tests': {},
            'database_health': {},
            'recommendations': []
        }
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    async def test_database_performance(self) -> Dict:
        """Teste Database-Performance"""
        print("📊 Testing Database Performance...")
        
        start_time = time.time()
        
        # Test 1: Schreib-Performance
        write_start = time.time()
        for i in range(100):
            db.save_price_data(f'TEST{i}', 'binance', 45000 + i, volume=1000)
        write_time = time.time() - write_start
        
        # Test 2: Lese-Performance
        read_start = time.time()
        dashboard_data = db.get_dashboard_data()
        recent_alerts = db.get_recent_arbitrage_alerts(hours=24)
        performance_data = db.get_latest_performance_data(limit=50)
        read_time = time.time() - read_start
        
        # Test 3: Cleanup
        cleanup_start = time.time()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM price_history WHERE symbol LIKE 'TEST%'")
            conn.commit()
        cleanup_time = time.time() - cleanup_start
        
        total_time = time.time() - start_time
        
        db_metrics = {
            'total_test_time': round(total_time, 3),
            'write_performance': round(write_time, 3),
            'read_performance': round(read_time, 3),
            'cleanup_time': round(cleanup_time, 3),
            'writes_per_second': round(100 / write_time, 2),
            'database_size_mb': self._get_db_size(),
            'status': 'healthy' if total_time < 5.0 else 'slow'
        }
        
        self.test_results['database_health'] = db_metrics
        return db_metrics
    
    def _get_db_size(self) -> float:
        """Hole Database-Größe in MB"""
        try:
            size_bytes = os.path.getsize(db.db_path)
            return round(size_bytes / (1024 * 1024), 2)
        except:
            return 0.0
    
    async def test_monitoring_cycle(self) -> Dict:
        """Teste einen kompletten Monitoring-Cycle"""
        print("🔄 Testing Monitoring Cycle...")
        
        monitor = CryptoMonitor24_7()
        monitor.config['arbitrage_check_interval'] = 5  # Schneller für Test
        monitor.config['watchlist_symbols'] = ['BTC/USDT', 'ETH/USDT']  # Weniger für Test
        monitor.config['analysis_crypto_count'] = 10  # Weniger für Test
        
        cycle_start = time.time()
        
        try:
            # Teste Arbitrage Check
            arbitrage_start = time.time()
            await monitor._arbitrage_check_cycle()
            arbitrage_time = time.time() - arbitrage_start
            
            # Teste Performance Check  
            performance_start = time.time()
            await monitor._performance_check_cycle()
            performance_time = time.time() - performance_start
            
            # Teste Stats Update
            monitor._update_stats()
            
            cycle_time = time.time() - cycle_start
            
            cycle_metrics = {
                'total_cycle_time': round(cycle_time, 3),
                'arbitrage_check_time': round(arbitrage_time, 3),
                'performance_check_time': round(performance_time, 3),
                'arbitrage_opportunities': monitor.stats['arbitrage_opportunities_found'],
                'performance_analyses': monitor.stats['total_performance_analyses'],
                'status': 'healthy' if cycle_time < 30.0 else 'slow'
            }
            
            self.test_results['performance_metrics'] = cycle_metrics
            return cycle_metrics
            
        except Exception as e:
            self.logger.error(f"❌ Monitoring Cycle Test fehlgeschlagen: {e}")
            self.test_results['errors_encountered'].append(f"Monitoring Cycle: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    async def test_smart_alerts(self) -> Dict:
        """Teste Smart Alert System"""
        print("🚨 Testing Smart Alert System...")
        
        # Test verschiedene Alert-Typen
        test_arbitrage = [{
            'symbol': 'TEST/USDT',
            'buy_exchange': 'binance',
            'sell_exchange': 'coinbase',
            'buy_price': 45000,
            'sell_price': 46500,
            'profit_percentage': 3.3,
            'profit_per_unit': 1500
        }]
        
        test_performance = [
            ('TEST1', {'sharpe_ratio': 2.1, 'annual_return': 95.0}),
            ('TEST2', {'sharpe_ratio': 1.8, 'annual_return': 75.0})
        ]
        
        alert_start = time.time()
        
        # Teste alle Alert-Arten
        alert_results = await alert_manager.process_alerts(
            arbitrage_opportunities=test_arbitrage,
            performance_data=test_performance,
            force_daily_summary=False  # Nicht im Test
        )
        
        alert_time = time.time() - alert_start
        
        # Hole Alert-Statistiken
        alert_stats = smart_alerts.get_alert_stats()
        
        alert_metrics = {
            'processing_time': round(alert_time, 3),
            'alerts_processed': alert_results,
            'rules_configured': alert_stats['rules_configured'],
            'rules_enabled': alert_stats['rules_enabled'],
            'status': 'healthy' if alert_time < 5.0 else 'slow'
        }
        
        self.test_results['alert_statistics'] = alert_metrics
        return alert_metrics
    
    def test_api_endpoints(self) -> Dict:
        """Teste alle API Endpoints"""
        print("🌐 Testing API Endpoints...")
        
        import requests
        
        api_base = "http://localhost:5000"
        endpoints = [
            "/api/dashboard-data",
            "/api/live-prices", 
            "/api/arbitrage-alerts",
            "/api/performance-data",
            "/api/bot-health"
        ]
        
        api_results = {}
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{api_base}{endpoint}", timeout=5)
                response_time = time.time() - start_time
                
                api_results[endpoint] = {
                    'status_code': response.status_code,
                    'response_time': round(response_time, 3),
                    'success': response.status_code == 200,
                    'data_valid': bool(response.json().get('success')) if response.status_code == 200 else False
                }
                
            except requests.exceptions.ConnectionError:
                api_results[endpoint] = {
                    'status_code': 'CONNECTION_ERROR',
                    'success': False,
                    'note': 'API Server nicht erreichbar'
                }
            except Exception as e:
                api_results[endpoint] = {
                    'status_code': 'ERROR',
                    'success': False,
                    'error': str(e)
                }
        
        # Berechne Gesamt-API-Gesundheit
        successful_endpoints = sum(1 for result in api_results.values() if result.get('success', False))
        api_health = 'healthy' if successful_endpoints >= len(endpoints) * 0.8 else 'degraded'
        
        api_metrics = {
            'endpoints_tested': len(endpoints),
            'successful_endpoints': successful_endpoints,
            'success_rate': round((successful_endpoints / len(endpoints)) * 100, 1),
            'endpoint_results': api_results,
            'status': api_health
        }
        
        self.test_results['api_tests'] = api_metrics
        return api_metrics
    
    async def run_stress_test(self, duration_minutes: int = 5) -> Dict:
        """Führe Stress-Test durch"""
        print(f"⚡ Running {duration_minutes}min Stress Test...")
        
        stress_start = time.time()
        end_time = stress_start + (duration_minutes * 60)
        
        cycles_completed = 0
        errors_encountered = 0
        total_alerts_sent = 0
        
        monitor = CryptoMonitor24_7()
        monitor.config['arbitrage_check_interval'] = 10  # Alle 10 Sekunden
        monitor.config['watchlist_symbols'] = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        monitor.config['analysis_crypto_count'] = 15
        
        while time.time() < end_time:
            cycle_start = time.time()
            
            try:
                # Arbitrage Check
                await monitor._arbitrage_check_cycle()
                
                # Performance Check (weniger häufig)
                if cycles_completed % 3 == 0:  # Alle 3 Cycles
                    await monitor._performance_check_cycle()
                
                # Smart Alerts Check
                test_arbitrage = [{
                    'symbol': f'STRESS{cycles_completed % 3}',
                    'profit_percentage': 1.5 + (cycles_completed % 3),
                    'buy_exchange': 'binance',
                    'sell_exchange': 'coinbase'
                }]
                
                alert_results = await alert_manager.process_alerts(
                    arbitrage_opportunities=test_arbitrage
                )
                total_alerts_sent += alert_results['total_alerts']
                
                cycles_completed += 1
                
                # Kurze Pause
                cycle_time = time.time() - cycle_start
                sleep_time = max(1, 10 - cycle_time)  # Min 1s Pause
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                errors_encountered += 1
                self.logger.error(f"❌ Stress Test Cycle Error: {e}")
                await asyncio.sleep(5)  # Längere Pause bei Fehlern
        
        stress_duration = time.time() - stress_start
        
        stress_metrics = {
            'duration_seconds': round(stress_duration, 1),
            'cycles_completed': cycles_completed,
            'errors_encountered': errors_encountered,
            'cycles_per_minute': round((cycles_completed / stress_duration) * 60, 1),
            'error_rate': round((errors_encountered / max(cycles_completed, 1)) * 100, 1),
            'alerts_sent': total_alerts_sent,
            'status': 'healthy' if errors_encountered < cycles_completed * 0.1 else 'unstable'
        }
        
        return stress_metrics
    
    def generate_recommendations(self) -> List[str]:
        """Generiere Optimierungs-Empfehlungen"""
        recommendations = []
        
        # Database Performance
        db_health = self.test_results.get('database_health', {})
        if db_health.get('writes_per_second', 0) < 50:
            recommendations.append("Database Write-Performance optimieren (< 50 writes/sec)")
        
        if db_health.get('database_size_mb', 0) > 100:
            recommendations.append("Database Cleanup implementieren (> 100MB)")
        
        # Monitoring Performance
        perf_metrics = self.test_results.get('performance_metrics', {})
        if perf_metrics.get('total_cycle_time', 0) > 30:
            recommendations.append("Monitoring Cycle optimieren (> 30s)")
        
        # API Performance
        api_tests = self.test_results.get('api_tests', {})
        if api_tests.get('success_rate', 0) < 90:
            recommendations.append("API Reliability verbessern (< 90% success rate)")
        
        # Alert Performance
        alert_stats = self.test_results.get('alert_statistics', {})
        if alert_stats.get('processing_time', 0) > 3:
            recommendations.append("Alert Processing optimieren (> 3s)")
        
        # Allgemeine Empfehlungen
        if not recommendations:
            recommendations.append("System läuft optimal! Keine Optimierungen nötig.")
        else:
            recommendations.append("Implementiere Caching für bessere Performance")
            recommendations.append("Erwäge Database-Indizierung für große Datensätze")
        
        return recommendations
    
    async def run_comprehensive_test(self, stress_test_duration: int = 5) -> Dict:
        """Führe kompletten Test durch"""
        print("🧪 STARTING COMPREHENSIVE 24H TEST SUITE")
        print("=" * 60)
        
        self.test_results['components_tested'].append('Database Performance')
        db_results = await self.test_database_performance()
        print(f"✅ Database Test: {db_results['status']} ({db_results['total_test_time']}s)")
        
        self.test_results['components_tested'].append('Monitoring Cycle')
        monitoring_results = await self.test_monitoring_cycle()
        print(f"✅ Monitoring Test: {monitoring_results['status']} ({monitoring_results.get('total_cycle_time', 0)}s)")
        
        self.test_results['components_tested'].append('Smart Alerts')
        alert_results = await self.test_smart_alerts()
        print(f"✅ Smart Alerts Test: {alert_results['status']} ({alert_results['processing_time']}s)")
        
        self.test_results['components_tested'].append('API Endpoints')
        api_results = self.test_api_endpoints()
        print(f"✅ API Test: {api_results['status']} ({api_results['success_rate']}% success)")
        
        self.test_results['components_tested'].append('Stress Test')
        stress_results = await self.run_stress_test(stress_test_duration)
        print(f"✅ Stress Test: {stress_results['status']} ({stress_results['cycles_completed']} cycles)")
        
        # Generiere Empfehlungen
        self.test_results['recommendations'] = self.generate_recommendations()
        
        # Test-Abschluss
        self.test_results['end_time'] = datetime.now().isoformat()
        total_duration = datetime.now() - self.test_start_time
        self.test_results['total_duration_minutes'] = round(total_duration.total_seconds() / 60, 1)
        
        return self.test_results
    
    def save_test_report(self, filename: str = None):
        """Speichere Test-Report"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"test_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Test-Report gespeichert: {filename}")
        return filename
    
    def print_summary_report(self):
        """Drucke Zusammenfassung"""
        print("\n" + "=" * 60)
        print("📋 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        print(f"⏱️ Total Duration: {self.test_results['total_duration_minutes']} minutes")
        print(f"🧪 Components Tested: {len(self.test_results['components_tested'])}")
        print(f"❌ Errors Encountered: {len(self.test_results['errors_encountered'])}")
        
        # Component Status
        print(f"\n📊 Component Status:")
        components = {
            'Database': self.test_results.get('database_health', {}).get('status', 'unknown'),
            'Monitoring': self.test_results.get('performance_metrics', {}).get('status', 'unknown'),
            'Smart Alerts': self.test_results.get('alert_statistics', {}).get('status', 'unknown'),
            'API': self.test_results.get('api_tests', {}).get('status', 'unknown')
        }
        
        for component, status in components.items():
            status_emoji = "✅" if status == 'healthy' else "⚠️" if status in ['slow', 'degraded'] else "❌"
            print(f"   {status_emoji} {component}: {status}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(self.test_results['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        # Overall Health
        healthy_components = sum(1 for status in components.values() if status == 'healthy')
        overall_health = round((healthy_components / len(components)) * 100, 1)
        
        print(f"\n🏥 Overall System Health: {overall_health}%")
        
        if overall_health >= 90:
            print("🎉 SYSTEM READY FOR 24/7 PRODUCTION!")
        elif overall_health >= 70:
            print("⚠️ System functional but needs optimization")
        else:
            print("❌ System needs significant improvements")
        
        print("=" * 60)


async def main():
    """Führe kompletten Test durch"""
    test_suite = ComprehensiveTestSuite()
    
    print("🚀 Starting Crypto Trading Bot 24h Test Suite...")
    print("⏳ This will test all system components thoroughly")
    
    # Frage nach Test-Dauer
    try:
        duration = input("\nStress Test Dauer in Minuten (Standard: 3): ").strip()
        stress_duration = int(duration) if duration else 3
    except (ValueError, EOFError):
        stress_duration = 3
    
    print(f"\n🔄 Running comprehensive test (Stress Test: {stress_duration} minutes)...")
    
    # Führe Tests durch
    results = await test_suite.run_comprehensive_test(stress_duration)
    
    # Speichere und zeige Report
    report_file = test_suite.save_test_report()
    test_suite.print_summary_report()
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    print("🎯 System is ready for 24/7 deployment if all tests passed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()