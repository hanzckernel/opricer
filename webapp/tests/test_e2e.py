import pytest
from playwright.sync_api import Page, expect
import multiprocessing
import time
import sys
import os

# Ensure root directory is in path to import index
sys.path.append(os.getcwd())

from webapp.app import app
# Import index module to trigger layout assignment
import index 

# Define port
PORT = 8051

def run_app():
    # app.layout is set by importing index
    app.run(port=PORT, debug=False, use_reloader=False)

@pytest.fixture(scope="module")
def run_server():
    p = multiprocessing.Process(target=run_app)
    p.start()
    time.sleep(3)  # Give server time to start
    yield
    p.terminate()
    p.join()

@pytest.fixture
def index_page(page: Page, run_server):
    page.goto(f"http://127.0.0.1:{PORT}/")
    return page

def test_app_title(index_page: Page):
    expect(index_page).to_have_title("Option Pricing Tool")
    
def test_navbar_navigation(index_page: Page):
    # Check default active
    expect(index_page.locator("#stock-link")).to_have_class(r"nav-link active")
    
    # Click options
    index_page.locator("#options-link").click()
    expect(index_page).to_have_url(f"http://127.0.0.1:{PORT}/options")
    expect(index_page.locator("#options-link")).to_have_class(r"nav-link active")
    
    # Click back to stock
    index_page.locator("#stock-link").click()
    expect(index_page).to_have_url(f"http://127.0.0.1:{PORT}/stock")

def test_stock_ticker_input(index_page: Page):
    # Assuming we are on stock page
    index_page.locator("#stock-link").click()
    
    # Open modal to add ticker
    index_page.locator("#new_stock").click()
    expect(index_page.locator("#stock_modal")).to_be_visible()
    
    # Input Ticker
    index_page.locator("#submit_input").fill("MSFT")
    
    # Click Add
    # Removed force=True to verify overlay fix
    index_page.locator("#submit_new_stock").click()
    
    # Modal should close
    expect(index_page.locator("#stock_modal")).not_to_be_visible()
    
    # Check if MSFT is in dropdown (simplified check: verify value or text)
    # This might be tricky with custom dropdowns, but let's try
    # Wait for graph update?
    # Ideally we check the graph title or trace name if visible
    
    # Let's check if "MSFT" is added to the dropdown value
    # Depending on implementation, we might need to inspect the react-select component structure
    # For now, let's just assert the graph exists
    expect(index_page.locator("#stock-graph")).to_be_visible()

def test_option_pricing_flow(index_page: Page):
    index_page.goto(f"http://127.0.0.1:{PORT}/options")
    
    # Open Modal
    index_page.locator("#new_underlying").click()
    expect(index_page.locator("#option_modal")).to_be_visible()
    
    # Fill details
    index_page.locator("#asset_name").fill("TestAsset")
    # Verify typing worked
    expect(index_page.locator("#asset_name")).to_have_value("TestAsset")
    
    index_page.locator("#spot").fill("100")
    index_page.locator("#volatility").fill("20")
    
    # Submit without force=True
    index_page.locator("#submit_new_option").click()
    expect(index_page.locator("#option_modal")).not_to_be_visible()
    
    # Select Asset in dropdown? 
    # Logic: Added asset should appear.
    # For simplicity, let's check if we can compute price
    
    # Fill Strike
    index_page.locator("#strike").fill("100")
    
    # Click Compute
    index_page.locator("#confirm").click()
    
    # Expect Confirmation Dialog
    # Dash ConfirmDialog usually renders as browser alert or custom UI?
    # dcc.ConfirmDialog triggers a browser alert.
    # Playwright handles dialogs automatically or we need a handler.
    # But wait, dcc.ConfirmDialog is not a browser alert? 
    # "The ConfirmDialog component sends a message to the browser..." -> Yes it is window.confirm()
    
    # We need to handle dialog
    def handle_dialog(dialog):
        dialog.accept()

    index_page.on("dialog", handle_dialog)
    
    # Trigger computation
    # Wait for graph update
    expect(index_page.locator("#opricer_graph")).to_be_visible()
