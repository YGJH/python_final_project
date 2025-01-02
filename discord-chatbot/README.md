# Discord Chatbot

這個專案是一個 Discord 機器人，旨在提供基於提示的回應功能，並與用戶進行互動。

## 專案結構

```
discord-chatbot
├── src
│   ├── bot.py               # Discord 機器人的主要入口點
│   ├── llm_jable_master.py   # 與 LLM 互動的功能
│   ├── controllers
│   │   └── index.ts         # 處理機器人指令的邏輯
│   ├── routes
│   │   └── index.ts         # 設置機器人的路由
│   └── types
│       └── index.ts         # 定義機器人訊息和指令的結構
├── package.json              # npm 的配置檔
├── tsconfig.json             # TypeScript 的配置檔
└── README.md                 # 專案文檔
```

## 安裝與使用

1. 確保已安裝 Python 和 Node.js。
2. 克隆此專案到本地：
   ```
   git clone <repository-url>
   ```
3. 進入專案目錄：
   ```
   cd discord-chatbot
   ```
4. 安裝 Python 依賴：
   ```
   pip install -r requirements.txt
   ```
5. 安裝 Node.js 依賴：
   ```
   npm install
   ```
6. 配置 Discord 機器人令牌，並在 `src/bot.py` 中設置。
7. 啟動機器人：
   ```
   python src/bot.py
   ```

## 功能

- 接收來自 Discord 的訊息並回應。
- 處理用戶指令並提供相應的功能。

## 貢獻

歡迎任何形式的貢獻！請提交問題或拉取請求。