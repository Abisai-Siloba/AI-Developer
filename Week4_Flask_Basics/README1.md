I would charge a hardware shop owner KES 15,000 for this tool.

## How to use

1. Open a terminal in the `Week4` folder.
2. Install Flask with `python -m pip install -r requirements.txt`.
3. Start the app with `python hardware_credit_app.py`.
4. Open `http://127.0.0.1:5000` in a browser.
5. Enter a customer's name and select **Search** to see their balance.

You can also look up a balance directly through the API. For example, visit
`http://127.0.0.1:5000/api/balance?customer=Amina%20Wanjiku`. The API returns
the customer's balance as JSON. The sample customer names and balances are
hardcoded in the app.