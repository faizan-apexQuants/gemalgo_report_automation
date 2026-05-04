import asyncio, os, pathlib, time, gc
from datetime import date
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
import pikepdf
from config import OUTPUT_DIR

env = Environment(loader=FileSystemLoader("templates"))
template = env.get_template("dashboard.html")

async def _html_to_pdf(html_str: str, pdf_path: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html_str, wait_until="domcontentloaded")
        await page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            margin={"top":"10mm","bottom":"10mm",
                    "left":"12mm","right":"12mm"}
        )
        await browser.close()

def _safe_delete(path: str, retries: int = 5, delay: float = 0.5):
    """
    Delete a file with retries — needed on Windows where
    the OS holds file handles briefly after closing.
    """
    for attempt in range(retries):
        try:
            os.remove(path)
            return
        except PermissionError:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print(f"  ⚠ Could not delete {path} — skipping")

def generate_pdfs(contexts: list[dict]) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = date.today().strftime("%Y-%m-%d")
    pdf_files = []

    # ── Step 1: Render each client dashboard to its own PDF ──
    for ctx in contexts:
        ctx["report_date"] = date.today().strftime("%d %b %Y")
        html = template.render(**ctx)
        safe_name = str(ctx["acc_no"]).replace("/", "-")
        pdf_path = f"{OUTPUT_DIR}/{safe_name}.pdf"
        asyncio.run(_html_to_pdf(html, pdf_path))
        pdf_files.append(pdf_path)
        print(f"  ✓ {ctx['name']} → {pdf_path}")

    # ── Step 2: Merge into one bundle ──────────────────────
    bundle = f"{OUTPUT_DIR}/Gemalgo_Report_{today}.pdf"
    merged = pikepdf.Pdf.new()
    sources = []  # keep refs so we can close them explicitly

    for f in pdf_files:
        src = pikepdf.open(f)
        sources.append(src)
        merged.pages.extend(src.pages)

    # Try to save, append suffix if locked
    base_bundle = bundle
    suffix = 1
    while True:
        try:
            merged.save(bundle)
            break
        except PermissionError:
            bundle = base_bundle.replace(".pdf", f"_{suffix}.pdf")
            suffix += 1

    print(f"✓ Merged PDF → {bundle}")

    # ── Step 3: Close ALL handles before deleting ──────────
    merged.close()
    for src in sources:
        src.close()
    sources.clear()
    gc.collect()          # force Python to release any lingering refs
    time.sleep(0.3)      # brief pause — Windows needs this

    # ── Step 4: Safe delete with retry ─────────────────────
    for f in pdf_files:
        _safe_delete(f)

    return bundle