#!/usr/bin/env python3
"""
Check Streamlit app with Playwright
Comprehensive interaction and analysis to diagnose deployment issues
"""

from playwright.sync_api import sync_playwright
import os
import time

def check_streamlit_app():
    """Check the Streamlit app with comprehensive analysis"""
    
    print("🌐 Launching Playwright for Streamlit app analysis...")
    
    with sync_playwright() as p:
        # Launch browser with extended timeout
        browser = p.chromium.launch(headless=False, slow_mo=1000)  # Visible browser for debugging
        
        try:
            # Create new page with extended timeout
            page = browser.new_page()
            page.set_default_timeout(30000)  # 30 second timeout
            
            # Set viewport size
            page.set_viewport_size({"width": 1920, "height": 1080})
            
            print("📱 Navigating to Streamlit app...")
            
            # Navigate to Streamlit app with extended wait
            response = page.goto("https://modernmagicformula.streamlit.app", wait_until="domcontentloaded")
            
            if response:
                print(f"📊 Response status: {response.status}")
                print(f"🔗 Final URL: {page.url}")
            
            # Wait for Streamlit to initialize
            print("⏳ Waiting for Streamlit to load...")
            page.wait_for_timeout(10000)  # 10 seconds for Streamlit to load
            
            # Take initial screenshot
            print("📸 Taking initial screenshot...")
            page.screenshot(path="streamlit_initial.png", full_page=True)
            
            # Look for Streamlit-specific loading indicators
            try:
                # Wait for Streamlit spinner to disappear (if present)
                page.wait_for_selector(".stSpinner", state="detached", timeout=15000)
                print("✅ Streamlit spinner finished")
            except:
                print("ℹ️ No Streamlit spinner detected")
            
            # Check for Streamlit main content area
            try:
                main_content = page.wait_for_selector(".main .block-container", timeout=10000)
                print("✅ Streamlit main content area found")
            except:
                print("❌ Streamlit main content area not found")
            
            # Wait additional time for dynamic content
            print("⏳ Waiting for dynamic content to load...")
            page.wait_for_timeout(5000)
            
            # Take final screenshot after loading
            print("📸 Taking final screenshot after loading...")
            page.screenshot(path="streamlit_loaded.png", full_page=True)
            
            # Get page content
            page_content = page.content()
            
            # Get visible text content
            try:
                body_text = page.locator("body").text_content()
                visible_text_length = len(body_text.strip())
            except:
                body_text = ""
                visible_text_length = 0
            
            print(f"\n📊 Detailed Page Analysis:")
            print(f"   - HTML content length: {len(page_content)} characters")
            print(f"   - Visible text length: {visible_text_length} characters")
            print(f"   - Page title: {page.title()}")
            
            # Check for specific Streamlit elements
            streamlit_elements = {
                "Streamlit container": ".main .block-container",
                "Streamlit sidebar": ".sidebar .sidebar-content", 
                "Streamlit header": "h1, h2, h3",
                "Streamlit buttons": ".stButton",
                "Streamlit selectbox": ".stSelectbox",
                "Streamlit dataframe": ".stDataFrame"
            }
            
            print("\n🔍 Streamlit Element Detection:")
            for name, selector in streamlit_elements.items():
                try:
                    elements = page.locator(selector)
                    count = elements.count()
                    if count > 0:
                        print(f"   ✅ {name}: {count} found")
                    else:
                        print(f"   ❌ {name}: not found")
                except:
                    print(f"   ❌ {name}: error checking")
            
            # Check for app-specific content
            print("\n🎯 App Content Analysis:")
            content_checks = {
                "Modern Magic Formula": "Modern Magic Formula" in body_text,
                "DIY Stock Picks": "DIY Stock Picks" in body_text or "DIY" in body_text,
                "Professional Interface": "Professional" in body_text,
                "Stock data table": "Stock" in body_text and ("Ticker" in body_text or "Symbol" in body_text),
                "Performance metrics": "Return" in body_text or "Performance" in body_text,
                "Loading message": "Loading" in body_text or "Please wait" in body_text,
                "Error messages": "error" in body_text.lower() or "exception" in body_text.lower()
            }
            
            for check, result in content_checks.items():
                status = "✅" if result else "❌"
                print(f"   {status} {check}")
            
            # Look for navigation elements
            print("\n🧭 Navigation Analysis:")
            nav_elements = page.locator("a, button").all()
            if nav_elements:
                print(f"   - Found {len(nav_elements)} interactive elements")
                for i, element in enumerate(nav_elements[:5]):  # First 5 elements
                    try:
                        text = element.text_content()
                        if text and text.strip():
                            print(f"     • {text.strip()}")
                    except:
                        pass
            
            # Check for specific old vs new interface indicators
            print("\n🔄 Version Detection:")
            old_indicators = ["deprecated", "old version", "legacy"]
            new_indicators = ["DIY Stock Picks", "individual investor", "Magic Formula rankings"]
            
            old_found = any(indicator.lower() in body_text.lower() for indicator in old_indicators)
            new_found = any(indicator in body_text for indicator in new_indicators)
            
            if new_found:
                print("   ✅ New DIY interface detected")
            elif old_found:
                print("   ⚠️ Old interface detected")
            else:
                print("   ❓ Unable to determine interface version")
            
            # Save detailed analysis
            with open("streamlit_analysis.txt", "w") as f:
                f.write(f"Streamlit App Analysis Report\n")
                f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"URL: {page.url}\n")
                f.write(f"Response Status: {response.status if response else 'Unknown'}\n")
                f.write(f"Page Title: {page.title()}\n")
                f.write(f"HTML Length: {len(page_content)}\n")
                f.write(f"Visible Text Length: {visible_text_length}\n\n")
                f.write("Visible Text Content:\n")
                f.write("=" * 50 + "\n")
                f.write(body_text)
                
            with open("streamlit_html.html", "w") as f:
                f.write(page_content)
                
            print(f"\n📄 Analysis saved to:")
            print(f"   - streamlit_analysis.txt (readable report)")
            print(f"   - streamlit_html.html (full HTML)")
            print(f"   - streamlit_initial.png (initial state)")
            print(f"   - streamlit_loaded.png (final state)")
            
        except Exception as e:
            print(f"❌ Error during Streamlit analysis: {e}")
            # Take error screenshot
            try:
                page.screenshot(path="streamlit_error.png", full_page=True)
                print("📸 Error screenshot saved to: streamlit_error.png")
            except:
                pass
            
        finally:
            browser.close()

if __name__ == "__main__":
    check_streamlit_app()