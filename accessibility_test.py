import pytest
from playwright.sync_api import sync_playwright
import time
import json
from datetime import datetime
import os

def test_streamlit_accessibility():
    """Test the accessibility of the Streamlit application."""
    with sync_playwright() as p:
        # Launch the browser
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Navigate to the Streamlit app
            page.goto('http://localhost:8501')
            
            # Wait for the page to load
            page.wait_for_load_state('networkidle')
            time.sleep(5)  # Additional wait for dynamic content
            
            # Run accessibility scan
            results = page.evaluate("""() => {
                return new Promise(resolve => {
                    const script = document.createElement('script');
                    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.0/axe.min.js';
                    script.onload = () => {
                        axe.run().then(results => resolve(results));
                    };
                    document.head.appendChild(script);
                });
            }""")
            
            # Create a timestamp for the report filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save the results to a JSON file
            with open(f'accessibility_report_{timestamp}.json', 'w') as f:
                json.dump(results, f, indent=2)
            
            # Process and print the results
            violations = results.get('violations', [])
            
            if violations:
                print(f"\nFound {len(violations)} accessibility violations:")
                for violation in violations:
                    print(f"\nRule violated: {violation['id']}")
                    print(f"Impact: {violation['impact']}")
                    print(f"Description: {violation['description']}")
                    print(f"Help: {violation['help']}")
                    print(f"Help URL: {violation['helpUrl']}")
                    print("\nElements affected:")
                    for node in violation['nodes']:
                        print(f"- {node['html']}")
                        print(f"  Fix: {node['failureSummary']}")
            else:
                print("\nNo accessibility violations found!")
                
            # Assert no violations were found
            assert len(violations) == 0, f"Found {len(violations)} accessibility violations"
            
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 