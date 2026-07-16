# 專案交接：Percento 風格記帳網頁（2026記帳）

> 跨裝置交接文件。要在別台裝置繼續開發，把這份內容給 Claude 即可。

## 專案概觀
個人理財儀表板網頁 App，手機優先、液態玻璃風格。分兩部分：

| 部分 | 技術 | 位置 / 部署 |
|------|------|------------|
| **前端** | 單頁 HTML/CSS/JS | `finance-dashboard/index.html`，git repo `finance-2026`（GitHub：`redarmychenzz/finance-2026`），部署到 GitHub Pages，`main` 分支自動生效 |
| **後端** | Google Apps Script | `WebApp.gs`（**不在 git 內**，手動貼到 Apps Script 編輯器並部署），`doGet` 回傳 JSON，`?action=` 帶參數 |

- 本機專案路徑：`.../Percento風格記帳/`（前端在子資料夾 `finance-dashboard/`，後端 `WebApp.gs` 在上層）
- 前端改完的慣例：**直接 commit + push 到 main，不用再問**
- 後端 Apps Script 部署網址（web app `/exec`）由使用者提供，會變動

## 資料來源
- Google Sheets（GOOGLEFINANCE 抓即時股價）
- USD/TWD 匯率 = `Config!K3` = `GOOGLEFINANCE("CURRENCY:USDTWD")`，fallback 31
- 資產四大群組：`bank`（銀行）/ `tw_stock`（台股）/ `sub_broker`（複委託）/ `overseas`（海外券商）
- 損益幣別：台股用 TWD、複委託/海外用 USD → **由網站以即時匯率換算成 TWD**（不用 Sheet 內固定匯率的儲存格）

## 已完成的主要功能
1. **即時匯率換算損益**：複委託/海外券商損益改用網站即時匯率，取代 Sheet 固定匯率儲存格
2. **已實現損益**：讀「股票已實現」分頁（`getRealizedPnl_`），欄位對照：
   - `tw_stock`: BC / BN / CR（TWD）
   - `sub_broker`: AG / AR / BY（USD）
   - `overseas`: J / V / CI（USD）
   - 範圍 row 20–100
3. **每日快照 DailySnapshot**：分頁欄位 `日期|總資產|台股損益|複委託損益|海外損益|台股市值|複委託市值|海外市值`（8 欄；市值 3 欄為 2026/07/16 新增，舊資料列該三欄空白）。時間觸發 `takeDailySnapshot()` 在**每天早上 7:00**（台股美股都收盤），透過 `settlementDateKey_()` 記為「前一天」的資料。另有 `?action=getSnapshots` 回傳全部快照（趨勢圖歷史曲線用）
4. **今日損益徽章**：主頁淨資產旁 + 台股/複委託/海外三張卡各一個。**正紅負綠**（台灣習慣），0 為中性灰底。口徑分兩種（2026/07/16 調整）：
   - 淨資產徽章 = live 減「前一日」快照（07:00 換日線）
   - 三張卡 = live 減「**前一交易日**」收盤快照（跳過週六日；美股時段跨半夜 21:30~05:00，白天顯示昨晚那場的漲跌）。後端 `tradingBaseline_()` 決定基準，因此 `pnlDiff.total ≠ 三卡相加` 屬預期
5. **下拉重新整理**：主頁 / 資產分配比頁 / 股票詳情頁三處都能原地下拉刷新（共用 `attachPullToRefresh`），動畫是置中的白色長條律動（等化器）
6. **互動調整**：點淨資產金額進入/離開「台幣/美金占比」頁（已移除上滑手勢）
7. **App 圖示**：原創設計（深藍漸層底 + 四色書籤斜階梯堆疊 + 白色 %），非複製 Percento 商用圖示。已接 favicon / apple-touch-icon，四角透明圓角
8. **網頁標題**：`<title>2026記帳</title>`（加到主畫面的預設名稱也吃這個）
9. **金額預設顯示**：進入點 `startApp()` 預設**顯示**金額（原本預設隱藏），右上角眼睛可切換

## 目前待辦 / 已知事項
- **後端 `WebApp.gs` 不在 git**：任何後端改動要手動貼進 Apps Script 並「重新部署」才生效。本機 `WebApp.gs`（專案上層資料夾）為最新版
- **趨勢圖改版進行中**：主頁第二分頁要改成三個分頁「總資產／台股市值／美股市值(複委託+海外)」，四種設計範例已出（範例 A 三分 Pill／B 三線疊圖／C 大數字儀表／D 橫滑卡片），等使用者挑選後改 `index.html`。歷史曲線資料來源 = `getSnapshots`（市值欄 2026-07-16 起才有值，舊列為 null 要略過）
- ~~消費明細用示範資料~~ → 已完成：`getConsumption` 端點已部署，消費明細為真實資料
- ~~快照市值 3 欄 + getSnapshots~~ → 已完成：2026/07/16 已部署並驗證，`takeSnapshot` 手動跑過一次，當日起有市值資料
- ~~資產配置頁（alloc）每日快照 diff~~ → **決定不做**（2026/07/16）：主頁已有四顆「較昨收」徽章，分配比頁保持乾淨。後端 `getDashboard` 回傳的 `assetDiff` 目前前端未使用，留著備用
- 值有時跨次讀取略有差異 → 是即時匯率 + 盤中股價時間差造成，非 bug

## 部署 / 快取提醒
- 前端：改完 `index.html` → `git push` main → GitHub Pages 自動更新。使用者需硬重新整理才看到新版
- 圖示 / 標題改動：已加到主畫面者需移除舊的、重新「加到主畫面」才會更新
