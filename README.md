# 台指期動能策略研究

結合**市場週期、籌碼收斂與逐步加碼**的台指期動能策略,並以**回測過度擬合檢驗**為核心的實證研究專題。

> **目前狀態:研究設計完成,第 1 層訊號模組已實作,尚未使用真實資料進行實證。**
> 本頁所有「結果」都是研究過程中的設計結論與程式驗證,不是回測績效。

---

## 目錄

1. [專題定位](#一專題定位)
2. [研究過程](#二研究過程)
3. [研究問題與假設](#三研究問題與假設)
4. [系統架構](#四系統架構)
5. [目前成果](#五目前成果)
6. [程式使用方式](#六程式使用方式)
7. [資料需求](#七資料需求)
8. [驗證流程](#八驗證流程)
9. [開發路線圖](#九開發路線圖)
10. [限制與風險](#十限制與風險)
11. [參考文獻](#十一參考文獻)

---

## 一、專題定位

**研究對象**:台灣股價指數期貨(大台、小台、微台),以 0050 為對照。

**核心問題**:實務交易者常用的動能改良方法(判斷大盤狀態、等待籌碼收斂、試單後加碼),在嚴格控制過度擬合之後,統計上是否站得住腳?

**特色**:

1. 以學術上已證實的**時間序列動能**為基礎,檢驗**實務交易方法**的增量價值。
2. **全程控制過度擬合**:記錄所有嘗試,計算 PBO、Deflated Sharpe Ratio,並做多重檢定校正。
3. 使用期交所公布的**大額交易人未沖銷部位**,直接驗證「籌碼集中」假設,不只從量價推論。

---

## 二、研究過程

### 階段 1:動能理論文獻

| 文獻 | 核心發現 | 在本專題的用途 |
|---|---|---|
| Moskowitz, Ooi & Pedersen (2012), *JFE* | 58 個期貨商品過去 12 個月報酬能預測下個月報酬;分散化投組 Sharpe > 1;在極端市場表現最好 | 時間序列動能、波動度調整、比較基準 |
| Goulding, Harvey & Mazzoleni (2023), *JFE* | 用 12 個月與 1 個月動能定義 Bull、Correction、Bear、Rebound 四種市場週期;快慢訊號混合的 Sharpe 最高 | 大盤狀態判斷(H1 的基礎) |
| Martin (2023), arXiv | 動能策略的正偏態來自「賺錢時部位變大」的設計;單純 ±1 訊號會讓偏態歸零 | 逐步加碼的理論依據(H3) |
| Avellaneda & Lee (2010), *Quantitative Finance* | 去除因子後的個股殘差有短期均值回歸;高量的價格變動代表真實資訊 | 突破必須帶量才算確認 |
| Sim & Kim (2022), *Finance Research Letters* | 剔除報酬過於顯眼的極端股票,可改善截面動能 | 對照用 |
| Karki & Khadka (2024), *NJMR* | 動能文獻的書目計量回顧 | 時間序列與截面動能的分類 |

**整合後的觀察**:

- 動能與均值回歸取決於**時間尺度**:月的尺度看動能,日的尺度看因子殘差的回歸。
- 幾篇論文的共同做法是:**訊號不明確時不下注或縮小部位**(Goulding 的 MED、Martin 的死區、Avellaneda 的進場門檻)。
- 實務方法(Minervini 的趨勢樣板、四階段分析、VCP)和學術研究**高度對應**,但缺乏系統性回測,這是本專題可以補上的地方。

### 階段 2:實務方法整理

整理 Minervini《超級績效》1、3 的筆記,並對照學術研究:

| 實務規則 | 學術對應 |
|---|---|
| 趨勢樣板:股價 > 200MA、200MA 上升、相對強度 ≥ 70 | 時間序列動能 + 截面動能 |
| 四階段分析 | Goulding 的四種市場週期 |
| 符合預期逐步加碼、不向下攤平 | Martin 的正偏態理論 |
| VCP:量縮整理後帶量突破 | Avellaneda 的成交量發現 |
| 環境困難時降低曝險 | Goulding 的波動擇時 |

### 階段 3:策略設計

1. 設計四層架構(見[第四節](#四系統架構))。
2. 針對兩個核心問題提出量化方法:
   - **大盤區間整理時如何判斷方向**:區間內不預測,只用 5 類領先指標計算方向分數,等帶量突破才進場。
   - **籌碼收斂如何量化**:波動收縮 + 量縮 + 大戶淨部位,而且可以用期交所資料直接驗證。
3. 設計逐步加碼規則:總風險預算固定,加碼前先上移停損,部位呈「小 → 大 → 小」。
4. **研究範圍收斂到大盤商品**(台指期),讓資料和分析更乾淨。

### 階段 4:回撤與風險文獻

| 文獻 | 用途 |
|---|---|
| Chekhlov, Uryasev & Zabarankin (2005), *IJTAF* | **條件回撤 CDD**:比最大回撤穩定;只用一條歷史路徑做最佳化,會高估 20–30% 的風險調整後報酬 |
| Uyar (2026),工作論文 | 回撤領先指標:信用利差、NFCI、VIX;6 個月期樣本外 AUC 0.737 |
| Battistelli (2024) / Proietti (2024) | 固定窗口回撤與 HAR 預測,用來設定停損寬度 |
| Qu, Mei & Doray (2022), *MLWA* | 尾部斜率偵測極端事件(事後偵測,不是預測) |
| Xu,高中研究 | 最大回撤主要取決於波動度、漂移、期間;同時是「用同期資料預測」的反面教材 |

### 階段 5:過度擬合控制文獻

| 文獻 | 用途 |
|---|---|
| Bailey & López de Prado (2014), *JPM* | **Deflated Sharpe Ratio**:扣除多重嘗試與非常態分布的影響 |
| Bailey, Borwein, López de Prado & Zhu (2017), *J. Computational Finance* | **PBO**:用 CSCV 估計挑選參數的流程有多大機率是在擬合雜訊 |
| Harvey, Liu & Zhu (2016), *RFS* | 多重檢定:新發現的 t 值門檻應提高到約 3.0 |

**重要修正**:單純保留一段資料做驗證(holdout)無法控制嘗試次數,因此驗證流程改為 holdout 加上 DSR、PBO 與完整的嘗試紀錄。

---

## 三、研究問題與假設

| 編號 | 假設 | 檢驗方法 |
|---|---|---|
| **H1** | 大盤方向分數能預測區間整理後的突破方向 | 事件研究 |
| **H2** | 波動收縮、量縮,加上大戶淨部位增加後的突破,成功率較高 | 事件研究 |
| **H3** | 試單後確認再加碼,比一次滿倉的風險調整後報酬更好 | 同一組訊號下比較部位規則 |
| **H4** | 加入回撤風險指標與波動度調整,可以降低 CDD 而不明顯降低 Sharpe | 有無風險疊加層的比較 |

**比較基準**:買進持有加權報酬指數、MOP 的 12 個月時間序列動能、Goulding 的 MED 策略。

**顯著性標準**:四個假設一起做 Holm 或 BHY 校正;有理論依據的假設,t 值至少 2.8–3.0。

---

## 四、系統架構

```
┌──────────────────────────────────────────────────────┐
│ 第 1 層  大盤狀態與方向                    【已實作】      │
│   市場週期 → 區間判斷 → 方向分數(5 分項)→ 突破確認         │
│   輸出:行動建議、多空曝險上限                             │
├──────────────────────────────────────────────────────┤
│ 第 2 層  籌碼收斂(大盤層級)                【規劃中】      │
│   波動收縮 + 量縮 + 大額交易人與法人淨部位                  │
├──────────────────────────────────────────────────────┤
│ 第 3 層  部位與加碼                        【規劃中】      │
│   試單 → 確認後加碼 → 移動停損                            │
│   口數 = 風險預算 ÷ (停損點數 × 每點價值)                  │
├──────────────────────────────────────────────────────┤
│ 第 4 層  風險疊加                          【規劃中】      │
│   波動度調整、回撤風險指標、連續虧損減碼、CDD 上限           │
└──────────────────────────────────────────────────────┘
                 ↓ 所有結果都要經過驗證層
┌──────────────────────────────────────────────────────┐
│ 驗證層  嘗試紀錄 → PBO → DSR → 多重檢定 → 樣本外驗證  【規劃中】│
└──────────────────────────────────────────────────────┘
```

### 第 1 層的邏輯

**1. 市場週期**(Goulding et al. 2023)

| 狀態 | 過去 12 個月報酬 | 過去 1 個月報酬 |
|---|---|---|
| Bull | ≥ 0 | ≥ 0 |
| Correction | ≥ 0 | < 0 |
| Bear | < 0 | < 0 |
| Rebound | < 0 | ≥ 0 |

**2. 區間整理判斷**:以下 5 個條件符合 3 個以上即判定為區間整理。

- 200 日均線的 20 日變化率絕對值 < 1%
- 60 日最高價 ÷ 最低價 − 1 < 10%
- 布林通道寬度的一年百分位 < 30%
- ADX(14) < 20
- 市場週期為 Correction 或 Rebound

**3. 方向分數**:5 類分項各投 −1、0、+1,換算成 −5 到 +5。

| 分項 | 指標 | 需要的資料 |
|---|---|---|
| 市場廣度 | 站上 50MA 的股票比例變化、52 週新高減新低 | 成分股收盤價 |
| 領導股 | 符合趨勢樣板的股票比例變化 | 成分股收盤價 |
| 量能不對稱 | 上漲日總量 ÷ 下跌日總量 | 指數成交量 |
| 法人籌碼 | 外資期貨淨部位、三大法人買賣超、融資餘額(下降偏多) | 籌碼資料 |
| 跨市場 | 金融類股與費半所處階段、新台幣升貶 | 國際資料 |

- 缺資料的分項會被排除,分數依可用分項數換算。可用分項少於 2 個時不給方向。
- 做多門檻 +3、做空門檻 −4。做空門檻較嚴格,因為 Goulding 發現 Correction 後有 61% 的機率回到 Bull。

**4. 突破確認**:收盤價突破 60 日區間 1% 以上,而且成交量 > 50 日均量的 1.5 倍。突破後 3 天內跌回區間判定為假突破。

**5. 曝險上限**

| 狀態 | 多方曝險上限 |
|---|---|
| 確認做多突破後持有中 | 100% |
| Bull 且非區間 | 100% |
| 區間整理、Correction、Rebound | 50% |
| Bear | 0% |

空方只在確認做空突破後開放,上限 50%。

---

## 五、目前成果

### 已完成

| 項目 | 說明 |
|---|---|
| 文獻閱讀與整合 | 14 篇論文、2 份實務筆記 |
| 研究設計 | 四個假設、四層架構、驗證流程 |
| 第 1 層程式 | 技術指標、趨勢樣板、市場週期、區間判斷、方向分數、突破狀態機 |

### 程式驗證(模擬資料)

用模擬的指數與 30 檔成分股資料執行完整流程:

- 全部 5 個分項都能正常計算,輸出行動建議與曝險上限。
- **前視偏誤檢查通過**:把資料截斷在第 500 天重新計算,前 500 天的所有欄位和使用完整資料時完全相同,代表訊號沒有用到未來資料。

> 這些只是程式正確性的檢查。模擬資料的訊號分布沒有任何經濟意義。

### 尚未完成

- 正式的測試檔(pytest)
- 真實資料串接
- 第 2–4 層與驗證層
- 任何實證結果

---

## 六、程式使用方式

### 安裝

```bash
pip install -r requirements.txt
```

需要 Python 3.10 以上。

### 專案結構

```
momentum_strategy/
├── indicators.py       # 均線、ADX、布林通道寬度、滾動百分位、投票工具
├── trend_template.py   # Minervini 趨勢樣板 8 條條件
└── market_signal.py    # 第 1 層:市場週期、區間判斷、方向分數、突破狀態機
```

### 範例

```python
import numpy as np
import pandas as pd
from momentum_strategy.market_signal import MarketData, SignalConfig, compute_market_signal

# 指數日資料:必須有 open, high, low, close, volume 欄位,索引為日期
dates = pd.bdate_range("2020-01-01", periods=600)
rng = np.random.default_rng(0)
close = pd.Series(10000 * np.exp(np.cumsum(rng.normal(3e-4, 0.01, 600))), index=dates)
index = pd.DataFrame({"open": close, "high": close * 1.005, "low": close * 0.995,
                      "close": close, "volume": rng.lognormal(14, 0.2, 600)}, index=dates)

signal = compute_market_signal(MarketData(index=index), SignalConfig())
print(signal[["market_state", "is_range", "direction_score", "action", "long_cap"]].tail())
```

這個範例只提供指數資料,所以方向分數只有「量能不對稱」1 個分項,低於最少 2 個的門檻,`direction_score` 會是 NaN。要得到完整的方向分數,請一併提供:

```python
MarketData(
    index=index,                    # 必要:加權指數 OHLCV
    constituents_close=...,         # 日期 x 股票代號的收盤價(市場廣度、領導股)
    foreign_futures_net_oi=...,     # 外資台指期未平倉淨口數
    institutional_net_buy=...,      # 三大法人現貨買賣超
    margin_balance=...,             # 融資餘額
    financial_index=...,            # 金融類股指數
    sox=...,                        # 費城半導體指數
    usdtwd=...,                     # 美元兌新台幣
)
```

所有門檻都集中在 `SignalConfig`,可以在建立時覆寫,例如 `SignalConfig(long_threshold=2.0)`。

### 時間慣例(重要)

**日期 t 的訊號使用 t 日收盤後(含美股 t 日收盤)已公布的資料,只能用在 t+1 開盤之後的交易。**回測時必須用 t+1 之後的報酬,否則會有前視偏誤。

### 主要輸出欄位

| 欄位 | 說明 |
|---|---|
| `market_state` | Bull、Correction、Bear、Rebound |
| `is_range` | 是否處於區間整理 |
| `comp_breadth` ... `comp_cross` | 各分項投票(−1、0、+1,缺資料為 NaN) |
| `direction_score` | 方向分數(−5 到 +5) |
| `bias` | long、short、neutral |
| `event` | 當日事件:做多確認、假突破出場等 |
| `action` | 行動建議 |
| `long_cap` / `short_cap` | 多方 / 空方曝險上限 |

---

## 七、資料需求

| 資料 | 頻率 | 來源 | 用途 |
|---|---|---|---|
| 加權指數、加權報酬指數 | 日 | 證交所、FinMind | 訊號計算 |
| 台指期各月合約 | 日 | 期交所、FinMind | 損益、連續序列 |
| 上市個股收盤價(含已下市) | 日 | FinMind | 市場廣度、領導股 |
| 三大法人期貨未平倉、**大額交易人未沖銷部位** | 日 | 期交所 | 籌碼分項、H2 |
| 三大法人現貨買賣超、融資融券 | 日 | 證交所 | 籌碼分項 |
| 選擇權 Put/Call ratio | 日 | 期交所 | 情緒指標 |
| 高收益債利差(BAMLH0A0HYM2)、NFCI、VIX(VIXCLS) | 日/週 | FRED | H4 回撤風險 |
| 費半、金融類股、新台幣、國際指數 | 日 | yfinance 等 | 跨市場分項、樣本外驗證 |

**處理原則**:記錄每筆資料的公布時間;標準化只用過去的資料;用報酬指數計算訊號,避免除息造成假下跌;台指期要處理轉倉與夏季逆價差。

---

## 八、驗證流程

| 步驟 | 內容 | 依據 |
|---|---|---|
| 0 | 看結果之前,先寫下假設與參數網格並凍結 | Harvey et al. (2016) |
| 1 | 跑完網格所有參數,存下每日損益矩陣,記錄每一次嘗試 | 三篇過度擬合論文 |
| 2 | 用 CSCV 計算 PBO、績效衰退斜率、樣本外虧損機率 | Bailey et al. (2017) |
| 3 | 以有效嘗試次數計算 Deflated Sharpe Ratio | Bailey & López de Prado (2014) |
| 4 | H1–H4 做 Holm 或 BHY 校正 | Harvey et al. (2016) |
| 5 | 最終測試期間只用一次,並用國際指數驗證 | 樣本外驗證 |
| 6 | 報告所有數字:嘗試次數、PBO、DSR、校正後 p 值、CDD | 可重現性 |

**評估指標**:年化報酬、alpha、Sharpe、DSR、MaxDD、CDD(α = 0.8)、偏態、勝率、PBO、換手率、交易成本佔比。

**交易成本**:台指期手續費、期交稅(十萬分之二)、滑價、轉倉成本。

---

## 九、開發路線圖

| 階段 | 內容 | 狀態 |
|---|---|---|
| 0 | 研究設計凍結:假設、參數網格、資料切分、嘗試紀錄表 | ⬜ |
| 1 | 資料管線:下載、台指期連續序列、品質檢查 | ⬜ |
| 2 | 驗證工具:DSR、PBO、Holm/BHY、CDD、區塊 bootstrap | ⬜ |
| 3 | 訊號與策略:第 1 層補齊籌碼分項、第 2–4 層、回測引擎 | 🟡 第 1 層已完成 |
| 4 | 實證檢驗:H1–H4 | ⬜ |
| 5 | App 雛形:Streamlit 儀表板 | ⬜ |
| 6 | 撰寫報告與簡報 | ⬜ |

**下一步**:完成階段 0 的研究設計凍結,同時實作階段 2 的驗證工具(不需要外部資料,可以用論文的數值例子驗證程式正確性)。

---

## 十、限制與風險

| 風險 | 對策 |
|---|---|
| 結果可能不顯著 | 不顯著本身也是有價值的結論;重點是方法嚴謹 |
| 區間突破事件太少,統計檢定力不足 | 合併多個台股與國際指數檢驗 |
| 過度擬合 | 先凍結設計、完整嘗試紀錄、PBO、DSR |
| 大額交易人資料的歷史長度有限 | 必要時縮短 H2 的樣本期間 |
| 趨勢策略在 2009 年後表現衰退 | 子期間分析並如實報告 |
| 開發環境無法連線到部分資料來源 | 在本機下載資料,或在環境網路設定中允許這些網域 |

---

## 十一、參考文獻

**動能**
- Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). Time series momentum. *Journal of Financial Economics*, 104(2), 228–250.
- Goulding, C. L., Harvey, C. R., & Mazzoleni, M. G. (2023). Momentum turning points. *Journal of Financial Economics*, 149, 378–406.
- Martin, R. J. (2023). Design and analysis of momentum trading strategies. arXiv:2101.01006.
- Avellaneda, M., & Lee, J.-H. (2010). Statistical arbitrage in the US equities market. *Quantitative Finance*, 10(7), 761–782.
- Sim, M., & Kim, H.-E. (2022). Salience theory and enhancing momentum profits. *Finance Research Letters*, 50, 103274.
- Karki, D., & Khadka, P. B. (2024). Momentum investment strategies across time and trends: A review and preview. *Nepal Journal of Multidisciplinary Research*, 7(1), 62–83.

**回撤與風險**
- Chekhlov, A., Uryasev, S., & Zabarankin, M. (2005). Drawdown measure in portfolio optimization. *International Journal of Theoretical and Applied Finance*, 8(1), 13–58.
- Uyar, A. (2026). Leading indicators of S&P 500 drawdowns: A horizon-specific macro-financial framework. Working paper.
- Battistelli, R. (2024). Drawdown analysis: Performance, risk and prediction of financial and technology sectors. Master's thesis, University of Gothenburg.
- Qu, T., Mei, K. W., & Doray, A. (2022). A simple method to detect extreme events from financial time series data. *Machine Learning with Applications*, 10, 100415.
- Xu, J. Estimating the universal maximum drawdown function using deep learning. Student research paper.

**過度擬合與多重檢定**
- Bailey, D. H., & López de Prado, M. (2014). The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting and non-normality. *Journal of Portfolio Management*, 40(5), 94–107.
- Bailey, D. H., Borwein, J. M., López de Prado, M., & Zhu, Q. J. (2017). The probability of backtest overfitting. *Journal of Computational Finance*, 20(4), 39–69.
- Harvey, C. R., Liu, Y., & Zhu, H. (2016). …and the cross-section of expected returns. *Review of Financial Studies*, 29(1), 5–68.

**實務**
- Minervini, M. 《超級績效》系列。

---

## 授權

見 [LICENSE](LICENSE)。
