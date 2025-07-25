#!/usr/bin/env python3
"""
After-Tax Performance Tracking Module

This module implements comprehensive tax-aware performance tracking for the
Modern Magic Formula strategy, including:

1. Short-term vs long-term capital gains tracking
2. Tax loss harvesting opportunities
3. After-tax return calculations
4. Tax-efficient rebalancing strategies
5. State and federal tax modeling

Key Features:
- Lot-level tracking for accurate tax calculations
- Multiple tax regime support (US federal + state)
- Tax loss harvesting optimization
- After-tax performance attribution
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore')


@dataclass
class TaxLot:
    """Represents a single tax lot for tracking"""
    ticker: str
    purchase_date: datetime
    shares: float
    purchase_price: float
    current_price: float = 0.0
    sale_date: Optional[datetime] = None
    sale_price: Optional[float] = None
    
    @property
    def cost_basis(self) -> float:
        return self.shares * self.purchase_price
    
    @property
    def current_value(self) -> float:
        return self.shares * self.current_price
    
    @property
    def unrealized_gain(self) -> float:
        return self.current_value - self.cost_basis
    
    @property
    def realized_gain(self) -> Optional[float]:
        if self.sale_price is not None:
            return self.shares * (self.sale_price - self.purchase_price)
        return None
    
    @property
    def holding_period_days(self) -> int:
        end_date = self.sale_date or datetime.now()
        return (end_date - self.purchase_date).days
    
    @property
    def is_long_term(self) -> bool:
        return self.holding_period_days > 365


@dataclass
class TaxProfile:
    """Tax rates and configuration"""
    federal_short_term_rate: float = 0.37      # Top federal ordinary income rate
    federal_long_term_rate: float = 0.20       # Top federal LTCG rate
    federal_net_investment_tax: float = 0.038  # Net investment income tax
    state_tax_rate: float = 0.0                # State tax rate (varies)
    tax_loss_carryforward: float = 0.0         # Previous year losses
    
    def effective_short_term_rate(self) -> float:
        """Combined effective short-term rate"""
        return self.federal_short_term_rate + self.federal_net_investment_tax + self.state_tax_rate
    
    def effective_long_term_rate(self) -> float:
        """Combined effective long-term rate"""
        return self.federal_long_term_rate + self.federal_net_investment_tax + self.state_tax_rate


class AfterTaxPerformanceTracker:
    """Comprehensive after-tax performance tracking system"""
    
    def __init__(self, tax_profile: TaxProfile = None):
        self.tax_profile = tax_profile or TaxProfile()
        self.tax_lots: List[TaxLot] = []
        self.realized_gains_history = []
        self.tax_payments_history = []
        
    def add_purchase(self, ticker: str, shares: float, price: float, 
                    date: datetime) -> TaxLot:
        """Record a new purchase creating a tax lot"""
        
        lot = TaxLot(
            ticker=ticker,
            purchase_date=date,
            shares=shares,
            purchase_price=price
        )
        
        self.tax_lots.append(lot)
        
        print(f"📈 Added tax lot: {ticker} - {shares:.2f} shares @ ${price:.2f}")
        print(f"   Cost basis: ${lot.cost_basis:,.2f}")
        
        return lot
    
    def update_current_prices(self, price_dict: Dict[str, float]):
        """Update current prices for all holdings"""
        
        for lot in self.tax_lots:
            if lot.ticker in price_dict and lot.sale_date is None:
                lot.current_price = price_dict[lot.ticker]
    
    def sell_shares(self, ticker: str, shares: float, price: float, 
                   date: datetime, method: str = "FIFO") -> Dict[str, Any]:
        """
        Record a sale and calculate tax impact
        
        Args:
            ticker: Stock ticker
            shares: Number of shares to sell
            price: Sale price per share
            date: Sale date
            method: Tax lot selection method (FIFO, LIFO, HIFO, SpecificID)
            
        Returns:
            Dict with sale details and tax impact
        """
        
        # Get available lots for this ticker
        available_lots = [lot for lot in self.tax_lots 
                         if lot.ticker == ticker and lot.sale_date is None]
        
        if not available_lots:
            raise ValueError(f"No shares of {ticker} available to sell")
        
        # Sort lots based on method
        if method == "FIFO":  # First In First Out
            available_lots.sort(key=lambda x: x.purchase_date)
        elif method == "LIFO":  # Last In First Out
            available_lots.sort(key=lambda x: x.purchase_date, reverse=True)
        elif method == "HIFO":  # Highest In First Out (best for taxes)
            available_lots.sort(key=lambda x: x.purchase_price, reverse=True)
        
        # Process sale
        remaining_shares = shares
        short_term_gain = 0.0
        long_term_gain = 0.0
        total_proceeds = shares * price
        total_cost_basis = 0.0
        lots_sold = []
        
        for lot in available_lots:
            if remaining_shares <= 0:
                break
                
            # Determine shares to sell from this lot
            shares_from_lot = min(remaining_shares, lot.shares)
            remaining_shares -= shares_from_lot
            
            # Calculate gain/loss
            lot_proceeds = shares_from_lot * price
            lot_cost_basis = shares_from_lot * lot.purchase_price
            lot_gain = lot_proceeds - lot_cost_basis
            total_cost_basis += lot_cost_basis
            
            # Check holding period
            lot.sale_date = date
            lot.sale_price = price
            
            if lot.is_long_term:
                long_term_gain += lot_gain
            else:
                short_term_gain += lot_gain
            
            # Update or remove lot
            if shares_from_lot == lot.shares:
                lot.sale_date = date
                lot.sale_price = price
            else:
                # Partial sale - create new lot for remaining shares
                lot.shares -= shares_from_lot
                sold_lot = TaxLot(
                    ticker=ticker,
                    purchase_date=lot.purchase_date,
                    shares=shares_from_lot,
                    purchase_price=lot.purchase_price,
                    sale_date=date,
                    sale_price=price
                )
                lots_sold.append(sold_lot)
        
        # Calculate taxes
        short_term_tax = short_term_gain * self.tax_profile.effective_short_term_rate()
        long_term_tax = long_term_gain * self.tax_profile.effective_long_term_rate()
        total_tax = short_term_tax + long_term_tax
        
        # After-tax proceeds
        after_tax_proceeds = total_proceeds - total_tax
        
        sale_record = {
            'ticker': ticker,
            'shares': shares,
            'sale_price': price,
            'sale_date': date,
            'total_proceeds': total_proceeds,
            'cost_basis': total_cost_basis,
            'short_term_gain': short_term_gain,
            'long_term_gain': long_term_gain,
            'total_gain': short_term_gain + long_term_gain,
            'short_term_tax': short_term_tax,
            'long_term_tax': long_term_tax,
            'total_tax': total_tax,
            'after_tax_proceeds': after_tax_proceeds,
            'method': method
        }
        
        self.realized_gains_history.append(sale_record)
        
        print(f"💰 Sold {ticker}: {shares:.2f} shares @ ${price:.2f}")
        print(f"   Proceeds: ${total_proceeds:,.2f}")
        print(f"   Cost basis: ${total_cost_basis:,.2f}")
        print(f"   Short-term gain: ${short_term_gain:,.2f} (tax: ${short_term_tax:,.2f})")
        print(f"   Long-term gain: ${long_term_gain:,.2f} (tax: ${long_term_tax:,.2f})")
        print(f"   Total tax: ${total_tax:,.2f}")
        print(f"   After-tax proceeds: ${after_tax_proceeds:,.2f}")
        
        return sale_record
    
    def identify_tax_loss_harvesting_opportunities(self, 
                                                  min_loss_threshold: float = 1000.0,
                                                  wash_sale_days: int = 30) -> List[Dict]:
        """Identify opportunities for tax loss harvesting"""
        
        opportunities = []
        
        # Get current unrealized losses
        for lot in self.tax_lots:
            if lot.sale_date is None and lot.unrealized_gain < -min_loss_threshold:
                # Check for potential wash sale issues
                recent_purchases = [l for l in self.tax_lots 
                                  if l.ticker == lot.ticker 
                                  and l.purchase_date > lot.purchase_date
                                  and (datetime.now() - l.purchase_date).days < wash_sale_days]
                
                has_wash_sale_risk = len(recent_purchases) > 0
                
                opportunity = {
                    'ticker': lot.ticker,
                    'shares': lot.shares,
                    'purchase_date': lot.purchase_date,
                    'purchase_price': lot.purchase_price,
                    'current_price': lot.current_price,
                    'unrealized_loss': lot.unrealized_gain,  # Negative value
                    'holding_period_days': lot.holding_period_days,
                    'is_long_term': lot.is_long_term,
                    'potential_tax_benefit': abs(lot.unrealized_gain) * 
                        (self.tax_profile.effective_long_term_rate() if lot.is_long_term 
                         else self.tax_profile.effective_short_term_rate()),
                    'wash_sale_risk': has_wash_sale_risk
                }
                
                opportunities.append(opportunity)
        
        # Sort by tax benefit
        opportunities.sort(key=lambda x: x['potential_tax_benefit'], reverse=True)
        
        return opportunities
    
    def calculate_portfolio_tax_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive tax metrics for the portfolio"""
        
        # Separate active and sold lots
        active_lots = [lot for lot in self.tax_lots if lot.sale_date is None]
        sold_lots = [lot for lot in self.tax_lots if lot.sale_date is not None]
        
        # Unrealized gains/losses
        unrealized_short_term = sum(lot.unrealized_gain for lot in active_lots 
                                   if not lot.is_long_term)
        unrealized_long_term = sum(lot.unrealized_gain for lot in active_lots 
                                  if lot.is_long_term)
        
        # Realized gains/losses
        realized_short_term = sum(record['short_term_gain'] 
                                 for record in self.realized_gains_history)
        realized_long_term = sum(record['long_term_gain'] 
                                for record in self.realized_gains_history)
        
        # Tax paid
        total_tax_paid = sum(record['total_tax'] 
                            for record in self.realized_gains_history)
        
        # Potential tax liability
        potential_short_term_tax = unrealized_short_term * self.tax_profile.effective_short_term_rate()
        potential_long_term_tax = unrealized_long_term * self.tax_profile.effective_long_term_rate()
        
        # Tax efficiency metrics
        total_gains = realized_short_term + realized_long_term + unrealized_short_term + unrealized_long_term
        if total_gains > 0:
            tax_drag = total_tax_paid / total_gains
            tax_efficiency = 1 - tax_drag
        else:
            tax_drag = 0
            tax_efficiency = 1
        
        metrics = {
            'unrealized_gains': {
                'short_term': unrealized_short_term,
                'long_term': unrealized_long_term,
                'total': unrealized_short_term + unrealized_long_term
            },
            'realized_gains': {
                'short_term': realized_short_term,
                'long_term': realized_long_term,
                'total': realized_short_term + realized_long_term
            },
            'taxes': {
                'paid': total_tax_paid,
                'potential_short_term': potential_short_term_tax,
                'potential_long_term': potential_long_term_tax,
                'potential_total': potential_short_term_tax + potential_long_term_tax
            },
            'efficiency': {
                'tax_drag': tax_drag,
                'tax_efficiency': tax_efficiency,
                'after_tax_return_impact': -tax_drag if total_gains > 0 else 0
            },
            'portfolio_composition': {
                'active_lots': len(active_lots),
                'short_term_lots': len([l for l in active_lots if not l.is_long_term]),
                'long_term_lots': len([l for l in active_lots if l.is_long_term])
            }
        }
        
        return metrics
    
    def simulate_rebalance_tax_impact(self, current_portfolio: List[Dict],
                                     target_portfolio: List[Dict],
                                     current_prices: Dict[str, float]) -> Dict[str, Any]:
        """Simulate tax impact of portfolio rebalancing"""
        
        # Update current prices
        self.update_current_prices(current_prices)
        
        # Identify sells needed
        current_tickers = {pos['ticker'] for pos in current_portfolio}
        target_tickers = {pos['ticker'] for pos in target_portfolio}
        
        # Stocks to sell completely
        stocks_to_sell = current_tickers - target_tickers
        
        # Stocks to rebalance (partial sells/buys)
        stocks_to_rebalance = current_tickers & target_tickers
        
        estimated_tax = 0.0
        estimated_proceeds = 0.0
        trades = []
        
        # Simulate complete sells
        for ticker in stocks_to_sell:
            lots = [lot for lot in self.tax_lots 
                   if lot.ticker == ticker and lot.sale_date is None]
            
            for lot in lots:
                gain = lot.unrealized_gain
                if lot.is_long_term:
                    tax = gain * self.tax_profile.effective_long_term_rate()
                else:
                    tax = gain * self.tax_profile.effective_short_term_rate()
                
                estimated_tax += tax
                estimated_proceeds += lot.current_value
                
                trades.append({
                    'ticker': ticker,
                    'action': 'SELL',
                    'shares': lot.shares,
                    'estimated_gain': gain,
                    'estimated_tax': tax,
                    'is_long_term': lot.is_long_term
                })
        
        return {
            'estimated_tax': estimated_tax,
            'estimated_proceeds': estimated_proceeds,
            'after_tax_proceeds': estimated_proceeds - estimated_tax,
            'number_of_trades': len(trades),
            'trades': trades,
            'tax_efficiency_score': 1 - (estimated_tax / estimated_proceeds) if estimated_proceeds > 0 else 1
        }
    
    def generate_tax_report(self) -> str:
        """Generate comprehensive tax report"""
        
        metrics = self.calculate_portfolio_tax_metrics()
        
        report = []
        report.append("📊 TAX ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Tax Profile
        report.append("📋 Tax Profile:")
        report.append(f"   Federal ST Rate: {self.tax_profile.federal_short_term_rate:.1%}")
        report.append(f"   Federal LT Rate: {self.tax_profile.federal_long_term_rate:.1%}")
        report.append(f"   State Tax Rate: {self.tax_profile.state_tax_rate:.1%}")
        report.append(f"   Effective ST Rate: {self.tax_profile.effective_short_term_rate():.1%}")
        report.append(f"   Effective LT Rate: {self.tax_profile.effective_long_term_rate():.1%}")
        report.append("")
        
        # Unrealized Gains
        report.append("💰 Unrealized Gains/Losses:")
        report.append(f"   Short-term: ${metrics['unrealized_gains']['short_term']:,.2f}")
        report.append(f"   Long-term: ${metrics['unrealized_gains']['long_term']:,.2f}")
        report.append(f"   Total: ${metrics['unrealized_gains']['total']:,.2f}")
        report.append("")
        
        # Realized Gains
        report.append("💵 Realized Gains/Losses:")
        report.append(f"   Short-term: ${metrics['realized_gains']['short_term']:,.2f}")
        report.append(f"   Long-term: ${metrics['realized_gains']['long_term']:,.2f}")
        report.append(f"   Total: ${metrics['realized_gains']['total']:,.2f}")
        report.append("")
        
        # Tax Impact
        report.append("🏦 Tax Impact:")
        report.append(f"   Taxes Paid: ${metrics['taxes']['paid']:,.2f}")
        report.append(f"   Potential Tax (unrealized):")
        report.append(f"      Short-term: ${metrics['taxes']['potential_short_term']:,.2f}")
        report.append(f"      Long-term: ${metrics['taxes']['potential_long_term']:,.2f}")
        report.append(f"      Total: ${metrics['taxes']['potential_total']:,.2f}")
        report.append("")
        
        # Efficiency Metrics
        report.append("📊 Tax Efficiency:")
        report.append(f"   Tax Drag: {metrics['efficiency']['tax_drag']:.2%}")
        report.append(f"   Tax Efficiency: {metrics['efficiency']['tax_efficiency']:.2%}")
        report.append(f"   After-tax Return Impact: {metrics['efficiency']['after_tax_return_impact']:.2%}")
        report.append("")
        
        # Portfolio Composition
        report.append("📈 Portfolio Tax Composition:")
        report.append(f"   Active Tax Lots: {metrics['portfolio_composition']['active_lots']}")
        report.append(f"   Short-term Lots: {metrics['portfolio_composition']['short_term_lots']}")
        report.append(f"   Long-term Lots: {metrics['portfolio_composition']['long_term_lots']}")
        
        # Tax Loss Harvesting Opportunities
        tlh_opportunities = self.identify_tax_loss_harvesting_opportunities()
        if tlh_opportunities:
            report.append("")
            report.append("🎯 Tax Loss Harvesting Opportunities:")
            for i, opp in enumerate(tlh_opportunities[:3]):  # Top 3
                report.append(f"   {i+1}. {opp['ticker']}: ${opp['unrealized_loss']:,.2f} loss")
                report.append(f"      Tax benefit: ${opp['potential_tax_benefit']:,.2f}")
                if opp['wash_sale_risk']:
                    report.append(f"      ⚠️  Wash sale risk")
        
        return "\n".join(report)


def test_after_tax_tracking():
    """Test the after-tax performance tracking system"""
    
    print("🧪 Testing After-Tax Performance Tracking")
    print("=" * 60)
    
    # Create tax profile (California resident example)
    tax_profile = TaxProfile(
        federal_short_term_rate=0.37,
        federal_long_term_rate=0.20,
        federal_net_investment_tax=0.038,
        state_tax_rate=0.133  # California top rate
    )
    
    # Initialize tracker
    tracker = AfterTaxPerformanceTracker(tax_profile)
    
    # Simulate some transactions
    print("\n📈 Simulating portfolio transactions...")
    
    # Purchase 1: AAPL (will be long-term)
    purchase_date_1 = datetime.now() - timedelta(days=400)
    tracker.add_purchase("AAPL", 100, 150.00, purchase_date_1)
    
    # Purchase 2: MSFT (will be short-term)
    purchase_date_2 = datetime.now() - timedelta(days=200)
    tracker.add_purchase("MSFT", 50, 300.00, purchase_date_2)
    
    # Purchase 3: GOOGL (will be long-term)
    purchase_date_3 = datetime.now() - timedelta(days=500)
    tracker.add_purchase("GOOGL", 30, 2500.00, purchase_date_3)
    
    # Update current prices
    current_prices = {
        "AAPL": 190.00,   # Gain
        "MSFT": 350.00,   # Gain
        "GOOGL": 2300.00  # Loss (tax loss harvesting opportunity)
    }
    tracker.update_current_prices(current_prices)
    
    # Simulate a sale (AAPL - long term gain)
    print(f"\n💰 Simulating sale...")
    sale_result = tracker.sell_shares("AAPL", 50, 190.00, datetime.now(), method="FIFO")
    
    # Check tax loss harvesting opportunities
    print(f"\n🎯 Identifying tax loss harvesting opportunities...")
    tlh_opportunities = tracker.identify_tax_loss_harvesting_opportunities(min_loss_threshold=1000)
    
    if tlh_opportunities:
        for opp in tlh_opportunities:
            print(f"   {opp['ticker']}: ${opp['unrealized_loss']:,.2f} loss")
            print(f"   Potential tax benefit: ${opp['potential_tax_benefit']:,.2f}")
    
    # Calculate portfolio metrics
    print(f"\n📊 Calculating portfolio tax metrics...")
    metrics = tracker.calculate_portfolio_tax_metrics()
    
    # Generate tax report
    print(f"\n📋 Generating tax report...")
    report = tracker.generate_tax_report()
    print(report)
    
    # Simulate rebalancing tax impact
    print(f"\n🔄 Simulating rebalance tax impact...")
    current_portfolio = [
        {'ticker': 'AAPL', 'shares': 50},
        {'ticker': 'MSFT', 'shares': 50},
        {'ticker': 'GOOGL', 'shares': 30}
    ]
    
    target_portfolio = [
        {'ticker': 'AAPL', 'shares': 30},
        {'ticker': 'NVDA', 'shares': 20},
        {'ticker': 'AMZN', 'shares': 10}
    ]
    
    rebalance_impact = tracker.simulate_rebalance_tax_impact(
        current_portfolio, target_portfolio, current_prices
    )
    
    print(f"   Estimated tax: ${rebalance_impact['estimated_tax']:,.2f}")
    print(f"   After-tax proceeds: ${rebalance_impact['after_tax_proceeds']:,.2f}")
    print(f"   Tax efficiency score: {rebalance_impact['tax_efficiency_score']:.2%}")
    
    return tracker


if __name__ == "__main__":
    test_after_tax_tracking()