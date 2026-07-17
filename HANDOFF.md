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
    - 版面（2026/07/17 家裡二修定案）：由上至下**等距 18px** 排列 pills → 資訊卡 → 圖表 → X軸+摘要 → 導覽列；圖表 `.tcw` `flex:1` **高度自適應**吃掉剩餘高度（min-height 120px），viewBox 高度由 JS 依實際長寬比動態算（`tVBH`，寬固定 400）→ 文字不變形，`resize` 時重繪；區間增減資訊卡補回 `--card-bg` 底色圓角卡
    - 首末資料點左右各留 14/400（3.5%）內距不貼邊、`.t-xlbls` padding 同步 3.5% 對齊；單一資料點時 X 標籤置中
    - 載入優化：快照存 localStorage（`trendSnaps_v1`）先畫再背景更新（stale-while-revalidate）＋ App 啟動 2.5 秒後預抓一次
    - 手勢（2026/07/17 家裡三修定案）：整頁（**含圖表區**）左滑=下一分頁、右滑=上一分頁、下拉=重新整理；圖表縮放改為**雙指捏合**（指距比例→天數，桌面滾輪保留）；長按 350ms=單日檢視（成立時取消切分頁誤觸，捏合中 canPull 擋下拉）
    - 底部留白：`#trend` padding-bottom = 導覽列 bottom + 53px + 28px（含 safe-area），摘要與導覽列間距加倍且 iPhone 瀏海機不再偏擠
    - 手勢（2026/07/18 收斂）：**長按檢視/雙指捏合進行中**由 `tChartBusy` 擋掉左右切分頁與下拉刷新（長按成立→ `tSw=null`+`tChartBusy=true`，捏合起始亦置 true，所有手指離開才歸 false）；`attachPullToRefresh` touchmove 會重新檢查 canPull，中途條件改變即放手
- **導覽膠囊樣式**：2026/07/18 曾試強化液態玻璃立體感，使用者覺得醜已**還原**回原本簡潔版（`.nav` rgba(255,255,255,0.10) 底、blur20/saturate180、單層 inset 高光+外投影）
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

## 投資報告面板(2026-07-17 新增；2026-07-18 三頁+風格/深淺/退出改版)

- **三份報告左右滑**(2026-07-18):`RPT_TABS`=daily(投資分析日報)／youting(游庭皓 節目整理)／gua(股癌 Podcast 整理)。面板 `#rptPanel` 頂部標題+更新時間+齒輪(8風格)+月亮(深淺)；下方三顆圓點(可點跳頁)；`.rpt-body` 內 iframe srcdoc 渲染。各型分別 `?action=getReport&type=` 抓取、localStorage 分型快取(`rptHtml_<type>`/`rptUpd_<type>`)。左右滑：非 iframe 區(圓點/邊界)由 `.rpt-body` touch 判斷；iframe 內滑動需報告端回傳訊息(見下方契約)。
- **退出方式改版**(2026-07-18)：**取消右上叉叉**，改用底部導覽膠囊退出——報告開啟時 `body.rpt-open` 讓 `.nav` z-index 升到 130 浮在面板(120)之上，點 home/趨勢即 `closeReport()`。moreBtn(圓餅)**一律開在第一頁 daily**(`rptLoad(0)`)並高亮。
- **報告內建切換列隱藏**(2026-07-18)：iframe `onload` 時同源注入 `#ctrl{display:none}`，隱藏報告右下角自帶的 8 風格/深淺列(改由頂部齒輪/月亮控制)。對 daily/youting/gua 皆生效、不需改報告端。
- **游庭皓/股癌接入**(2026-07-18，task4)：`youting`=財經皓角、`gua`=股癌，已把 `投資分析/reports/haojiao_*.html`、`gooaye_*.html` 補上 postMessage 監聽並 POST 到對應 type(內容已上線)。未來自動發布：`投資分析/.claude/commands/haojiao.md`(加 type=youting 雙發布)、`gooaye.md`(加 type=gua)已補 curl 步驟＋註明監聽區塊保留。這兩種報告用「上一份同型 html 當範本」，故監聽已隨範本前傳。
- **8風格/深淺鈕 = postMessage 契約**(2026-07-18，task5)：齒輪選單 8 顆(風格1–8)、月亮切深淺，選擇存 localStorage(`rptStyle`/`rptTheme`)，透過 `rptFrame.contentWindow.postMessage({app:'percento',kind:'display',style:0..7,theme:'dark'|'light'},'*')` 送入報告(iframe onload 時也送一次)。報告端另可回傳 `{app:'percento',kind:'swipe',dir:'left'|'right'}` 讓 iframe 內橫滑也能切報告。契約全文見 [REPORT_CONTRACT.md](REPORT_CONTRACT.md)。
  - **✅ 契約已在《投資分析》端實作並端到端驗證(2026-07-18)**：報告模板 `投資分析/templates/report-template-web.html` 的 `#ctrl` 切換器 `<script>` 已加監聽(對應 style 0..7→s1..s8、theme、呼叫既有 `apply()`)＋橫滑回傳；`投資分析/.claude/commands/daily-report.md` 第 65 行註明該區塊不可刪。**現有 7/17 日報已補上同段 script 並重新 POST 覆蓋 Drive**，App 齒輪選風格3已實測讓報告 iframe 變金融終端綠、月亮切 light↔dark 成功。游庭皓/gua 沿用同模板故一併支援。(《投資分析》非 git repo，改動存本機 OneDrive)
- **後端**(`WebApp.gs`,需手動貼上+重新部署)：`getReport(e)`/`putReport` 支援 `&type=daily|youting|gua`，三型各自 Drive 檔(ScriptProperties `REPORT_FILE_ID_<type>`、`REPORT_UPDATED_<type>`；daily 相容舊 `REPORT_FILE_ID`)。token 仍為 `REPORT_TOKEN`。**youting/gua 由各自 Claude 專案 POST `putReport&type=…` 發布**(daily 仍走《投資分析》`/daily-report`)。發布前該型顯示「尚未發布」。
- **Drive 授權待辦**：`getReport` 曾回「沒有呼叫 DriveApp.createFile 的權限」——`WebApp.gs` 內已備 `authorizeDrive()`（無底線→會出現在編輯器執行下拉），選它按▶執行一次同意 Drive 權限即通，之後不必再跑。
- **注意**:重新部署 Apps Script 時務必用「管理部署 → 編輯 → 新版本」保持同一個 /exec 網址;若網址改變,要同步改前端 `API_URL` 與各發布專案的網址。
