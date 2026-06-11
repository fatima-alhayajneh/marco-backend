Task 8: Quick Guide

    Update: Pull the latest changes using git pull origin main.

    Run: Start the server with uvicorn app.main:app --reload.

    Test: Access the API interface at http://127.0.0.1:8000/docs.

   ### Task 9: Core Logic Updates
* **Scarcity Pricing:** +50% markup if Stock = 1.
* **VAT:** 16% tax applied on the final price.
* **Loyalty Points:** Points = Total Order Value.
* **Inventory:** Automatic stock decrement per order.

### Test Case Example:
* **Base Price:** 100 JOD
* **After Markup (1.5x):** 150 JOD
* **Final with VAT (1.16x):** 174 JOD
