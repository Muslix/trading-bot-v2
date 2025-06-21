"""
Export Utility Plugin - CSV/PDF generation and reporting functionality
"""

import csv
import json
import io
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd

from ..base import UtilPlugin, UtilConfig


class ExportUtil(UtilPlugin):
    """
    Export utility plugin for generating reports and exports.
    """
    
    def __init__(self, config: UtilConfig):
        super().__init__(config)
        self.export_count = 0
        self.last_export_time = None
        
        # Report templates
        self.report_templates = {
            "portfolio_summary": {
                "columns": ["symbol", "current_price", "value", "market_cap", "volume_24h", "change_24h"],
                "title": "Portfolio Summary Report"
            },
            "arbitrage_opportunities": {
                "columns": ["symbol", "buy_exchange", "sell_exchange", "buy_price", "sell_price", "profit_percentage", "potential_profit"],
                "title": "Arbitrage Opportunities Report"
            },
            "performance_metrics": {
                "columns": ["symbol", "annual_return", "volatility", "sharpe_ratio", "max_drawdown", "sortino_ratio"],
                "title": "Performance Metrics Report"
            },
            "trading_history": {
                "columns": ["timestamp", "symbol", "action", "amount", "price", "total_value", "exchange"],
                "title": "Trading History Report"
            },
            "tax_report": {
                "columns": ["date", "symbol", "type", "amount", "price_usd", "total_usd", "gain_loss", "exchange"],
                "title": "Tax Report"
            }
        }
    
    async def _initialize_util(self) -> bool:
        """Initialize export utility."""
        try:
            # Try to import optional dependencies
            try:
                import matplotlib
                matplotlib.use('Agg')  # Non-interactive backend
                import matplotlib.pyplot as plt
                import seaborn as sns
                self.plotting_available = True
                self.plt = plt
                self.sns = sns
            except ImportError:
                self.plotting_available = False
                self.logger.warning("Matplotlib/Seaborn not available - chart generation disabled")
            
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet
                self.pdf_available = True
                self.reportlab = {
                    'colors': colors,
                    'pagesizes': {'letter': letter, 'A4': A4},
                    'SimpleDocTemplate': SimpleDocTemplate,
                    'Table': Table,
                    'TableStyle': TableStyle,
                    'Paragraph': Paragraph,
                    'Spacer': Spacer,
                    'getSampleStyleSheet': getSampleStyleSheet
                }
            except ImportError:
                self.pdf_available = False
                self.logger.warning("ReportLab not available - PDF generation disabled")
            
            self.logger.info(f"Export utility initialized (PDF: {self.pdf_available}, Charts: {self.plotting_available})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize export utility: {e}")
            return False
    
    async def process_data(self, data: Dict[str, Any]) -> Any:
        """
        Process export operations.
        
        Args:
            data: Contains action and parameters
            
        Returns:
            Result based on action
        """
        action = data.get("action", "export_csv")
        
        if action == "export_csv":
            return await self._export_csv(data)
        elif action == "export_pdf":
            return await self._export_pdf(data)
        elif action == "export_json":
            return await self._export_json(data)
        elif action == "generate_chart":
            return await self._generate_chart(data)
        elif action == "create_tax_report":
            return await self._create_tax_report(data)
        elif action == "create_portfolio_report":
            return await self._create_portfolio_report(data)
        elif action == "get_templates":
            return self._get_report_templates()
        elif action == "add_template":
            return self._add_report_template(data)
        elif action == "get_stats":
            return self._get_export_stats()
        else:
            raise ValueError(f"Unknown export action: {action}")
    
    async def _export_csv(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Export data to CSV format."""
        try:
            export_data = data.get("data", [])
            filename = data.get("filename", f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            template_name = data.get("template")
            custom_columns = data.get("columns")
            
            if not export_data:
                return {"success": False, "error": "No data provided for export"}
            
            # Determine columns to export
            if custom_columns:
                columns = custom_columns
            elif template_name and template_name in self.report_templates:
                columns = self.report_templates[template_name]["columns"]
            else:
                # Auto-detect columns from data
                if isinstance(export_data[0], dict):
                    columns = list(export_data[0].keys())
                else:
                    return {"success": False, "error": "Cannot determine columns for export"}
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=columns)
            writer.writeheader()
            
            for row in export_data:
                if isinstance(row, dict):
                    # Filter only the columns we want
                    filtered_row = {col: row.get(col, '') for col in columns}
                    writer.writerow(filtered_row)
            
            csv_content = output.getvalue()
            output.close()
            
            # Update stats
            self.export_count += 1
            self.last_export_time = datetime.now()
            
            return {
                "success": True,
                "format": "csv",
                "filename": filename,
                "content": csv_content,
                "rows_exported": len(export_data),
                "columns": columns,
                "size_bytes": len(csv_content.encode('utf-8'))
            }
            
        except Exception as e:
            self.logger.error(f"CSV export failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _export_pdf(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Export data to PDF format."""
        try:
            if not self.pdf_available:
                return {"success": False, "error": "PDF generation not available - install reportlab"}
            
            export_data = data.get("data", [])
            filename = data.get("filename", f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            title = data.get("title", "Trading Bot Report")
            template_name = data.get("template")
            
            if not export_data:
                return {"success": False, "error": "No data provided for export"}
            
            # Create PDF in memory
            buffer = io.BytesIO()
            doc = self.reportlab['SimpleDocTemplate'](buffer, pagesize=self.reportlab['pagesizes']['A4'])
            
            # Build PDF content
            story = []
            styles = self.reportlab['getSampleStyleSheet']()
            
            # Title
            title_para = self.reportlab['Paragraph'](title, styles['Title'])
            story.append(title_para)
            story.append(self.reportlab['Spacer'](1, 12))
            
            # Report metadata
            metadata = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            metadata_para = self.reportlab['Paragraph'](metadata, styles['Normal'])
            story.append(metadata_para)
            story.append(self.reportlab['Spacer'](1, 12))
            
            # Determine columns
            if template_name and template_name in self.report_templates:
                columns = self.report_templates[template_name]["columns"]
            else:
                columns = list(export_data[0].keys()) if export_data and isinstance(export_data[0], dict) else []
            
            # Create table data
            table_data = [columns]  # Header row
            for row in export_data:
                if isinstance(row, dict):
                    table_row = [str(row.get(col, '')) for col in columns]
                    table_data.append(table_row)
            
            # Create table
            table = self.reportlab['Table'](table_data)
            table.setStyle(self.reportlab['TableStyle']([
                ('BACKGROUND', (0, 0), (-1, 0), self.reportlab['colors'].grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.reportlab['colors'].whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), self.reportlab['colors'].beige),
                ('GRID', (0, 0), (-1, -1), 1, self.reportlab['colors'].black)
            ]))
            
            story.append(table)
            
            # Build PDF
            doc.build(story)
            pdf_content = buffer.getvalue()
            buffer.close()
            
            # Update stats
            self.export_count += 1
            self.last_export_time = datetime.now()
            
            return {
                "success": True,
                "format": "pdf",
                "filename": filename,
                "content": pdf_content,
                "rows_exported": len(export_data),
                "columns": columns,
                "size_bytes": len(pdf_content)
            }
            
        except Exception as e:
            self.logger.error(f"PDF export failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _export_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Export data to JSON format."""
        try:
            export_data = data.get("data", [])
            filename = data.get("filename", f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            pretty = data.get("pretty", True)
            
            if not export_data:
                return {"success": False, "error": "No data provided for export"}
            
            # Create JSON content
            if pretty:
                json_content = json.dumps(export_data, indent=2, default=str)
            else:
                json_content = json.dumps(export_data, default=str)
            
            # Update stats
            self.export_count += 1
            self.last_export_time = datetime.now()
            
            return {
                "success": True,
                "format": "json",
                "filename": filename,
                "content": json_content,
                "records_exported": len(export_data),
                "size_bytes": len(json_content.encode('utf-8'))
            }
            
        except Exception as e:
            self.logger.error(f"JSON export failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate charts from data."""
        try:
            if not self.plotting_available:
                return {"success": False, "error": "Chart generation not available - install matplotlib/seaborn"}
            
            chart_data = data.get("data", [])
            chart_type = data.get("chart_type", "line")
            title = data.get("title", "Chart")
            x_column = data.get("x_column")
            y_column = data.get("y_column")
            filename = data.get("filename", f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            if not chart_data:
                return {"success": False, "error": "No data provided for chart"}
            
            # Convert to DataFrame for easier plotting
            df = pd.DataFrame(chart_data)
            
            # Create plot
            self.plt.figure(figsize=(10, 6))
            
            if chart_type == "line":
                if x_column and y_column:
                    self.plt.plot(df[x_column], df[y_column])
                else:
                    self.plt.plot(df.index, df.iloc[:, 0])
                    
            elif chart_type == "bar":
                if x_column and y_column:
                    self.plt.bar(df[x_column], df[y_column])
                else:
                    self.plt.bar(df.index, df.iloc[:, 0])
                    
            elif chart_type == "pie":
                if y_column:
                    self.plt.pie(df[y_column], labels=df[x_column] if x_column else None, autopct='%1.1f%%')
                else:
                    self.plt.pie(df.iloc[:, 0], autopct='%1.1f%%')
                    
            elif chart_type == "scatter":
                if x_column and y_column:
                    self.plt.scatter(df[x_column], df[y_column])
                    
            self.plt.title(title)
            self.plt.tight_layout()
            
            # Save to buffer
            buffer = io.BytesIO()
            self.plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            self.plt.close()
            
            chart_content = buffer.getvalue()
            buffer.close()
            
            # Update stats
            self.export_count += 1
            self.last_export_time = datetime.now()
            
            return {
                "success": True,
                "format": "png",
                "chart_type": chart_type,
                "filename": filename,
                "content": chart_content,
                "size_bytes": len(chart_content)
            }
            
        except Exception as e:
            self.logger.error(f"Chart generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_tax_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a tax report for trading activities."""
        try:
            trading_data = data.get("trading_data", [])
            year = data.get("year", datetime.now().year)
            currency = data.get("currency", "USD")
            
            if not trading_data:
                return {"success": False, "error": "No trading data provided"}
            
            # Process trading data for tax purposes
            tax_events = []
            total_gains = 0
            total_losses = 0
            
            for trade in trading_data:
                if isinstance(trade, dict):
                    trade_date = trade.get("date", "")
                    symbol = trade.get("symbol", "")
                    trade_type = trade.get("type", "")  # buy/sell
                    amount = float(trade.get("amount", 0))
                    price = float(trade.get("price", 0))
                    total_value = amount * price
                    
                    # Calculate gain/loss (simplified - real tax calc would need FIFO/LIFO)
                    gain_loss = 0
                    if trade_type.lower() == "sell":
                        # Simplified: assume 10% gain for demo
                        gain_loss = total_value * 0.1
                        if gain_loss > 0:
                            total_gains += gain_loss
                        else:
                            total_losses += abs(gain_loss)
                    
                    tax_events.append({
                        "date": trade_date,
                        "symbol": symbol,
                        "type": trade_type,
                        "amount": amount,
                        "price_usd": price,
                        "total_usd": total_value,
                        "gain_loss": gain_loss,
                        "exchange": trade.get("exchange", "")
                    })
            
            # Create summary
            tax_summary = {
                "year": year,
                "currency": currency,
                "total_trades": len(tax_events),
                "total_gains": total_gains,
                "total_losses": total_losses,
                "net_gain_loss": total_gains - total_losses,
                "events": tax_events
            }
            
            return {
                "success": True,
                "report_type": "tax_report",
                "tax_summary": tax_summary,
                "disclaimer": "This is a simplified tax report. Consult a tax professional for accurate tax calculations."
            }
            
        except Exception as e:
            self.logger.error(f"Tax report generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_portfolio_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive portfolio report."""
        try:
            portfolio_data = data.get("portfolio_data", {})
            performance_data = data.get("performance_data", {})
            timeframe = data.get("timeframe", "30d")
            
            if not portfolio_data:
                return {"success": False, "error": "No portfolio data provided"}
            
            # Create portfolio summary
            total_value = sum(asset.get("value", 0) for asset in portfolio_data.values())
            asset_count = len(portfolio_data)
            
            # Top performers
            sorted_assets = sorted(
                portfolio_data.items(),
                key=lambda x: x[1].get("change_24h", 0),
                reverse=True
            )
            
            top_performers = sorted_assets[:5]
            worst_performers = sorted_assets[-5:]
            
            # Risk metrics (if available)
            portfolio_metrics = {
                "total_value": total_value,
                "asset_count": asset_count,
                "diversification_score": min(100, asset_count * 10),  # Simplified
                "risk_level": "Medium"  # Simplified
            }
            
            # Add performance data if available
            if performance_data:
                portfolio_metrics.update({
                    "sharpe_ratio": performance_data.get("sharpe_ratio", 0),
                    "max_drawdown": performance_data.get("max_drawdown", 0),
                    "annual_return": performance_data.get("annual_return", 0)
                })
            
            report = {
                "report_date": datetime.now().isoformat(),
                "timeframe": timeframe,
                "portfolio_metrics": portfolio_metrics,
                "top_performers": [{"symbol": k, **v} for k, v in top_performers],
                "worst_performers": [{"symbol": k, **v} for k, v in worst_performers],
                "all_assets": [{"symbol": k, **v} for k, v in portfolio_data.items()]
            }
            
            return {
                "success": True,
                "report_type": "portfolio_report",
                "report": report
            }
            
        except Exception as e:
            self.logger.error(f"Portfolio report generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_report_templates(self) -> Dict[str, Any]:
        """Get available report templates."""
        return {
            "success": True,
            "templates": self.report_templates
        }
    
    def _add_report_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new report template."""
        template_name = data.get("name", "")
        template_config = data.get("config", {})
        
        if not template_name or not template_config:
            return {"success": False, "error": "Template name and config required"}
        
        self.report_templates[template_name] = template_config
        
        return {
            "success": True,
            "template_added": template_name,
            "total_templates": len(self.report_templates)
        }
    
    def _get_export_stats(self) -> Dict[str, Any]:
        """Get export statistics."""
        return {
            "total_exports": self.export_count,
            "last_export_time": self.last_export_time.isoformat() if self.last_export_time else None,
            "available_formats": {
                "csv": True,
                "json": True,
                "pdf": self.pdf_available,
                "charts": self.plotting_available
            },
            "available_templates": list(self.report_templates.keys()),
            "plugin_name": self.name,
            "enabled": self.config.enabled
        }