import requests
from collections import defaultdict
from datetime import datetime
from config import API_URL, API_HEADERS, API_TIMEOUT

def fetch_accounts() -> list[dict]:
    """
    Fetch all client accounts from Gemalgo API.
    Returns list of account dicts, skipping nulls.
    """
    try:
        resp = requests.get(API_URL, headers=API_HEADERS, timeout=API_TIMEOUT)
        resp.raise_for_status()   # raises on 4xx / 5xx
        payload = resp.json()

        if not payload.get("status"):
            raise ValueError("API returned status: false")

        all_accounts = payload["data"]

        # Filter out accounts with no balance data (incomplete records)
        active = [
            acc for acc in all_accounts
            if acc.get("acc_balance") is not None
            and acc.get("acc_is_deleted") == False
            and acc.get("acc_is_active") == True
        ]
        print(f"✓ Fetched {len(active)} active accounts")
        return active

    except requests.Timeout:
        raise RuntimeError("API request timed out")
    except requests.RequestException as e:
        raise RuntimeError(f"API error: {e}")

def fetch_trade_history(acc_no: str) -> list[dict]:
    """Fetch trade history for a given account number."""
    url = f"https://api.gemalgo.com/api/trade/history/{acc_no}"
    try:
        resp = requests.get(url, headers=API_HEADERS, timeout=API_TIMEOUT)
        if resp.status_code == 200:
            payload = resp.json()
            if payload.get("status") and payload.get("data"):
                return payload["data"]
        return []
    except Exception as e:
        print(f"  ⚠ Failed to fetch history for {acc_no}: {e}")
        return []

def safe(acc: dict, key: str, default="—"):
    """Return field value or a safe default if null/missing."""
    val = acc.get(key)
    return val if val is not None else default

def fmt_currency(val, default="—") -> str:
    if val is None: return default
    sign = "+" if float(val) > 0 else ""
    return f"{sign}${float(val):,.2f}"

def fmt_pct(val, default="—") -> str:
    if val is None: return default
    return f"{float(val):.2f}%"

def build_context(acc: dict) -> dict:
    """Map raw API fields → template-friendly dict and generate chart data."""
    acc_no = safe(acc, "acc_no")
    
    # ── Fetch and Process Trade History for Charts ──
    history = fetch_trade_history(acc_no) if acc_no != "—" else []
    
    # Sort history by close time (oldest to newest)
    history = sorted(
        [t for t in history if t.get("mth_order_close_time_dtf")], 
        key=lambda x: x["mth_order_close_time_dtf"]
    )

    dates = []
    cumulative_profit = []
    daily_pnl_labels = []
    daily_pnl_data = []
    buy_counts = []
    sell_counts = []
    
    if history:
        current_cumulative = 0
        daily_profits = defaultdict(float)
        daily_buys = defaultdict(int)
        daily_sells = defaultdict(int)

        for trade in history:
            # Cumulative profit data
            profit = float(trade.get("mth_order_profit", 0))
            current_cumulative += profit
            dt_str = trade["mth_order_close_time_dtf"]
            # Extract date for daily aggregation
            date_only = dt_str.split('T')[0]
            # Format nicely for the equity curve label (e.g. '18 Dec')
            try:
                dt_obj = datetime.strptime(date_only, "%Y-%m-%d")
                short_date = dt_obj.strftime("%d %b")
            except:
                short_date = date_only

            dates.append(short_date)
            cumulative_profit.append(round(current_cumulative, 2))
            
            # Daily aggregations
            daily_profits[short_date] += profit
            if trade.get("mth_order_type") == 0:
                daily_buys[short_date] += 1
            elif trade.get("mth_order_type") == 1:
                daily_sells[short_date] += 1
                
        # To avoid overcrowding the bar charts, take the last 20 days
        sorted_daily_keys = list(daily_profits.keys())[-20:]
        for k in sorted_daily_keys:
            daily_pnl_labels.append(k)
            daily_pnl_data.append(round(daily_profits[k], 2))
            buy_counts.append(daily_buys[k])
            sell_counts.append(daily_sells[k])

    chart_data = {
        "dates": dates,
        "cumulative_profit": cumulative_profit,
        "daily_labels": daily_pnl_labels,
        "daily_pnl": daily_pnl_data,
        "buy_counts": buy_counts,
        "sell_counts": sell_counts
    }
    
    # KPIs
    balance = float(acc.get("acc_balance") or 0)
    profit = float(acc.get("acc_profit") or 0)
    
    # Helper to calculate percentage based on balance
    def calc_pct(val):
        if not val or balance == 0: return "0.00%"
        return f"{(float(val) / balance) * 100:.2f}%"

    return {
        "name":             safe(acc, "acc_name", "Unknown Client"),
        "acc_no":           acc_no,
        "platform":         safe(acc, "acc_platform", "Unknown"),
        "algo":             safe(acc, "acc_algo_name") if acc.get("acc_algo_name") else safe(acc, "acc_algo", "Unknown"),
        "risk_level":       safe(acc, "acc_risk_level", "Unknown"),
        "server":           safe(acc, "acc_server"),
        "currency":         safe(acc, "acc_currency", "USD"),
        "balance":          fmt_currency(balance),
        "profit_total":     fmt_currency(profit),
        "roi_total":        calc_pct(profit),
        "profit_month":     fmt_currency(acc.get("acc_profit_month")),
        "profit_week":      fmt_currency(acc.get("acc_profit_week")),
        "profit_today":     fmt_currency(acc.get("acc_profit_today")),
        "pct_daily":        calc_pct(acc.get("acc_profit_today")),
        "pct_weekly":       calc_pct(acc.get("acc_profit_week")),
        "pct_monthly":      calc_pct(acc.get("acc_profit_month")),
        "chart_data":       chart_data
    }