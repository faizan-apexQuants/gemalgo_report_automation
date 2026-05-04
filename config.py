# ── API ──────────────────────────────────────────────
API_URL = "https://api.gemalgo.com/api/trade/multiple_account/all"
API_TIMEOUT = 30   # seconds

# Add auth headers here if the API requires a token:
# API_HEADERS = {"Authorization": "Bearer YOUR_TOKEN_HERE"}
API_HEADERS = {}   # currently no auth needed

# ── EMAIL ─────────────────────────────────────────────
EMAIL_SENDER   = "shaikhfaizan1512@gmail.com"
EMAIL_PASSWORD = "tkqo gibf afvi ujkh"  # Gmail App Password (16 chars)
EMAIL_TO       = ["faizan@apexquants.com"]  # list of recipients
SMTP_HOST      = "smtp.gmail.com"
SMTP_PORT      = 587

# ── OUTPUT ────────────────────────────────────────────
OUTPUT_DIR = "output"