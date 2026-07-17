# 投資報告端 postMessage 契約

> 給《投資分析》（及游庭皓／股癌整理）等**產出報告 HTML** 的專案。
> 讓 2026記帳 App 日報面板頂部的「齒輪（8 風格）」與「月亮（深淺）」能遠端驅動報告內建切換器。

報告 HTML 被 App 以 `<iframe srcdoc>`（`sandbox="allow-scripts allow-same-origin"`）載入。
App 端在 iframe 載入完成、以及使用者每次點齒輪／月亮時，會 `postMessage` 進來。

## App → 報告（報告端要監聽）

```js
{ app:'percento', kind:'display', style: 0..7, theme: 'dark' | 'light' }
```

- `style`：0–7，對應報告自己的 8 種風格（第 1 種 = 0，以此類推）。
- `theme`：`'dark'` 或 `'light'`。

## 報告端要加的程式（貼進報告 HTML 的 `<script>`）

把報告「套用第 N 風格」「套用深/淺」各抽成一個函式（原本按鈕也呼叫它們），再加監聽：

```js
// 你報告內既有的切換邏輯，抽成這兩個函式：
function applyStyle(i){ /* i = 0..7，套用第 i+1 種風格 */ }
function applyTheme(mode){ /* mode = 'dark' | 'light' */ }

// 監聽 App 傳進來的設定（訊息可能早於或晚於 DOM ready，兩種都要能套）
window.addEventListener('message', function(e){
  var d = e.data;
  if(!d || d.app !== 'percento') return;
  if(d.kind === 'display'){
    if(typeof d.style === 'number') applyStyle(d.style);
    if(d.theme) applyTheme(d.theme);
  }
});
```

要點：
- 報告**自己內建的 8 風格 / 深淺切換器保留**，postMessage 只是「遠端按同一組按鈕」，兩邊共用 `applyStyle`／`applyTheme`。
- App 會在 iframe `onload` 再送一次，所以 DOM 已就緒；但保險起見 `applyStyle`／`applyTheme` 要能在任何時機安全套用。

## 報告 → App（選配：讓 iframe 內橫滑也能切三份報告）

iframe 內的觸控 App 收不到，若要「在報告內容上左右滑」也能切報告，報告端偵測到橫滑時回傳：

```js
// dir='left' → 切下一份、'right' → 上一份
parent.postMessage({ app:'percento', kind:'swipe', dir:'left' }, '*');
```

不做也沒關係——App 面板的三顆圓點可直接點選跳頁。

## 發布位置對照

| 報告 | 前端 type | 發布端點 |
|------|-----------|----------|
| 投資分析日報 | `daily` | `putReport&token=…&type=daily`（或省略 type，預設 daily） |
| 游庭皓 節目整理 | `youting` | `putReport&token=…&type=youting` |
| 股癌 Podcast 整理 | `gua` | `putReport&token=…&type=gua` |

token = `WebApp.gs` 的 `REPORT_TOKEN`。POST body 放整份報告 HTML。
