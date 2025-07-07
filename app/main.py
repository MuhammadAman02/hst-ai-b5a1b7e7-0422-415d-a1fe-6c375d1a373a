"""
Pakistani Bank Fraud Detection System - Main Application
UI components and page definitions using NiceGUI framework.
"""

from nicegui import ui, app
import asyncio
from typing import Dict, Any
import time

from app.config import settings
from app.core.logging import get_logger
from app.core.health import HealthCheck

logger = get_logger("main")


class FraudDetectionUI:
    """Main UI class for the fraud detection system."""
    
    def __init__(self):
        self.transaction_history = []
        self.fraud_alerts = []
        self.system_stats = {
            "total_transactions": 0,
            "fraud_detected": 0,
            "fraud_rate": 0.0,
            "last_update": time.time()
        }
    
    async def analyze_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate fraud analysis of a transaction."""
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Simple fraud detection logic (replace with actual ML model)
        amount = float(transaction_data.get("amount", 0))
        account_age = int(transaction_data.get("account_age_days", 365))
        transaction_hour = int(transaction_data.get("hour", 12))
        
        # Risk factors
        risk_score = 0.0
        risk_factors = []
        
        # High amount transactions
        if amount > settings.max_transaction_amount * 0.8:
            risk_score += 0.3
            risk_factors.append("High transaction amount")
        
        # New account
        if account_age < 30:
            risk_score += 0.2
            risk_factors.append("New account")
        
        # Unusual hours (late night/early morning)
        if transaction_hour < 6 or transaction_hour > 22:
            risk_score += 0.1
            risk_factors.append("Unusual transaction time")
        
        # Random factor for demonstration
        import random
        risk_score += random.uniform(0, 0.4)
        
        is_fraud = risk_score >= settings.fraud_threshold
        
        result = {
            "transaction_id": transaction_data.get("transaction_id", f"TXN_{int(time.time())}"),
            "amount": amount,
            "risk_score": round(risk_score, 3),
            "is_fraud": is_fraud,
            "risk_factors": risk_factors,
            "timestamp": time.time(),
            "status": "FRAUD DETECTED" if is_fraud else "APPROVED"
        }
        
        # Update statistics
        self.system_stats["total_transactions"] += 1
        if is_fraud:
            self.system_stats["fraud_detected"] += 1
            self.fraud_alerts.append(result)
        
        self.system_stats["fraud_rate"] = (
            self.system_stats["fraud_detected"] / self.system_stats["total_transactions"] * 100
        )
        self.system_stats["last_update"] = time.time()
        
        self.transaction_history.append(result)
        
        # Keep only last 100 transactions
        if len(self.transaction_history) > 100:
            self.transaction_history = self.transaction_history[-100:]
        
        return result


# Global UI instance
fraud_ui = FraudDetectionUI()


@ui.page('/')
async def index():
    """Main dashboard page."""
    ui.add_head_html('''
        <style>
            .fraud-card { border-left: 4px solid #ef4444; }
            .safe-card { border-left: 4px solid #10b981; }
            .warning-card { border-left: 4px solid #f59e0b; }
            .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .transaction-row { transition: all 0.3s ease; }
            .transaction-row:hover { background-color: #f8fafc; }
        </style>
    ''')
    
    with ui.column().classes('w-full max-w-7xl mx-auto p-4'):
        # Header
        with ui.row().classes('w-full items-center justify-between mb-6'):
            ui.label('🏦 Pakistani Bank Fraud Detection System').classes('text-3xl font-bold text-gray-800')
            ui.label(f'v{settings.app_version}').classes('text-sm text-gray-500')
        
        # Statistics Cards
        stats_container = ui.row().classes('w-full gap-4 mb-6')
        
        with stats_container:
            with ui.card().classes('stat-card text-white p-4 flex-1'):
                ui.label('Total Transactions').classes('text-sm opacity-80')
                total_label = ui.label('0').classes('text-2xl font-bold')
            
            with ui.card().classes('stat-card text-white p-4 flex-1'):
                ui.label('Fraud Detected').classes('text-sm opacity-80')
                fraud_label = ui.label('0').classes('text-2xl font-bold')
            
            with ui.card().classes('stat-card text-white p-4 flex-1'):
                ui.label('Fraud Rate').classes('text-sm opacity-80')
                rate_label = ui.label('0.0%').classes('text-2xl font-bold')
            
            with ui.card().classes('stat-card text-white p-4 flex-1'):
                ui.label('System Status').classes('text-sm opacity-80')
                status_label = ui.label('🟢 Online').classes('text-2xl font-bold')
        
        # Transaction Analysis Form
        with ui.card().classes('w-full p-6 mb-6'):
            ui.label('🔍 Analyze New Transaction').classes('text-xl font-semibold mb-4')
            
            with ui.row().classes('w-full gap-4'):
                transaction_id = ui.input('Transaction ID', placeholder='TXN_123456').classes('flex-1')
                amount = ui.number('Amount (PKR)', value=50000, format='%.2f').classes('flex-1')
                account_age = ui.number('Account Age (days)', value=365, format='%.0f').classes('flex-1')
                hour = ui.number('Transaction Hour (0-23)', value=14, format='%.0f').classes('flex-1')
            
            analyze_button = ui.button('🔍 Analyze Transaction', 
                                     on_click=lambda: analyze_transaction_handler()).classes('mt-4 bg-blue-600 text-white')
            
            # Result display
            result_container = ui.column().classes('mt-4')
        
        # Recent Transactions
        with ui.card().classes('w-full p-6'):
            ui.label('📊 Recent Transactions').classes('text-xl font-semibold mb-4')
            transactions_container = ui.column().classes('w-full')
            
            # Initial empty state
            with transactions_container:
                ui.label('No transactions analyzed yet. Use the form above to analyze your first transaction.').classes('text-gray-500 text-center py-8')
        
        async def analyze_transaction_handler():
            """Handle transaction analysis."""
            try:
                # Validate inputs
                if not transaction_id.value:
                    ui.notify('Please enter a transaction ID', type='warning')
                    return
                
                if not amount.value or amount.value <= 0:
                    ui.notify('Please enter a valid amount', type='warning')
                    return
                
                # Show loading state
                analyze_button.props('loading')
                result_container.clear()
                
                with result_container:
                    ui.spinner(size='lg')
                    ui.label('Analyzing transaction...').classes('text-gray-600')
                
                # Prepare transaction data
                transaction_data = {
                    "transaction_id": transaction_id.value,
                    "amount": amount.value,
                    "account_age_days": account_age.value or 365,
                    "hour": hour.value or 12
                }
                
                # Analyze transaction
                result = await fraud_ui.analyze_transaction(transaction_data)
                
                # Display result
                result_container.clear()
                
                with result_container:
                    card_class = 'fraud-card' if result['is_fraud'] else 'safe-card'
                    
                    with ui.card().classes(f'{card_class} p-4'):
                        with ui.row().classes('w-full items-center justify-between'):
                            ui.label(f"Transaction {result['transaction_id']}").classes('font-semibold')
                            status_color = 'text-red-600' if result['is_fraud'] else 'text-green-600'
                            ui.label(result['status']).classes(f'{status_color} font-bold')
                        
                        with ui.row().classes('w-full gap-4 mt-2'):
                            ui.label(f"Amount: PKR {result['amount']:,.2f}").classes('text-gray-700')
                            ui.label(f"Risk Score: {result['risk_score']:.3f}").classes('text-gray-700')
                        
                        if result['risk_factors']:
                            ui.label('Risk Factors:').classes('font-semibold mt-2')
                            for factor in result['risk_factors']:
                                ui.label(f"• {factor}").classes('text-sm text-gray-600 ml-4')
                
                # Update statistics
                total_label.text = str(fraud_ui.system_stats["total_transactions"])
                fraud_label.text = str(fraud_ui.system_stats["fraud_detected"])
                rate_label.text = f"{fraud_ui.system_stats['fraud_rate']:.1f}%"
                
                # Update transactions list
                update_transactions_list()
                
                # Clear form
                transaction_id.value = ''
                amount.value = 50000
                
                # Show success notification
                if result['is_fraud']:
                    ui.notify('🚨 FRAUD DETECTED! Transaction flagged for review.', type='negative')
                else:
                    ui.notify('✅ Transaction approved.', type='positive')
                
            except Exception as e:
                logger.error(f"Error analyzing transaction: {e}")
                result_container.clear()
                with result_container:
                    ui.label(f'Error: {str(e)}').classes('text-red-600')
                ui.notify('Error analyzing transaction', type='negative')
            
            finally:
                analyze_button.props(remove='loading')
        
        def update_transactions_list():
            """Update the transactions list display."""
            transactions_container.clear()
            
            if not fraud_ui.transaction_history:
                with transactions_container:
                    ui.label('No transactions analyzed yet.').classes('text-gray-500 text-center py-4')
                return
            
            # Show recent transactions (last 10)
            recent_transactions = fraud_ui.transaction_history[-10:][::-1]  # Reverse to show newest first
            
            with transactions_container:
                for txn in recent_transactions:
                    card_class = 'fraud-card' if txn['is_fraud'] else 'safe-card'
                    
                    with ui.card().classes(f'{card_class} p-3 mb-2 transaction-row'):
                        with ui.row().classes('w-full items-center justify-between'):
                            with ui.column().classes('flex-1'):
                                ui.label(f"ID: {txn['transaction_id']}").classes('font-semibold text-sm')
                                ui.label(f"PKR {txn['amount']:,.2f}").classes('text-gray-700')
                            
                            with ui.column().classes('text-right'):
                                status_color = 'text-red-600' if txn['is_fraud'] else 'text-green-600'
                                ui.label(txn['status']).classes(f'{status_color} font-bold text-sm')
                                ui.label(f"Risk: {txn['risk_score']:.3f}").classes('text-gray-500 text-xs')


@ui.page('/health')
async def health_page():
    """System health monitoring page."""
    ui.add_head_html('<title>System Health - Pakistani Bank Fraud Detection</title>')
    
    with ui.column().classes('w-full max-w-4xl mx-auto p-4'):
        ui.label('🏥 System Health Monitor').classes('text-3xl font-bold text-gray-800 mb-6')
        
        # Health status container
        health_container = ui.column().classes('w-full')
        
        async def refresh_health():
            """Refresh health status."""
            health_container.clear()
            
            with health_container:
                ui.spinner(size='lg')
                ui.label('Checking system health...').classes('text-gray-600')
            
            try:
                health_data = HealthCheck.check_all()
                
                health_container.clear()
                
                with health_container:
                    # Overall status
                    status_color = {
                        'healthy': 'text-green-600',
                        'warning': 'text-yellow-600',
                        'error': 'text-red-600'
                    }.get(health_data['status'], 'text-gray-600')
                    
                    with ui.card().classes('p-4 mb-4'):
                        ui.label(f"Overall Status: {health_data['status'].upper()}").classes(f'{status_color} text-xl font-bold')
                        ui.label(f"Last Check: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(health_data['timestamp']))}").classes('text-gray-500')
                    
                    # Individual checks
                    for check_name, check_data in health_data['checks'].items():
                        check_color = {
                            'healthy': 'safe-card',
                            'warning': 'warning-card',
                            'error': 'fraud-card'
                        }.get(check_data['status'], 'safe-card')
                        
                        with ui.card().classes(f'{check_color} p-4 mb-4'):
                            ui.label(check_name.replace('_', ' ').title()).classes('font-semibold text-lg mb-2')
                            
                            # Display check details
                            for key, value in check_data.items():
                                if key != 'status':
                                    if isinstance(value, (list, dict)):
                                        ui.label(f"{key}: {str(value)}").classes('text-sm text-gray-700 font-mono')
                                    else:
                                        ui.label(f"{key}: {value}").classes('text-sm text-gray-700')
            
            except Exception as e:
                health_container.clear()
                with health_container:
                    ui.label(f'Error checking health: {str(e)}').classes('text-red-600')
        
        # Refresh button
        ui.button('🔄 Refresh Health Status', on_click=refresh_health).classes('mb-4 bg-blue-600 text-white')
        
        # Initial health check
        await refresh_health()


def main():
    """Main application entry point."""
    try:
        # Validate configuration
        if not settings.validate_config():
            logger.error("Configuration validation failed")
            return
        
        # Display configuration
        settings.display_config()
        
        # Configure NiceGUI app
        app.add_static_files('/static', 'static')
        
        # Start the application
        logger.info(f"🚀 Starting server on {settings.host}:{settings.port}")
        
        ui.run(
            host=settings.host,
            port=settings.port,
            reload=settings.reload,
            show=settings.is_development,
            title=settings.app_name,
            favicon='🏦'
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


if __name__ == "__main__":
    main()