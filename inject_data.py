#!/usr/bin/env python3
"""
inject_data.py — Finance Dashboard 資料注入腳本
用法：python3 inject_data.py
產出：finance_dashboard.html（已嵌入資料的完整 HTML）
"""

import urllib.request
import csv
import json
import io
import datetime
import re
import os
import sys

# ═══════════════════════════════════════════════════
#  CONFIG — 只需修改此區塊
# ═══════════════════════════════════════════════════

SHEET_ID    = "1vP7eqzOZoUa3aDDVGlP-4QNKFkESvIKIM0i4yw5PrFk"
GID_ACCOUNT = "1459939608"   # 財務投影分頁（非個人帳戶）
GID_HISTORY = "1472600172"   # 歷史月份結算資產（F22 起 = 2026/01 結算值）
GID_ASSETS  = "1584973733"   # 資產配置分頁（股票損益）

MONTH_GIDS = {
    "1": "2054575111",
    "2": "21876207",
    "3": "615511442",
    "4": "223399667",
    # 新增月份只需在此加一行："月份": "GID"
}

# ── 各帳戶餘額（硬編碼，每次更新餘額只需改這裡）──────
# ⚠ 待確認：帳戶分頁 GID=1459939608 為財務投影表，不含帳戶餘額。
#   若之後找到含餘額的正確分頁 GID，可改為動態讀取。
HARDCODED_TWD = [
    {"name": "兆豐彰化",     "balance": 120158},
    {"name": "國泰CUBE",    "balance": 149822},
    {"name": "將來",         "balance": 12614},
    {"name": "台新Richard",  "balance": 26159},
    {"name": "遠東商銀",     "balance": 7037},
    {"name": "永豐DAWHO",   "balance": 29351},
    {"name": "陽信銀行",     "balance": 20936},
]
HARDCODED_USD = [
    {"name": "國泰CUBE外幣", "balance": 312.18},
    {"name": "Firstrade",   "balance": 454.39},
]

# ── 總資產（硬編碼，待確認正確儲存格後改為動態讀取）──
# ⚠ O4（row=3, col=14）目前值為 '65.63%'（投資總占比），非總資產。
#   請在 Google Sheets 確認總資產所在儲存格後，更新 TOTAL_ASSETS_ROW/COL。
TOTAL_ASSETS_HARDCODE = 10210886   # 使用者提供的近似值，供顯示用
TOTAL_ASSETS_ROW = 3               # TODO：待確認正確 row（目前 O4 非總資產）
TOTAL_ASSETS_COL = 14              # TODO：待確認正確 col

# ═══════════════════════════════════════════════════
#  財務投影表欄位（帳戶 GID，0-based index）
#  這張表有年度投資報酬與未來預測，可用於趨勢圖
# ═══════════════════════════════════════════════════

# 年度歷史趨勢：從 row 9 起，col 3=年份, col 4=起始資產, col 15=年末總資產
PROJ_START_ROW   = 9    # 第一筆歷史資料（2024年）
PROJ_YEAR_COL    = 3    # 年份
PROJ_START_COL   = 4    # 投資金額（年初資產）
PROJ_TOTAL_COL   = 15   # 總資產（年末）

# ═══════════════════════════════════════════════════
#  當月分頁欄位（0-based index）
# ═══════════════════════════════════════════════════

# AL 欄 = index 37（A=0..Z=25, AA=26..AL=37）
MONTHLY_TOTAL_ROW = 2    # AL3 = 本月總支出（原 AL7 已更正）
MONTHLY_TOTAL_COL = 37   # AL 欄
MONTHLY_AVG_ROW   = 7    # AL8 = 每日平均花費
MONTHLY_AVG_COL   = 37

# 消費明細結構（已驗證）：
#   col 0  = 日期
#   col 1~ = 各消費群組，每組 5 欄：[項目, 金額, 支付方式, 回饋類別, 消費類別]
#   最多 6 組（cols 1-30），col 31 = 日總金額
EXPENSE_START_COL   = 1   # 消費群組起始欄（col 0 = 日期）
EXPENSE_GROUPS      = 6   # 最多 6 組消費/天
EXPENSE_GROUP_SIZE  = 5   # 每組 5 欄
EXPENSE_AMT_OFFSET  = 1   # 金額在組內第 2 欄
EXPENSE_CAT_OFFSET  = 4   # 消費類別在組內第 5 欄

# row 0 = 標題, row 1 = 1號, row 2 = 2號 ...
# 讀取邏輯：range(1, today.day + 1)

# 資產配置分頁（GID=1584973733）
ASSETS_PNL_ROW = 16   # P17 = row 16, col 15
ASSETS_PNL_COL = 15
ASSETS_PCT_ROW = 16   # L17 = row 16, col 11（漲跌百分比）
ASSETS_PCT_COL = 11

# 歷史結算資產（GID=1472600172）
# F22 = 2026/01 結算（row=21, col=5），每月往下一列
HISTORY_BASE_ROW = 21  # 0-based：F22 = index 21
HISTORY_COL      = 5   # F 欄（0-based：A=0,B=1,...,F=5）
MONTHLY_BUDGET   = 40000  # 每月預算（本月剩餘 = MONTHLY_BUDGET - 本月支出）
DAILY_BUDGET     = 1333   # 每日預算（日均剩餘 = DAILY_BUDGET - 日均消費）

# 消費類別清單（共 26 類）
CATEGORIES = [
    "股票抽籤", "餐費", "飲料", "零食", "剪髮", "eTag", "洗車", "停車",
    "交通費", "健身房", "Youtube", "氣泡水", "生髮水", "藥藥", "整骨",
    "約會", "奢侈品", "生活用品", "醫藥費", "電信費", "車用", "電子書",
    "治裝", "Apple Store", "AI", "會員費",
]


# ═══════════════════════════════════════════════════
#  工具函式
# ═══════════════════════════════════════════════════

def fetch_csv(gid: str) -> list:
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
        f"/export?format=csv&gid={gid}"
    )
    print(f"  → fetch GID={gid} ...", end=" ", flush=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
        rows = list(csv.reader(io.StringIO(raw)))
        print(f"OK ({len(rows)} rows × {len(rows[0]) if rows else 0} cols)")
        return rows
    except Exception as e:
        print(f"FAILED: {e}")
        return []


def cell(rows: list, row: int, col: int) -> str:
    try:
        return rows[row][col].strip()
    except (IndexError, TypeError):
        return ""


def parse_num(s: str) -> float:
    if not s:
        return 0.0
    s = re.sub(r"[NT$,\s]", "", s)
    s = s.replace("(", "-").replace(")", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


# ═══════════════════════════════════════════════════
#  讀取：財務投影分頁（用於趨勢圖）
# ═══════════════════════════════════════════════════

def read_trend(rows: list) -> list:
    """從財務投影表讀取年度總資產歷史（實際年份）"""
    trend = []
    current_year = datetime.date.today().year

    for i in range(PROJ_START_ROW, len(rows)):
        year_str = cell(rows, i, PROJ_YEAR_COL)
        total_str = cell(rows, i, PROJ_TOTAL_COL)

        # 只取有效年份
        if not year_str or not year_str.isdigit() or len(year_str) != 4:
            break
        year = int(year_str)
        if year > current_year:
            break   # 只要歷史，不要未來預測

        total = parse_num(total_str)
        if total <= 0:
            break

        trend.append({"month": year_str, "total": total})

    return trend


# ═══════════════════════════════════════════════════
#  讀取：當月分頁
# ═══════════════════════════════════════════════════

def read_monthly(rows: list, month: int) -> dict:
    total_expense = parse_num(cell(rows, MONTHLY_TOTAL_ROW, MONTHLY_TOTAL_COL))
    avg_daily     = parse_num(cell(rows, MONTHLY_AVG_ROW,   MONTHLY_AVG_COL))

    today = datetime.date.today()
    day   = today.day if today.month == month else (len(rows) - 1)

    category_sum = {cat: 0.0 for cat in CATEGORIES}

    for row_idx in range(1, day + 1):   # row 1 = 1號
        if row_idx >= len(rows):
            break
        row = rows[row_idx]
        for g in range(EXPENSE_GROUPS):
            base    = EXPENSE_START_COL + g * EXPENSE_GROUP_SIZE  # 1,6,11,16,21,26
            amt_col = base + EXPENSE_AMT_OFFSET                    # 2,7,12,17,22,27
            cat_col = base + EXPENSE_CAT_OFFSET                    # 5,10,15,20,25,30
            try:
                amt_raw = row[amt_col] if amt_col < len(row) else ""
                cat     = row[cat_col].strip() if cat_col < len(row) else ""
            except IndexError:
                continue
            amt = parse_num(amt_raw)
            if amt <= 0 or not cat:
                continue
            if cat in category_sum:
                category_sum[cat] += amt

    category_sum_clean = {k: round(v) for k, v in category_sum.items() if v > 0}

    return {
        "month":         month,
        "total_expense": total_expense,
        "avg_daily":     avg_daily,
        "category_sum":  category_sum_clean,
    }


# ═══════════════════════════════════════════════════
#  讀取：股票損益（資產配置分頁）
# ═══════════════════════════════════════════════════

def read_stock_pnl() -> tuple:
    """Returns (pnl_amount, pnl_pct): P17 和 L17"""
    if not GID_ASSETS:
        print("  → 資產配置 GID 未設定，股票損益使用 0")
        return 0.0, 0.0
    rows = fetch_csv(GID_ASSETS)
    if not rows:
        return 0.0, 0.0
    pnl = parse_num(cell(rows, ASSETS_PNL_ROW, ASSETS_PNL_COL))  # P17
    pct = parse_num(cell(rows, ASSETS_PCT_ROW,  ASSETS_PCT_COL))  # L17
    return pnl, pct


# ═══════════════════════════════════════════════════
#  讀取：歷史月份結算資產（GID=1472600172）
# ═══════════════════════════════════════════════════

def read_history_settled(rows: list, current_month: int) -> tuple:
    """
    從歷史結算分頁取得上個月的結算總資產，計算 MoM 漲跌。
    Returns (prev_settled, mom_change_pct)
    """
    if current_month <= 1:
        return 0.0, None
    # 前一個月的 row：HISTORY_BASE_ROW + (current_month - 2)
    prev_row = HISTORY_BASE_ROW + (current_month - 2)
    prev_val = parse_num(cell(rows, prev_row, HISTORY_COL))
    return prev_val, None  # mom_change 在 main() 計算


# ═══════════════════════════════════════════════════
#  主程式
# ═══════════════════════════════════════════════════

def main():
    today     = datetime.date.today()
    month     = today.month
    month_str = str(month)

    print(f"Finance Dashboard 資料注入器  [{today}  第{month}月]")
    print("=" * 58)

    # ── 財務投影分頁（年度趨勢）──
    print("【財務投影分頁（帳戶 GID）】")
    acct_rows = fetch_csv(GID_ACCOUNT)
    trend = read_trend(acct_rows) if acct_rows else []

    # ── 歷史結算分頁（MoM 比較）──
    print("【歷史結算分頁（GID_HISTORY）】")
    hist_rows = fetch_csv(GID_HISTORY) if GID_HISTORY else []
    prev_settled = 0.0
    if hist_rows and month > 1:
        prev_settled, _ = read_history_settled(hist_rows, month)
    mom_change = None
    if prev_settled > 0:
        mom_change = round((TOTAL_ASSETS_HARDCODE - prev_settled) / prev_settled * 100, 2)

    # ── 所有月份分頁（預載）──
    all_months = {}
    for m_str, gid in MONTH_GIDS.items():
        print(f"【{m_str}月分頁】")
        rows = fetch_csv(gid)
        if rows:
            m_data = read_monthly(rows, int(m_str))
            remaining      = MONTHLY_BUDGET - m_data["total_expense"]
            daily_remaining = DAILY_BUDGET  - m_data["avg_daily"]
            all_months[m_str] = {
                "total_expense":   m_data["total_expense"],
                "avg_daily":       m_data["avg_daily"],
                "remaining":       remaining,
                "daily_remaining": daily_remaining,
                "category_sum":    m_data["category_sum"],
            }

    # 當月資料（向後相容）
    monthly = all_months.get(month_str, {
        "total_expense": 0, "avg_daily": 0,
        "remaining": MONTHLY_BUDGET, "daily_remaining": DAILY_BUDGET,
        "category_sum": {}
    })

    # ── 資產配置分頁 ──
    print("【資產配置分頁】")
    stock_pnl, stock_pct = read_stock_pnl()

    # ── 帳戶餘額（硬編碼）──
    accounts_twd = [a for a in HARDCODED_TWD if a["balance"] > 0]
    accounts_usd = [a for a in HARDCODED_USD if a["balance"] > 0]

    # ── 組合 JSON ──
    payload = {
        "generated_at":    today.isoformat(),
        "current_month":   month,
        "total_assets":    TOTAL_ASSETS_HARDCODE,
        "mom_change":      mom_change,
        "monthly_expense": monthly["total_expense"],
        "avg_daily":       monthly["avg_daily"],
        "remaining":       monthly["remaining"],
        "daily_remaining": monthly["daily_remaining"],
        "stock_daily_pnl": stock_pnl,
        "stock_pct":       stock_pct,
        "trend":           trend,
        "accounts_twd":    accounts_twd,
        "accounts_usd":    accounts_usd,
        "category_sum":    monthly["category_sum"],
        "all_months":      all_months,   # 所有月份預載資料
    }

    json_str = json.dumps(payload, ensure_ascii=False, indent=2)

    # ── 注入 HTML ──
    base_dir      = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, "template.html")
    output_path   = os.path.join(base_dir, "finance_dashboard.html")

    if not os.path.exists(template_path):
        print(f"❌ 找不到 {template_path}")
        sys.exit(1)

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    if "INJECTED_DATA_PLACEHOLDER" not in html:
        print("❌ template.html 中找不到 INJECTED_DATA_PLACEHOLDER")
        sys.exit(1)

    html = html.replace("INJECTED_DATA_PLACEHOLDER", json_str)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    # ── 摘要 ──
    print("=" * 58)
    print(f"✅  產生 finance_dashboard.html")
    print(f"    總資產（硬編碼）: NT${TOTAL_ASSETS_HARDCODE:>12,.0f}")
    mom_str = f"{mom_change:+.2f}%" if mom_change is not None else "N/A"
    print(f"    vs 上月結算     :  {mom_str}")
    print(f"    本月支出（AL3） : NT${monthly['total_expense']:>12,.0f}")
    print(f"    本月剩餘        : NT${monthly['remaining']:>12,.0f}")
    print(f"    每日均花（AL8） : NT${monthly['avg_daily']:>12,.0f}")
    print(f"    日均剩餘        : NT${monthly['daily_remaining']:>12,.0f}")
    pnl_sign = '+' if stock_pnl >= 0 else ''
    pct_sign = '+' if stock_pct >= 0 else ''
    print(f"    股票損益（P17） :  {pnl_sign}NT${abs(stock_pnl):>11,.0f}")
    print(f"    股票漲跌（L17） :  {pct_sign}{stock_pct:.2f}%")
    print(f"    台幣帳戶        : {len(accounts_twd)} 個")
    print(f"    外幣帳戶        : {len(accounts_usd)} 個")
    print(f"    趨勢資料點      : {len(trend)} 年")
    print(f"    預載月份        : {list(all_months.keys())}")
    print(f"    消費類別        : {len(monthly.get('category_sum',{}))} 類")
    if monthly.get("category_sum"):
        print("    消費明細（top5）:")
        top5 = sorted(monthly["category_sum"].items(), key=lambda x: -x[1])[:5]
        for cat, amt in top5:
            print(f"      {cat}: NT${amt:,.0f}")
    print()
    print("⚠  待確認事項：")
    print("   1. 帳戶餘額目前為硬編碼，需每次手動更新 inject_data.py")
    print("   2. 總資產為硬編碼（TOTAL_ASSETS_HARDCODE），請確認正確儲存格")
    print("   3. 主要工作流程已改為直接開啟 finance_dashboard.html（即時 fetch）")


if __name__ == "__main__":
    main()
