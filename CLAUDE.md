# Finance Dashboard 專案說明

## 檔案結構
```
finance-dashboard/
├── finance_dashboard.html  ← 主要產出物（直接開啟即可，即時 fetch Google Sheets）
├── template.html           ← 靜態注入模板（inject_data.py 用）
├── inject_data.py          ← 靜態資料注入腳本（備用）
└── CLAUDE.md               ← 本說明
```

## 主要使用方式（推薦）

直接用瀏覽器開啟 `finance_dashboard.html`，頁面會自動 fetch Google Sheets 即時資料。
**不需要執行 Python 腳本。**

```
雙擊 finance_dashboard.html → 輸入密碼 → 自動載入資料
```

### 自動更新
- 每 5 分鐘自動重新 fetch 所有資料
- 右上角顯示「更新：HH:MM:SS」

### ⚠️ 重要：Google Sheets 必須設為公開
直接 fetch 需要 Google Sheets 設為「知道連結的人可以檢視」：
1. 試算表右上角點擊「共用」
2. 「一般存取權」→「知道連結的人」
3. 角色選「檢視者」
4. 點擊「完成」

若未設定，頁面會顯示錯誤提示。

---

## 備用方式（靜態注入）

```bash
python3 inject_data.py
# → 重新產生 finance_dashboard.html（覆蓋即時版本）
```

**注意：靜態注入會覆蓋即時版本，需重新執行腳本才能更新資料。**

---

## Google Sheets 設定

Sheet ID：`1vP7eqzOZoUa3aDDVGlP-4QNKFkESvIKIM0i4yw5PrFk`

| 分頁 | GID | 用途 |
|------|-----|------|
| 收入（年度所得）| 1459939608 | 年度趨勢圖（GID_ACCOUNTS）|
| 帳戶（月結算） | 1472600172 | O4 即時總資產 + MoM 月結算（GID_HISTORY）|
| 資產配置 | 1584973733 | 股票今日損益 |
| 1月 | 2054575111 | 當月支出分類 |
| 2月 | 21876207 | 當月支出分類 |
| 3月 | 615511442 | 當月支出分類 |
| 4月 | 223399667 | 當月支出分類 |

新增月份：在 `inject_data.py` 頂部 `MONTH_GIDS` 加一行即可，`finance_dashboard.html` 同步更新。

---

## 資料欄位對應（0-based index）

### 收入分頁（GID=1459939608）→ 代碼中的 GID_ACCOUNTS / rowsAcct
| 資料 | 儲存格 | row | col |
|------|--------|-----|-----|
| 歷史年份 | D欄（row9起） | 8+ | 3 |
| 歷史總資產 | P欄（row9起） | 8+ | 15 |
⚠️ 注意：此分頁的 O4 是「投資總占比」(65.63%)，**不是總資產**。

### 帳戶分頁（GID=1472600172）→ 代碼中的 GID_HISTORY / rowsHist
| 資料 | 儲存格 | row（0-based）| col |
|------|--------|--------------|-----|
| **目前總資產** | **O4** | **3** | **14** |
| 2026/01 結算 | F22 | 21 | 5 |
| 2026/02 結算 | F23 | 22 | 5 |
| 2026/03 結算 | F24 | 23 | 5 |
| 2026/04 結算 | F25 | 24 | 5 |
| 依此類推 | F{21+month} | 20+month | 5 |

MoM 計算：`(當月總資產 O4 - 上月結算值) / 上月結算值 × 100`

### 資產配置分頁（GID=1584973733）
| 資料 | 儲存格 | row | col |
|------|--------|-----|-----|
| 股票今日損益 | P17 | 16 | 15 |
| 股票漲跌百分比 | L17 | 16 | 11 |

### 當月分頁（1月~4月）
| 資料 | 儲存格 | row | col |
|------|--------|-----|-----|
| 本月總支出 | **AL3** | **2** | **37** |
| 分類名稱 | AO（col=40）| row2~row27 | 40 |
| 分類金額 | AP（col=41）| row2~row27 | 41 |
| 分類佔比 | AQ（col=42）| row2~row27 | 42 |

消費明細 B2:AE31，5 組 × 5 欄，row2=1號...row31=30號：
- 組 g (0~4)：`base = 1 + g*5`
- 名稱 = `base`、金額 = `base+1`、消費類別 = `base+4`

帳戶餘額 row index（0-indexed，X欄=col23）：
- 兆豐銀行：row=6
- 國泰Cube(TWD)：row=12
- 將來銀行：row=15
- 台新Richard：row=16
- 遠東商銀：row=17
- 永豐DAWHO：row=22
- 陽信銀行：row=23
- 國泰Cube(USD)：row=31
- Firstrade：row=34

現金流 = 兆豐+將來+台新+遠東+永豐+陽信（不含國泰Cube台幣）

---

## 預算設定

| 項目 | 預算 | 計算邏輯 |
|------|------|---------|
| 每月預算 | NT$40,000 | 本月剩餘 = 40000 - 本月支出 |
| 每日預算 | NT$1,333 | 日均剩餘 = 1333 - 日均消費 |

修改預算：在 `finance_dashboard.html` JavaScript 頂部修改 `MONTHLY_BUDGET` / `DAILY_BUDGET`。

---

## 密碼設定

目前密碼：`micronic`（SHA-256 hash 已寫入 HTML）

登入狀態永久儲存於 `localStorage`，關閉瀏覽器後不需重新輸入。
清除方式：瀏覽器 DevTools → Application → Local Storage → 刪除 `finance_auth`

換密碼步驟：
1. 瀏覽器 DevTools console 執行：
   ```javascript
   crypto.subtle.digest('SHA-256',new TextEncoder().encode('新密碼'))
     .then(b=>console.log([...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,'0')).join('')))
   ```
2. 複製輸出，替換 `finance_dashboard.html` 中的 `PASSWORD_HASH` 值

---

## 帳戶餘額

目前為硬編碼（尚未找到 Sheets 正確欄位）。
更新方式：修改 `finance_dashboard.html` 中的 `HARDCODED_TWD` / `HARDCODED_USD` 陣列。

---

## GitHub Pages 部署架構

### 部署方式
1. 本機執行 `inject_data.py` → 產生 `finance_dashboard.html`（含當日靜態快照）
2. 複製為 `index.html`（GitHub Pages 讀取入口）
3. Push 到 GitHub → Pages 自動更新

### 頁面行為（混合模式）
- **首次載入**：顯示靜態快照（inject_data.py 注入的當日資料）
- **背景更新**：頁面載入後自動 fetch Google Sheets 最新資料，每 5 分鐘刷新
- **月份切換**：點選月份 pill 切換顯示不同月份的消費明細
- **Favicon**：💰 錢幣 emoji，透過 SVG data URI 嵌入，不需外部圖片

### 安全性架構
- **repo 設為 Public**（GitHub Pages 免費方案只支援公開 repo）
- **Google Sheets 設為公開**（知道連結的人可以檢視）
- **密碼保護**：網頁本身需要輸入密碼（SHA-256 驗證）才能查看資料
- **個資保護**：密碼保護 + Sheets 無法直接找到，風險可接受

### 資料更新流程
每次想更新靜態快照（例如帳戶餘額有變動）：
```bash
python3 inject_data.py           # 更新靜態資料
cp finance_dashboard.html index.html
git add finance_dashboard.html index.html
git commit -m "update data $(date +%Y-%m-%d)"
git push
```
Google Sheets 的消費/支出資料會每次開啟頁面自動 fetch，無需手動更新。

### CSV 解析重要說明
Google Sheets 匯出 CSV 時，某些欄位含換行符（信用卡說明等），
raw 文字行數（38 行）≠ 實際資料列數（35 列）。
**parseCsv 必須使用字元逐步解析（已修正），不可用 split('\n') 分割。**
舊版 live 版本的 parseCsv 有此 bug，導致 AL8（每日平均）讀取錯誤顯示 0。

## 待辦事項
- [ ] 確認帳戶分頁 O4 是否為正確的總資產儲存格
- [ ] 確認帳戶餘額動態讀取欄位（目前為硬編碼）
- [ ] 設定正式密碼
- [x] 建立 GitHub repo 並啟用 Pages 部署
- [ ] 新增月份時同步更新 `inject_data.py` 的 `MONTH_GIDS`（`finance_dashboard.html` 的 JS 也需同步更新）
