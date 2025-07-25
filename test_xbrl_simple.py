#!/usr/bin/env python3
"""
Simple test to understand XBRL structure in edgartools
"""

import edgar
import pandas as pd

def test_xbrl_extraction():
    """Test basic XBRL data extraction"""
    
    edgar.set_identity('Modern Magic Formula Research contact@example.com')
    
    # Get Apple's latest 10-K
    company = edgar.Company('AAPL')
    filings = company.get_filings(form='10-K')
    latest_filing = filings[0]
    
    print(f"Testing XBRL extraction for {company.name}")
    print(f"Filing date: {latest_filing.filing_date}")
    
    # Get XBRL data
    xbrl = latest_filing.xbrl()
    
    # Explore the facts directly
    print(f"\nXBRL facts count: {len(xbrl.facts)}")
    print(f"Facts type: {type(xbrl.facts)}")
    
    # Look for common financial concepts
    concepts_to_find = [
        'Revenues', 'Revenue', 'NetSales',
        'OperatingIncomeLoss', 'OperatingIncome',
        'NetIncomeLoss', 'NetIncome',
        'Assets', 'AssetsCurrent',
        'CashAndCashEquivalentsAtCarryingValue'
    ]
    
    found_facts = {}
    
    # Try different ways to access facts
    try:
        facts_list = list(xbrl.facts)
        print(f"Facts converted to list: {len(facts_list)}")
        
        for i, fact in enumerate(facts_list[:50]):  # First 50 for testing
            concept = fact.concept
            if any(search_term in concept for search_term in concepts_to_find):
                # Get the most recent value
                if hasattr(fact, 'value') and fact.value is not None:
                    period_key = str(fact.period) if hasattr(fact, 'period') else 'unknown'
                    
                    if concept not in found_facts:
                        found_facts[concept] = []
                        
                    found_facts[concept].append({
                        'value': fact.value,
                        'period': period_key,
                        'unit': fact.unit if hasattr(fact, 'unit') else None
                    })
                    
    except Exception as e:
        print(f"Error accessing facts: {e}")
        
        # Try alternative approach
        print("Trying alternative fact access...")
        try:
            # Maybe we can search for specific concepts
            for concept in concepts_to_find:
                matching_facts = xbrl.facts.filter(concept=concept)
                if matching_facts:
                    print(f"Found facts for {concept}: {len(matching_facts)}")
                    
        except Exception as e2:
            print(f"Alternative approach also failed: {e2}")
    
    print(f"\n📊 Found {len(found_facts)} relevant financial concepts:")
    
    for concept, values in found_facts.items():
        print(f"\n{concept}:")
        # Show the most recent few values
        for i, item in enumerate(values[:3]):
            print(f"  {item['period']}: {item['value']} {item['unit']}")
            
    return found_facts

if __name__ == "__main__":
    facts = test_xbrl_extraction()