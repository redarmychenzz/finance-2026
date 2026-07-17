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
5. **下拉重新整理**：主頁 / 資產分配比頁 / 股票詳情頁 / 趨勢頁四處都能原地下拉刷新（共用 `attachPullToRefresh`），動畫是置中的白色長條律動（等化器）。趨勢頁特別處理：起點在圖表(.tcw)上的觸控屬縮放/長按手勢，不觸發下拉
6. **互動調整**：點淨資產金額進入/離開「台幣/美金占比」頁（已移除上滑手勢）
7. **App 圖示**：原創設計（深藍漸層底 + 四色書籤斜階梯堆疊 + 白色 %），非複製 Percento 商用圖示。已接 favicon / apple-touch-icon，四角透明圓角
8. **網頁標題**：`<title>2026記帳</title>`（加到主畫面的預設名稱也吃這個）
9. **金額預設顯示**：進入點 `startApp()` 預設**顯示**金額（原本預設隱藏），右上角眼睛可切換
10. **趨勢圖改版**（2026/07/16-17，`index.html` 趨勢頁全面重寫）：三分頁「總資產／台股市值／美股市值(複委託+海外)」，資料接 `?action=getSnapshots` 真實快照。規格：
    - 圖高固定 135px（viewBox 400×160，縮放比例一致文字不變形）；區間增減資訊與 20/60/120 日快捷在圖上方一列（`.t-head`），剩餘高度由 auto margin 均分各欄塊間距
    - 預設近 20 個交易日；手勢連續縮放：手機在圖上按住上下滑、電腦滾輪（7 天～全部），縮放到 20/60/120 時快捷自動反白（Pointer Events + `touch-action:none`）
    - 單日檢視：手機長按 350ms／電腦點擊或按住拖曳 → 虛線對位線＋**白底**單日資訊框浮於資料點旁（日期、金額、較前一交易日增減），右下 ✕ 關閉；左上區間摘要不受影響
    - 每日直向格線標資料點位置（>60 日簡化為每 5 天）；Y 軸貼合可見區間＋「萬」刻度；跳過週六日快照；市值 null 舊列略過不補 0；金額配合右上眼睛遮罩；快照 5 分鐘記憶體快取
    - 資料累積：總資產自 2026-07-14、台股/美股市值自 2026-07-16 起，隨每日 07:00 快照自動變長
11. **導覽列**：第三顆按鈕改為圓餅圖示（同線條風格），直接進入「投資分析日報」面板（詳見下方日報段落）
12. **消費明細真實資料**：後端 `getConsumption` 讀當月分頁（A1:AE{天數+1}），日常消費詳情頁為真實資料（早期示範資料已汰換）

## 目前待辦 / 已知事項
- **後端 `WebApp.gs` 不在 git**：任何後端改動要手動貼進 Apps Script 並「重新部署」才生效。本機 `WebApp.gs`（專案上層資料夾）為最新版。已部署驗證的端點：getDashboard（含前一交易日徽章邏輯 `tradingBaseline_`）/ getConsumption / getSnapshots / takeSnapshot；`getReport`/`putReport`（日報）以實際部署狀態為準
- ~~資產配置頁（alloc）每日快照 diff~~ → **決定不做**（2026/07/16）：主頁已有四顆「較昨收」徽章，分配比頁保持乾淨。後端 `getDashboard` 回傳的 `assetDiff` 目前前端未使用，留著備用
- 底部選單（⋯sheet）與「設定」頁目前**無入口**（導覽列第三鈕已改為直接進日報），程式碼保留，之後要恢復再接
- 值有時跨次讀取略有差異 → 是即時匯率 + 盤中股價時間差造成，非 bug
- 本機 git 對 OneDrive 目錄已設 `core.fileMode false`（OneDrive 會動權限位，避免整包檔案誤報已修改）；`git status` 顯示 ahead 很多時先 `git fetch` 再判斷

## 部署 / 快取提醒
- 前端：改完 `index.html` → `git push` main → GitHub Pages 自動更新。使用者需硬重新整理才看到新版
- 圖示 / 標題改動：已加到主畫面者需移除舊的、重新「加到主畫面」才會更新

## 投資分析日報分頁(2026-07-17 新增)

- **前端**:導覽列最右鈕(圓餅)**直接**進入全螢幕日報面板(2026-07-17 稍晚改:原底部選單入口已取消,選單本身與「設定」目前無入口,程式碼保留)。面板 `#rptPanel`,fetch `?action=getReport` 取 `{ok,html,updated}`,iframe srcdoc 渲染(報告自帶八風格切換器),localStorage 快取(`rptHtml`/`rptUpd`)供離線與秒開。
- **後端**(`WebApp.gs`,需手動貼上+重新部署):`doGet ?action=getReport` 讀 Drive 固定檔;`doPost ?action=putReport&token=…` 收日報 HTML 寫入 Drive(檔案 ID 記在 ScriptProperties `REPORT_FILE_ID`)。token 寫在 WebApp.gs 的 `REPORT_TOKEN`,與《投資分析》`/daily-report` 發布指令一致。
- **發布來源**:《投資分析》專案 `/daily-report` 第 6 步之 4(每日 06:30 排程+手動),curl POST;同時仍發布 Claude Artifact(fd6d75f3…)作備援。
- **注意**:重新部署 Apps Script 時務必用「管理部署 → 編輯 → 新版本」保持同一個 /exec 網址;若開新部署導致網址改變,要同步改前端 `API_URL` 與《投資分析》`daily-report.md` 的發布網址。
