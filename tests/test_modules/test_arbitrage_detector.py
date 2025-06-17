"""
Tests für modules/arbitrage_detector.py
Teste Arbitrage-Erkennung und Alert-System
"""

import pytest

from src.modules.arbitrage_detector import (
    alert_system,
    analyze_arbitrage_history,
    calculate_profit_potential,
    detect_arbitrage_opportunities,
    filter_opportunities_by_criteria,
    get_best_arbitrage_opportunity,
)


class TestDetectArbitrageOpportunities:
    """Tests für detect_arbitrage_opportunities Funktion"""

    def test_no_arbitrage_opportunity(self):
        """Test wenn keine Arbitrage-Möglichkeit existiert"""
        prices = {
            "binance": 45000.0,
            "coinbase": 45050.0,  # Nur 0.11% Unterschied
            "kraken": 45025.0,
        }

        opportunities = detect_arbitrage_opportunities(prices, threshold=0.01)

        assert opportunities == []

    def test_single_arbitrage_opportunity(self):
        """Test einzelne Arbitrage-Möglichkeit"""
        prices = {"binance": 45000.0, "coinbase": 45600.0, "kraken": 45100.0}  # 1.33% höher

        opportunities = detect_arbitrage_opportunities(prices, threshold=0.01)

        assert len(opportunities) > 0

        # Finde die beste Möglichkeit
        best_opp = max(opportunities, key=lambda x: x["profit_percent"])

        assert best_opp["buy_exchange"] == "binance"
        assert best_opp["sell_exchange"] == "coinbase"
        assert best_opp["buy_price"] == 45000.0
        assert best_opp["sell_price"] == 45600.0
        assert best_opp["profit_percent"] == 1.33
        assert best_opp["profit_per_unit"] == 600.0

    def test_multiple_arbitrage_opportunities(self):
        """Test mehrere Arbitrage-Möglichkeiten"""
        prices = {
            "binance": 45000.0,
            "coinbase": 46000.0,  # Sehr hoch
            "kraken": 44500.0,  # Sehr niedrig
            "kucoin": 45800.0,  # Auch hoch
        }

        opportunities = detect_arbitrage_opportunities(prices, threshold=0.01)

        # Sollte mehrere Möglichkeiten finden
        assert len(opportunities) > 1

        # Alle sollten profitable sein
        for opp in opportunities:
            assert opp["profit_percent"] > 1.0
            assert opp["profit_per_unit"] > 0

    def test_custom_threshold(self):
        """Test benutzerdefinierte Schwelle"""
        prices = {
            "binance": 45000.0,
            "coinbase": 45200.0,  # 0.44% Unterschied
        }

        # Mit 1% Schwelle: keine Möglichkeit
        opportunities_1pct = detect_arbitrage_opportunities(prices, threshold=0.01)
        assert len(opportunities_1pct) == 0

        # Mit 0.3% Schwelle: eine Möglichkeit
        opportunities_03pct = detect_arbitrage_opportunities(prices, threshold=0.003)
        assert len(opportunities_03pct) == 1

    def test_zero_prices_ignored(self):
        """Test dass Null-Preise ignoriert werden"""
        prices = {"binance": 45000.0, "coinbase": 0.0, "kraken": 45600.0}  # Kaputte API

        opportunities = detect_arbitrage_opportunities(prices, threshold=0.01)

        # Sollte coinbase ignorieren
        for opp in opportunities:
            assert "coinbase" not in [opp["buy_exchange"], opp["sell_exchange"]]

    def test_identical_prices(self):
        """Test identische Preise auf allen Börsen"""
        prices = {"binance": 45000.0, "coinbase": 45000.0, "kraken": 45000.0}

        opportunities = detect_arbitrage_opportunities(prices, threshold=0.01)

        assert opportunities == []


class TestAlertSystem:
    """Tests für alert_system Funktion"""

    def test_alert_for_profitable_opportunity(self, capsys):
        """Test Alert für profitable Möglichkeit"""
        opportunities = [
            {
                "buy_exchange": "binance",
                "sell_exchange": "coinbase",
                "buy_price": 45000.0,
                "sell_price": 45600.0,
                "profit_percent": 1.33,
                "profit_per_unit": 600.0,
            }
        ]

        alerts = alert_system(opportunities, min_profit=1.0)
        captured = capsys.readouterr()

        assert len(alerts) == 1
        assert "ARBITRAGE ALERT" in captured.out
        assert "1.33%" in captured.out
        assert "BINANCE" in captured.out
        assert "COINBASE" in captured.out
        assert "$600.00" in captured.out

    def test_no_alert_for_low_profit(self, capsys):
        """Test kein Alert für niedrigen Profit"""
        opportunities = [
            {
                "buy_exchange": "binance",
                "sell_exchange": "coinbase",
                "buy_price": 45000.0,
                "sell_price": 45200.0,
                "profit_percent": 0.44,  # Unter 1%
                "profit_per_unit": 200.0,
            }
        ]

        alerts = alert_system(opportunities, min_profit=1.0)
        captured = capsys.readouterr()

        assert len(alerts) == 0
        assert "ARBITRAGE ALERT" not in captured.out

    def test_custom_profit_threshold(self, capsys):
        """Test benutzerdefinierte Profit-Schwelle"""
        opportunities = [
            {
                "buy_exchange": "binance",
                "sell_exchange": "coinbase",
                "buy_price": 45000.0,
                "sell_price": 45200.0,
                "profit_percent": 0.44,
                "profit_per_unit": 200.0,
            }
        ]

        alerts = alert_system(opportunities, min_profit=0.3)

        assert len(alerts) == 1


class TestCalculateProfitPotential:
    """Tests für calculate_profit_potential Funktion"""

    def test_profit_calculation_basic(self):
        """Test grundlegende Profit-Berechnung"""
        opportunity = {"buy_price": 45000.0, "sell_price": 45600.0, "profit_per_unit": 600.0}

        profit = calculate_profit_potential(opportunity, volume=1.0)

        assert profit["volume"] == 1.0
        assert profit["gross_profit"] == 600.0
        assert profit["trading_fees"] > 0  # Sollte Fees berücksichtigen
        assert profit["net_profit"] < profit["gross_profit"]  # Nach Fees
        assert profit["net_profit_percent"] > 0

    def test_profit_calculation_large_volume(self):
        """Test Profit-Berechnung für großes Volumen"""
        opportunity = {"buy_price": 45000.0, "sell_price": 45600.0, "profit_per_unit": 600.0}

        profit = calculate_profit_potential(opportunity, volume=10.0)

        assert profit["volume"] == 10.0
        assert profit["gross_profit"] == 6000.0  # 10 * 600
        assert profit["net_profit"] < 6000.0  # Nach Fees

    def test_trading_fees_calculation(self):
        """Test dass Trading-Fees korrekt berechnet werden"""
        opportunity = {"buy_price": 100.0, "sell_price": 102.0, "profit_per_unit": 2.0}

        profit = calculate_profit_potential(opportunity, volume=1.0)

        # Bei 0.1% Fee Rate: 0.1 + 0.102 = 0.202 total fees
        expected_fees = (100.0 * 0.001) + (102.0 * 0.001)
        assert abs(profit["trading_fees"] - round(expected_fees, 2)) < 0.01


class TestArbitrageHistory:
    """Tests für analyze_arbitrage_history Funktion"""

    def test_empty_history(self):
        """Test leere Historie"""
        history = analyze_arbitrage_history([])

        assert history["total_opportunities"] == 0
        assert history["avg_profit_percent"] == 0
        assert history["max_profit_percent"] == 0
        assert history["profitable_periods"] == 0
        assert history["total_periods"] == 0

    def test_history_with_opportunities(self):
        """Test Historie mit Möglichkeiten"""
        opportunities_history = [
            [{"profit_percent": 1.5}, {"profit_percent": 2.0}],  # 2 Möglichkeiten
            [],  # Keine Möglichkeiten
            [{"profit_percent": 1.0}],  # 1 Möglichkeit
        ]

        history = analyze_arbitrage_history(opportunities_history)

        assert history["total_opportunities"] == 3
        assert history["avg_profit_percent"] == 1.5  # (1.5+2.0+1.0)/3
        assert history["max_profit_percent"] == 2.0
        assert history["profitable_periods"] == 2  # Periode 0 und 2
        assert history["total_periods"] == 3

    def test_history_no_opportunities(self):
        """Test Historie ohne Möglichkeiten"""
        opportunities_history = [[], [], []]

        history = analyze_arbitrage_history(opportunities_history)

        assert history["total_opportunities"] == 0
        assert history["profitable_periods"] == 0
        assert history["total_periods"] == 3


class TestFilterOpportunities:
    """Tests für filter_opportunities_by_criteria Funktion"""

    def test_filter_by_min_profit(self):
        """Test Filter nach Mindest-Profit"""
        opportunities = [
            {"profit_percent": 2.0, "buy_price": 45000},
            {"profit_percent": 0.5, "buy_price": 45000},
            {"profit_percent": 1.5, "buy_price": 45000},
        ]

        filtered = filter_opportunities_by_criteria(opportunities, min_profit=1.0)

        assert len(filtered) == 2
        profits = [opp["profit_percent"] for opp in filtered]
        assert 2.0 in profits
        assert 1.5 in profits
        assert 0.5 not in profits

    def test_filter_by_volume_support(self):
        """Test Filter nach Volumen-Unterstützung"""
        opportunities = [
            {"profit_percent": 2.0, "buy_price": 50000},  # 5M volume support
            {"profit_percent": 2.0, "buy_price": 5},  # 500 volume support
        ]

        filtered = filter_opportunities_by_criteria(
            opportunities, min_profit=1.0, min_volume_support=1000
        )

        assert len(filtered) == 1
        assert filtered[0]["buy_price"] == 50000  # Nur high-price überlebt

    def test_filter_empty_list(self):
        """Test Filter auf leere Liste"""
        filtered = filter_opportunities_by_criteria([], min_profit=1.0)
        assert filtered == []


class TestGetBestOpportunity:
    """Tests für get_best_arbitrage_opportunity Funktion"""

    def test_best_opportunity_selection(self):
        """Test Auswahl der besten Möglichkeit"""
        opportunities = [
            {"profit_percent": 1.5, "buy_exchange": "binance"},
            {"profit_percent": 2.5, "buy_exchange": "kraken"},  # Beste
            {"profit_percent": 1.0, "buy_exchange": "coinbase"},
        ]

        best = get_best_arbitrage_opportunity(opportunities)

        assert best["profit_percent"] == 2.5
        assert best["buy_exchange"] == "kraken"

    def test_best_opportunity_empty_list(self):
        """Test beste Möglichkeit bei leerer Liste"""
        best = get_best_arbitrage_opportunity([])
        assert best == {}

    def test_best_opportunity_single_item(self):
        """Test beste Möglichkeit mit einem Element"""
        opportunities = [{"profit_percent": 1.5, "buy_exchange": "binance"}]

        best = get_best_arbitrage_opportunity(opportunities)

        assert best == opportunities[0]


class TestArbitrageDetectorEdgeCases:
    """Tests für Edge Cases im Arbitrage Detector"""

    def test_very_small_price_differences(self):
        """Test sehr kleine Preisunterschiede"""
        prices = {"binance": 45000.00, "coinbase": 45000.01}  # Winziger Unterschied

        opportunities = detect_arbitrage_opportunities(prices, threshold=0.0001)

        assert len(opportunities) == 0  # Zu klein für sinnvolle Arbitrage

    def test_extreme_price_differences(self):
        """Test extreme Preisunterschiede"""
        prices = {
            "binance": 45000.0,
            "broken_exchange": 90000.0,  # 100% Unterschied - wahrscheinlich Fehler
        }

        opportunities = detect_arbitrage_opportunities(prices, threshold=0.01)

        assert len(opportunities) == 1
        best_opp = opportunities[0]
        assert best_opp["profit_percent"] == 100.0

    def test_single_exchange_prices(self):
        """Test mit nur einem Exchange"""
        prices = {"binance": 45000.0}

        opportunities = detect_arbitrage_opportunities(prices, threshold=0.01)

        assert opportunities == []
