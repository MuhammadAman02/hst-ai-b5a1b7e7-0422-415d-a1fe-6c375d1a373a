"""
Pakistani Bank Fraud Detection System - Main UI Application
Real-time fraud monitoring dashboard with professional banking interface.
"""

from nicegui import ui, app
from datetime import datetime, timedelta
import asyncio
from typing import List, Dict
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from app.config import settings
from core.database import init_db
from core.utils import format_currency, mask_account_number, mask_cnic
from services.fraud_detection import fraud_detector
from services.transaction_service import transaction_service
from services.alert_service import alert_service
from models.schemas import TransactionCreate, TransactionType, RiskLevel

# Initialize database
init_db()

# Global state for real-time updates
dashboard_data = {
    'transactions': [],
    'alerts': [],
    'stats': {},
    'last_update': datetime.utcnow()
}

# Professional Pakistani banking color scheme
COLORS = {
    'primary': '#1a365d',      # Deep blue
    'secondary': '#2d3748',    # Dark gray
    'success': '#38a169',      # Green
    'warning': '#d69e2e',      # Orange
    'danger': '#e53e3e',       # Red
    'info': '#3182ce',         # Blue
    'light': '#f7fafc',        # Light gray
    'dark': '#1a202c'          # Very dark
}

def check_dependencies():
    """Verify all required dependencies are available."""
    required_packages = ['nicegui', 'uvicorn', 'python_dotenv', 'sqlalchemy', 'pandas', 'scikit_learn', 'plotly']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_').replace('scikit_learn', 'sklearn'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print(f"📦 Install with: pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All dependencies available")
    return True

async def update_dashboard_data():
    """Update dashboard data in background."""
    while True:
        try:
            # Update transaction stats
            dashboard_data['stats'] = transaction_service.get_transaction_stats()
            
            # Update recent flagged transactions
            dashboard_data['transactions'] = transaction_service.get_flagged_transactions(20)
            
            # Update active alerts
            dashboard_data['alerts'] = alert_service.get_active_alerts(20)
            
            # Update alert stats
            alert_stats = alert_service.get_alert_stats()
            dashboard_data['stats'].update(alert_stats)
            
            dashboard_data['last_update'] = datetime.utcnow()
            
        except Exception as e:
            print(f"Error updating dashboard data: {e}")
        
        await asyncio.sleep(30)  # Update every 30 seconds

def create_stats_cards():
    """Create statistics cards for the dashboard."""
    stats = dashboard_data.get('stats', {})
    
    with ui.row().classes('w-full gap-4 mb-6'):
        # Total Transactions Card
        with ui.card().classes('flex-1 p-4 bg-white shadow-lg'):
            with ui.row().classes('items-center justify-between'):
                with ui.column():
                    ui.label('Total Transactions').classes('text-sm text-gray-600')
                    ui.label(f"{stats.get('total_transactions', 0):,}").classes('text-2xl font-bold text-blue-600')
                ui.icon('account_balance', size='2rem').classes('text-blue-500')
        
        # Flagged Transactions Card
        with ui.card().classes('flex-1 p-4 bg-white shadow-lg'):
            with ui.row().classes('items-center justify-between'):
                with ui.column():
                    ui.label('Flagged Transactions').classes('text-sm text-gray-600')
                    ui.label(f"{stats.get('flagged_transactions', 0):,}").classes('text-2xl font-bold text-red-600')
                ui.icon('flag', size='2rem').classes('text-red-500')
        
        # Active Alerts Card
        with ui.card().classes('flex-1 p-4 bg-white shadow-lg'):
            with ui.row().classes('items-center justify-between'):
                with ui.column():
                    ui.label('Active Alerts').classes('text-sm text-gray-600')
                    ui.label(f"{stats.get('active_alerts', 0):,}").classes('text-2xl font-bold text-orange-600')
                ui.icon('warning', size='2rem').classes('text-orange-500')
        
        # Fraud Rate Card
        with ui.card().classes('flex-1 p-4 bg-white shadow-lg'):
            with ui.row().classes('items-center justify-between'):
                with ui.column():
                    ui.label('Fraud Rate').classes('text-sm text-gray-600')
                    ui.label(f"{stats.get('fraud_rate', 0):.2f}%").classes('text-2xl font-bold text-purple-600')
                ui.icon('analytics', size='2rem').classes('text-purple-500')

def create_fraud_chart():
    """Create fraud detection chart."""
    stats = dashboard_data.get('stats', {})
    
    # Sample data for demonstration
    fraud_data = {
        'Risk Level': ['Low', 'Medium', 'High', 'Critical'],
        'Count': [
            stats.get('total_transactions', 100) - stats.get('flagged_transactions', 10),
            max(0, stats.get('flagged_transactions', 10) - stats.get('high_risk_transactions', 5)),
            max(0, stats.get('high_risk_transactions', 5) - stats.get('critical_alerts', 2)),
            stats.get('critical_alerts', 2)
        ],
        'Color': ['#38a169', '#d69e2e', '#e53e3e', '#9b1c1c']
    }
    
    fig = go.Figure(data=[
        go.Bar(
            x=fraud_data['Risk Level'],
            y=fraud_data['Count'],
            marker_color=fraud_data['Color'],
            text=fraud_data['Count'],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title='Fraud Risk Distribution',
        xaxis_title='Risk Level',
        yaxis_title='Number of Transactions',
        template='plotly_white',
        height=300
    )
    
    return fig

def create_transaction_timeline():
    """Create transaction timeline chart."""
    transactions = dashboard_data.get('transactions', [])
    
    if not transactions:
        # Sample data for demonstration
        dates = [(datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7, 0, -1)]
        counts = [15, 23, 18, 31, 27, 19, 25]
    else:
        # Group transactions by date
        df = pd.DataFrame([{
            'date': t.timestamp.strftime('%Y-%m-%d'),
            'fraud_score': t.fraud_score
        } for t in transactions])
        
        daily_counts = df.groupby('date').size().reset_index(name='count')
        dates = daily_counts['date'].tolist()
        counts = daily_counts['count'].tolist()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=counts,
        mode='lines+markers',
        name='Flagged Transactions',
        line=dict(color='#e53e3e', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Flagged Transactions Timeline',
        xaxis_title='Date',
        yaxis_title='Number of Flagged Transactions',
        template='plotly_white',
        height=300
    )
    
    return fig

def create_transaction_table():
    """Create recent transactions table."""
    transactions = dashboard_data.get('transactions', [])
    
    if not transactions:
        ui.label('No flagged transactions found').classes('text-gray-500 text-center p-4')
        return
    
    # Table headers
    columns = [
        {'name': 'transaction_id', 'label': 'Transaction ID', 'field': 'transaction_id'},
        {'name': 'account', 'label': 'Account', 'field': 'account'},
        {'name': 'amount', 'label': 'Amount', 'field': 'amount'},
        {'name': 'type', 'label': 'Type', 'field': 'type'},
        {'name': 'fraud_score', 'label': 'Fraud Score', 'field': 'fraud_score'},
        {'name': 'risk_level', 'label': 'Risk Level', 'field': 'risk_level'},
        {'name': 'timestamp', 'label': 'Time', 'field': 'timestamp'}
    ]
    
    # Table rows
    rows = []
    for transaction in transactions[:10]:  # Show only first 10
        rows.append({
            'transaction_id': transaction.transaction_id[:12] + '...',
            'account': mask_account_number(transaction.account_number),
            'amount': format_currency(transaction.amount),
            'type': transaction.transaction_type.title(),
            'fraud_score': f"{transaction.fraud_score:.3f}",
            'risk_level': transaction.risk_level.value.upper(),
            'timestamp': transaction.timestamp.strftime('%H:%M:%S')
        })
    
    ui.table(columns=columns, rows=rows).classes('w-full')

def create_alerts_table():
    """Create active alerts table."""
    alerts = dashboard_data.get('alerts', [])
    
    if not alerts:
        ui.label('No active alerts').classes('text-gray-500 text-center p-4')
        return
    
    # Table headers
    columns = [
        {'name': 'alert_type', 'label': 'Alert Type', 'field': 'alert_type'},
        {'name': 'account', 'label': 'Account', 'field': 'account'},
        {'name': 'severity', 'label': 'Severity', 'field': 'severity'},
        {'name': 'fraud_score', 'label': 'Score', 'field': 'fraud_score'},
        {'name': 'message', 'label': 'Message', 'field': 'message'},
        {'name': 'timestamp', 'label': 'Time', 'field': 'timestamp'}
    ]
    
    # Table rows
    rows = []
    for alert in alerts[:10]:  # Show only first 10
        severity_color = {
            'critical': '🔴',
            'high': '🟠', 
            'medium': '🟡',
            'low': '🟢'
        }.get(alert.severity.value, '⚪')
        
        rows.append({
            'alert_type': alert.alert_type.replace('_', ' ').title(),
            'account': mask_account_number(alert.account_number),
            'severity': f"{severity_color} {alert.severity.value.upper()}",
            'fraud_score': f"{alert.fraud_score:.3f}",
            'message': alert.message[:50] + '...' if len(alert.message) > 50 else alert.message,
            'timestamp': alert.timestamp.strftime('%H:%M:%S')
        })
    
    ui.table(columns=columns, rows=rows).classes('w-full')

async def simulate_transaction():
    """Simulate a new transaction for testing."""
    import random
    
    # Sample account numbers
    accounts = ['1234567890', '9876543210', '5555666677', '1111222233']
    
    # Sample transaction types
    types = list(TransactionType)
    
    # Create random transaction
    transaction_data = TransactionCreate(
        transaction_id=f"TXN{random.randint(100000, 999999)}",
        account_number=random.choice(accounts),
        transaction_type=random.choice(types),
        amount=random.uniform(1000, 500000),  # 1K to 500K PKR
        location=random.choice(['Karachi', 'Lahore', 'Islamabad', 'Unknown']),
        device_info='Mobile App',
        description='Test transaction'
    )
    
    try:
        # Process transaction
        transaction = transaction_service.create_transaction(transaction_data)
        
        # Create alert if high risk
        if transaction.fraud_score >= 0.7:
            fraud_score_obj = fraud_detector.calculate_fraud_score(transaction)
            alert_service.create_alert(transaction, transaction.fraud_score, fraud_score_obj.risk_factors)
        
        ui.notify(f'Simulated transaction: {format_currency(transaction.amount)} (Score: {transaction.fraud_score:.3f})', 
                 type='positive' if transaction.fraud_score < 0.7 else 'negative')
        
    except Exception as e:
        ui.notify(f'Error simulating transaction: {str(e)}', type='negative')

@ui.page('/')
async def dashboard():
    """Main fraud detection dashboard."""
    
    # Add custom CSS for professional banking look
    ui.add_head_html('''
    <style>
        .q-page { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .banking-header { 
            background: linear-gradient(90deg, #1a365d 0%, #2d3748 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-2px);
        }
        .alert-critical { border-left: 4px solid #e53e3e; }
        .alert-high { border-left: 4px solid #d69e2e; }
        .alert-medium { border-left: 4px solid #3182ce; }
        .alert-low { border-left: 4px solid #38a169; }
    </style>
    ''')
    
    # Header
    with ui.card().classes('banking-header w-full'):
        with ui.row().classes('items-center justify-between w-full'):
            with ui.column():
                ui.label('🏦 Pakistani Bank Fraud Detection System').classes('text-2xl font-bold')
                ui.label(f'Real-time monitoring • Last update: {dashboard_data["last_update"].strftime("%H:%M:%S")}').classes('text-sm opacity-80')
            
            with ui.row().classes('gap-2'):
                ui.button('🔄 Refresh', on_click=lambda: ui.run_javascript('location.reload()')).classes('bg-blue-600')
                ui.button('⚡ Simulate Transaction', on_click=simulate_transaction).classes('bg-green-600')
    
    # Statistics Cards
    create_stats_cards()
    
    # Charts Row
    with ui.row().classes('w-full gap-4 mb-6'):
        # Fraud Risk Chart
        with ui.card().classes('flex-1 p-4'):
            ui.label('Fraud Risk Analysis').classes('text-lg font-semibold mb-4')
            fraud_chart = create_fraud_chart()
            ui.plotly(fraud_chart).classes('w-full')
        
        # Transaction Timeline
        with ui.card().classes('flex-1 p-4'):
            ui.label('Flagged Transactions Timeline').classes('text-lg font-semibold mb-4')
            timeline_chart = create_transaction_timeline()
            ui.plotly(timeline_chart).classes('w-full')
    
    # Tables Row
    with ui.row().classes('w-full gap-4'):
        # Recent Flagged Transactions
        with ui.card().classes('flex-1 p-4'):
            ui.label('🚩 Recent Flagged Transactions').classes('text-lg font-semibold mb-4')
            create_transaction_table()
        
        # Active Alerts
        with ui.card().classes('flex-1 p-4'):
            ui.label('🚨 Active Fraud Alerts').classes('text-lg font-semibold mb-4')
            create_alerts_table()
    
    # Model Information
    with ui.card().classes('w-full p-4 mt-6'):
        ui.label('🤖 ML Model Information').classes('text-lg font-semibold mb-4')
        model_stats = fraud_detector.get_model_stats()
        
        with ui.row().classes('gap-8'):
            ui.label(f"Model Version: {model_stats['model_version']}").classes('text-sm')
            ui.label(f"Algorithm: {model_stats['algorithm']}").classes('text-sm')
            ui.label(f"Features: {model_stats['features_count']}").classes('text-sm')
            ui.label(f"Fraud Threshold: {model_stats['fraud_threshold']}").classes('text-sm')
            ui.label(f"Status: {model_stats['model_status']}").classes('text-sm text-green-600')

@ui.page('/transactions')
async def transactions_page():
    """Transaction monitoring page."""
    ui.label('🔍 Transaction Monitoring').classes('text-2xl font-bold mb-6')
    
    # Transaction filters
    with ui.card().classes('w-full p-4 mb-6'):
        ui.label('Filters').classes('text-lg font-semibold mb-4')
        with ui.row().classes('gap-4'):
            ui.select(['All', 'Flagged Only', 'High Risk'], value='Flagged Only').classes('w-48')
            ui.input('Account Number').classes('w-48')
            ui.input('Date Range').classes('w-48')
            ui.button('Apply Filters').classes('bg-blue-600')
    
    # Detailed transaction table
    with ui.card().classes('w-full p-4'):
        ui.label('Transaction Details').classes('text-lg font-semibold mb-4')
        create_transaction_table()

@ui.page('/alerts')
async def alerts_page():
    """Alert management page."""
    ui.label('🚨 Alert Management').classes('text-2xl font-bold mb-6')
    
    # Alert statistics
    with ui.row().classes('w-full gap-4 mb-6'):
        alert_stats = dashboard_data.get('stats', {})
        
        with ui.card().classes('flex-1 p-4 alert-critical'):
            ui.label('Critical Alerts').classes('text-sm text-gray-600')
            ui.label(f"{alert_stats.get('critical_alerts', 0)}").classes('text-2xl font-bold text-red-600')
        
        with ui.card().classes('flex-1 p-4 alert-high'):
            ui.label('High Risk Alerts').classes('text-sm text-gray-600')
            ui.label(f"{alert_stats.get('high_risk_alerts', 0)}").classes('text-2xl font-bold text-orange-600')
        
        with ui.card().classes('flex-1 p-4 alert-medium'):
            ui.label('Total Active').classes('text-sm text-gray-600')
            ui.label(f"{alert_stats.get('active_alerts', 0)}").classes('text-2xl font-bold text-blue-600')
        
        with ui.card().classes('flex-1 p-4 alert-low'):
            ui.label('Resolution Rate').classes('text-sm text-gray-600')
            ui.label(f"{alert_stats.get('resolution_rate', 0):.1f}%").classes('text-2xl font-bold text-green-600')
    
    # Alert management table
    with ui.card().classes('w-full p-4'):
        ui.label('Active Alerts').classes('text-lg font-semibold mb-4')
        create_alerts_table()

def main():
    """Main application entry point."""
    if not check_dependencies():
        return
    
    print("🏦 Starting Pakistani Bank Fraud Detection System...")
    print(f"🌐 Dashboard will be available at: http://{settings.host}:{settings.port}")
    print("🔒 Features: Real-time fraud detection, ML-powered risk scoring, Professional banking UI")
    
    # Start background data update task
    app.on_startup(lambda: asyncio.create_task(update_dashboard_data()))
    
    # Run the application
    ui.run(
        host=settings.host,
        port=settings.port,
        title="Pakistani Bank Fraud Detection System",
        favicon="🏦",
        dark=False,
        show=True
    )

if __name__ == "__main__":
    main()