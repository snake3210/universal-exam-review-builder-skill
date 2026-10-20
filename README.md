# Universal Exam Review Builder (`universal-exam-review-builder`)

一套專為 Antigravity / AI Agent 打造的 **「萬用考題拆解與視覺化戰情複習系統建置器」** 全域技能（Global Skill）。
無論是 **國小/國高中學科（數學、自然、社會）** 還是 **國家專技高考/職類認證（消防設備師/士、EMT-P/ACLS、警大消佐班、法律、工程師證照）**，只需提供考卷檔案或指定考試主題，即可自動完成：

1. **三種輸入來源支援**：
   - ① 本地考卷解析（PDF / Word / 圖片，支援自動偵測掃描檔並切換 AI 視覺辨識）
   - ② 公開歷屆考卷自動爬蟲下載（內建 1 req/s 速率限制與指數退避）
   - ③ 無現成考卷時，依指定課綱/法規主題由 AI 精準命題
2. **圖表無損高畫質裁切（250 DPI）**：自動裁切考卷內嵌幾何圖、實驗圖表、心電圖或工程圖，題幹「零劇透」還原真實考場。
3. **四維度 AI 逆向工程深度拆解**：
   - `algorithm_path`：3～4 步視覺化思考決策節點圖（最終結論以翡翠綠高亮）
   - `key_triggers`：題幹破題關鍵字螢光筆標記
   - `confusion_trap`：易混淆誘答選項拆解 + 跨年度考古題家族串聯 + 送分/多解爭議題剖析
   - `guideline_check`：最新修法 / 醫療指引 / 課綱公式檢核警示
4. **雙主題（🌙 深色戰情室 / ☀️ 明亮護眼）響應式 SPA ＋ 單一檔案離線獨立版（`.html`）**：
   - 支援電腦雙欄並列、手機/平板底部懸浮導覽列、圖片雙指無段縮放（Pinch-to-Zoom）、5 大考前衝刺速查表抽屜（Cheat Sheet Modal）。

---

## 🚀 一鍵安裝方式（跨電腦同步）

將本儲存庫 Clone 至你的 Antigravity 全域技能目錄（`~/.gemini/config/skills/`）：

```bash
git clone https://github.com/snake3210/universal-exam-review-builder-skill.git "$HOME/.gemini/config/skills/universal-exam-review-builder"
```
