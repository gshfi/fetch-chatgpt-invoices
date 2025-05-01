# 🧾 ChatGPT Invoice Downloader (Playwright, Headless)

This script automatically downloads **all your OpenAI ChatGPT invoices** via the ChatGPT web interface and Stripe, using Playwright in headless mode.

Invoices are saved to:  
**invoices/openai/**

✅ Downloads all available invoices  
✅ Skips already-downloaded files  
✅ Fully headless (no browser window)  
✅ Uses your own session token, not OpenAI API key  

---

## ⚙️ Requirements

- Python 3.8+
- [Playwright](https://playwright.dev/python) (for Chromium automation)

Install the required packages:

```bash
pip install playwright
playwright install
```

## 🔑 How to Get Your Access Token

1. Log in to https://chat.openai.com
2. Open Developer Console (press F12, then go to the Console tab)
3. Run the following command:

```
window.__reactRouterContext?.state?.loaderData?.root?.clientBootstrap?.session?.accessToken
```
4. Copy the access token string it returns
5. Set the environment variable:

`For Windows PowerShell:`
```
$env:CHAT_GPT_ACCESS_TOKEN="your-access-token"
```
`For macOS/Linux:`
```
export CHAT_GPT_ACCESS_TOKEN="your-access-token"
```

## ▶️ How to Run the Script

Once your access token is set, simply run:
```
python get_invoices_openapi.py
```
The script will:

- Verify your access token
- Get the Stripe invoice portal URL
- Collect all invoice download links
- Download each PDF invoice and save it to invoices/openai/
- Skip invoices that are already downloaded

## 📁 Output

Invoices are saved with their original Stripe filenames, for example:
```
invoices/openai/invoice-2025-05-01.pdf
```
--- Already existing files will not be downloaded again.
## ⚠️ Notes

* This script does not use the official OpenAI API.
* Tokens expire quickly. If you get a 403 Forbidden error, retrieve a new token via browser console.
* No personal data is stored — only publicly visible invoice PDFs are downloaded using your session.
