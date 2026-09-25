# Financial Report — 股票交易訊號燈

以布林通道(Bollinger Bands)為核心的美股訊號燈與回測工具。

## 核心邏輯

用布林通道的 **%B** 指標判斷股價目前落在通道的哪個位置:

- `%B >= top_threshold`(預設 0.8)→ **接近高點**:提示獲利了結多單、或考慮開/加空單
- `%B <= bottom_threshold`(預設 0.2)→ **接近底部**:提示回補空單、或考慮做多

`%B = 1.0` 代表股價正好貼齊上軌,`%B = 0.0` 代表正好貼齊下軌;超過 1 或低於 0 代表已經突破軌道。

這是**均值回歸(mean reversion)** 邏輯:賭股價在通道內震盪、極端後會拉回。這套邏輯在盤整震盪的股票上表現較好,但遇到強趨勢股(單邊噴出或崩跌)時容易連續虧損,所以**先回測驗證有效性,是正確的第一步**。

## 專案結構

```
signal_light/
  data.py        # 透過 yfinance 抓美股歷史資料(或讀本地 CSV)
  indicators.py  # 布林通道 + %B 計算
  signals.py     # 依 %B 門檻分類 near_top / near_bottom / none
  backtest.py    # 進出場模擬引擎 + 績效指標
  plot.py        # 價格圖(含訊號標記)與權益曲線圖
  cli.py         # 命令列入口
tests/           # 用合成資料驗證指標、訊號、回測邏輯是否正確
```

## 安裝

```bash
pip install -r requirements.txt
```

## 使用方式

```bash
# 回測 AAPL 近 2 年資料,並把圖存到 charts/ 資料夾
python -m signal_light.cli --ticker AAPL --period 2y --plot charts

# 自訂布林通道參數與訊號門檻
python -m signal_light.cli --ticker TSLA --period 3y \
  --window 20 --num-std 2 --top-threshold 0.85 --bottom-threshold 0.15

# 只做多、不做空
python -m signal_light.cli --ticker MSFT --period 2y --no-short

# 用本地 CSV(欄位需含 Date, Close)離線測試
python -m signal_light.cli --ticker TEST --csv data/aapl.csv
```

輸出範例:

```
=== AAPL Bollinger Band Signal Light Backtest ===
Trades:            18
Win rate:          61.1%
Avg trade return:  2.34%
Total return:      15.82%
Sharpe ratio:      0.87
Max drawdown:      -9.4%
```

## 執行測試

```bash
pytest tests/ -v
```

> 本開發環境的雲端沙盒基於組織網路政策封鎖了 Yahoo Finance 的連線,所以測試全部用合成的震盪價格資料驗證邏輯正確性,沒有依賴即時連線。在你自己的電腦或伺服器上執行 `--ticker` 抓即時資料應該不會有這個限制。

## 目前的限制 / 下一步

- **只用布林通道單一指標**:之後可以加 RSI、KD 做多指標確認,減少假訊號。
- **一次只持有一個部位**(多單或空單擇一,不會加碼疊倉),符合你「獲利了結」「加空單時先出清舊多單」的直覺邏輯;如果之後想做真正的分批加碼,需要擴充 `backtest.py` 的部位管理。
- **尚未接上即時通知**:回測驗證出有效的參數組合後,下一步是寫一支排程腳本,定期抓最新股價、計算訊號,一旦觸發 near_top / near_bottom 就用 LINE Notify 推播給你。
- **回測是簡化模型**:用收盤價成交、無滑價與手續費假設,實際交易表現會比回測差,正式上線前建議加上合理的手續費/滑價估算。
