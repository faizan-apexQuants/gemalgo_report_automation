import pathlib
from api_client     import fetch_accounts, build_context
from pdf_generator  import generate_pdfs
from email_sender   import send_report

def run():
    print("="*50)
    print("Gemalgo Automated Report Pipeline")
    print("="*50)

    # 1. Fetch data from Gemalgo API
    print("\n[1/4] Fetching accounts from API...")
    accounts = fetch_accounts()

    if not accounts:
        print("No active accounts found. Exiting.")
        return

    # 2. Build template context for each client
    print("\n[2/4] Mapping API data to dashboard...")
    contexts = [build_context(acc) for acc in accounts]

    # 3. Generate PDFs
    print("\n[3/4] Rendering dashboards and exporting PDFs...")
    bundle_path = generate_pdfs(contexts)

    # 4. Send email
    print("\n[4/4] Sending email...")
    send_report(bundle_path, len(contexts))

    print(f"\n✅ Done! Report: {bundle_path}")

if __name__ == "__main__":
    run()