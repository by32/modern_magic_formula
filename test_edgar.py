#!/usr/bin/env python3
"""
Test edgartools integration with proper SEC compliance
"""

import os
import edgar
import time
from edgar import Company, set_identity

def test_edgar_connection():
    """Test edgar connection with proper user agent"""
    
    # Set proper user agent for SEC compliance
    user_agent = "Modern Magic Formula Research contact@example.com"
    os.environ['SEC_EDGAR_USER_AGENT'] = user_agent
    
    # Set identity for edgartools
    set_identity(user_agent)
    
    print(f"Testing edgartools with user agent: {user_agent}")
    
    # Test with a delay to respect rate limits
    time.sleep(1)
    
    try:
        # Try direct CIK lookup for Apple (0000320193)
        print("Attempting direct CIK lookup...")
        company = Company('0000320193')
        print(f"✅ Success! Company: {company.name}")
        print(f"   CIK: {company.cik}")
        
        # Try getting filings
        print("Getting recent filings...")
        filings = company.get_filings(form='10-K').latest(1)
        if filings:
            filing = filings[0]
            print(f"   Latest 10-K: {filing.date}")
            print(f"   Filing URL: {filing.filing_details_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_alternative_approach():
    """Test alternative approach using requests directly"""
    import requests
    import time
    
    headers = {
        'User-Agent': 'Modern Magic Formula Research contact@example.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'data.sec.gov'
    }
    
    print("\nTesting direct SEC API access...")
    
    try:
        # Test basic connection to SEC API
        url = "https://data.sec.gov/submissions/CIK0000320193.json"
        time.sleep(1)  # Respect rate limits
        
        response = requests.get(url, headers=headers)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Direct API Success!")
            print(f"   Company: {data.get('name', 'N/A')}")
            print(f"   SIC: {data.get('sic', 'N/A')}")
            return True
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Direct API Error: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Edgar Tools Integration ===\n")
    
    # Test edgartools library
    edgar_success = test_edgar_connection()
    
    # Test direct API approach
    direct_success = test_alternative_approach()
    
    print("\n=== Results ===")
    print(f"EdgarTools Library: {'✅ Working' if edgar_success else '❌ Failed'}")
    print(f"Direct API Access: {'✅ Working' if direct_success else '❌ Failed'}")
    
    if edgar_success:
        print("\n✅ Ready to implement point-in-time fundamentals with edgartools!")
    elif direct_success:
        print("\n🔄 Can implement using direct SEC API calls")
    else:
        print("\n⚠️  Need to investigate SEC access requirements further")