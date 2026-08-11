+++
title = "自用工具"
seo_title = "自用工具箱：交易、支付與研究數據工具"
description = "Eric SJ 自用與研究工具箱，整理穩定幣美股、加密交易、支付、網路連線、學習資源及鏈上研究數據工具，並提供推薦工具的簡明上手指南。"
tool_hub = true
section_label = "工具箱"
hero_title = "自用工具"
hero_description = "Eric SJ 長期使用的自用/研究工具箱，包含交易平台、穩定幣支付工具、鏈上數據網站、RWA數據和學習資源。"
tool_filters = ["交易平台", "數據指標", "其他工具"]
all_tools_label = "全部工具"
recommended_label = "推薦工具"
research_label = "研究數據工具"
research_description = "這些工具主要用於 Eric SJ 日常研究、數據查詢和行業分析。"
visit_default_label = "訪問網站 →"
expand_label = "展開"
collapse_label = "收起"
scenes_label = "適合場景"
features_label = "特點"
risk_label = "風險提示"
usage_label = "用途"
suitable_label = "適合"
empty_label = "目前分類暫無工具。"
recommended_intro = "推薦工具用來解決交易、支付、網路連線與學習資源取得等具體問題。先用卡片快速判斷是否適合，再進入上手教學核對流程、限制與風險。"
intent_label = "我想解決什麼"
tutorial_label = "查看上手教學"
recommended_risk = "涉及交易、證券、數位資產或支付服務時，請在註冊前確認所在地區的資格限制、KYC、費用、資產規則與服務主體；本文僅提供工具資訊，不構成投資建議。"

[[tool_intents]]
label = "使用穩定幣配置美股"
slug = "bit-us-stocks"

[[tool_intents]]
label = "進行加密資產交易"
slug = "binance"

[[tool_intents]]
label = "使用穩定幣支付"
slug = "pokepay"

[[tool_intents]]
label = "解決多裝置網路連線"
slug = "kuli-vpn"

[[tool_intents]]
label = "查找影片學習資源"
slug = "youxuan-video"

[[recommended_faq]]
question = "如何選擇推薦工具？"
answer = "先從自己要解決的問題出發：穩定幣配置美股對應 BIT，加密資產現貨交易對應 Binance，穩定幣支付對應 PokePay，海外網路連線對應 Kuli雲 VPN，影片學習資源對應優選視頻網。"

[[recommended_faq]]
question = "推薦工具和研究數據工具有什麼不同？"
answer = "推薦工具提供上手教學與外部服務入口；研究數據工具只用於快速存取公開的數據查詢與研究平台。"

[[recommended_faq]]
question = "使用前需要核對什麼？"
answer = "涉及帳戶、交易或支付的工具，應先核對地區資格、KYC、費用、充值與提領規則、支援資產及服務條款；動態規則以工具官方目前頁面為準。"

[[recommended_tools]]
title = "BIT"
slug = "bit-us-stocks"
category = "交易平台"
tags = ["交易平台", "美股", "穩定幣"]
description = "使用 USDT / USDC 為美股帳戶入金的交易入口，適合已持有穩定幣並希望配置美國上市證券的使用者。"
scenes = [
  "穩定幣買美股",
  "美股資產配置",
  "USDT / USDC 入金",
]
features = [
  "BIT 為 Matrixport 更新後的品牌名稱",
  "提供美股帳戶申請與穩定幣入金路徑",
  "交易前需確認 KYC、費用、地區資格與證券帳戶規則",
]
caution = "證券交易存在虧損風險，服務資格與產品範圍以 BIT 目前規則為準。"
button_label = "使用穩定幣進行美股交易 →"
url = "https://invest.matrixport.com/newRegister/cn?invite_code=ERICSJ"
sponsored_status = "unknown"

[[recommended_tools]]
title = "Kuli雲 VPN"
slug = "kuli-vpn"
category = "其他工具"
tags = ["網絡工具", "AI", "海外研究"]
description = "用於存取海外網站與線上服務的網路連線工具，具體節點、方案和客戶端以服務後台為準。"
scenes = [
  "海外研究",
  "存取 AI 工具",
  "瀏覽海外網站",
]
features = [
  "註冊後可查看目前方案與節點",
  "依照後台說明設定相容客戶端",
  "購買前應確認裝置相容性與流量限制",
]
caution = "網路可用性受地區、裝置和服務狀態影響，不對速度、隱私或持續可用性作保證。"
button_label = "開始使用 Kuli雲 VPN →"
url = "https://kuli1.kuli-online.guru/#/register?code=5jTBMaeF"
sponsored_status = "unknown"

[[recommended_tools]]
title = "Binance"
slug = "binance"
category = "交易平台"
tags = ["交易平台", "加密交易", "Web3"]
description = "提供加密資產充值、提領與現貨交易等基礎帳戶功能的平台，適合需要集中管理和交易加密資產的使用者。"
scenes = [
  "BTC / ETH 現貨交易",
  "加密資產充值與提領",
  "基礎帳戶管理",
]
features_title = "為什麼推薦"
features = [
  "現貨介面支援市價單與限價單等常用訂單類型",
  "充值方式與可用功能會因地區而異",
  "提幣前必須核對資產、地址和區塊鏈網路",
]
caution = "並非所有地區都可使用全部產品，註冊與交易前應核對當地資格和平台目前條款。"
button_label = "註冊 Binance →"
url = "https://www.bsmkweb.cc/register?ref=SJSJSJSJ"
sponsored_status = "unknown"

[[recommended_tools]]
title = "PokePay U卡"
slug = "pokepay"
category = "交易平台"
tags = ["穩定幣", "支付", "U卡"]
description = "提供虛擬卡與實體卡申請、加密資產充值和消費入口的支付工具，實際可用範圍取決於帳戶資格與目前產品。"
scenes = [
  "海外消費",
  "線上訂閱與支付",
  "加密資產充值後消費",
]
features = [
  "官方頁面列出虛擬卡與實體卡",
  "申請需要註冊、充值、完成 KYC 並啟用卡片",
  "卡片類型、費用、資產與地區規則可能變動",
]
caution = "申請前請在官方頁面核對卡片類型、費用、支援地區、充值資產和退款處理規則。"
button_label = "申請 PokePay →"
url = "https://app.pokepay.cc/pages/invitation/regist?r=537547"
sponsored_status = "unknown"

[[recommended_tools]]
title = "優選視頻網"
slug = "youxuan-video"
category = "其他工具"
tags = ["學習資源", "AI", "技能提升"]
description = "聚合講座、培訓課程與下載資料的學習資源網站，適合按主題搜尋資料並在購買前核對資源說明。"
coverage_title = "覆蓋"
coverage = [
  "編程",
  "AI",
  "商業",
  "投資",
  "技能提升",
  "...",
]
scenes_title = "適合"
scenes = [
  "想系統學習新領域的用戶",
  "希望持續提升專業能力的用戶",
]
caution = "資源授權、交付、會員與售後資訊需以網站目前說明為準，購買前應自行確認。"
button_label = "訪問優選視頻網 →"
url = "http://m.youxuan68.com/users/reg.asp?action=apply&yhh=30426"
sponsored_status = "unknown"

[[research_tools]]
title = "RootData"
category = "數據指標"
tags = ["Web3項目", "融資數據", "早期項目"]
description = "Web3項目研究數據庫。"
usage = "查詢項目融資信息、投資機構、團隊背景和生態關係。"
suitable = [
  "發現早期項目",
  "研究行業趨勢",
]
url = "https://rootdata.com/"

[[research_tools]]
title = "CoinGlass"
category = "數據指標"
tags = ["衍生品", "資金費率", "ETF"]
description = "加密市場衍生品數據平臺。"
usage = "查詢資金費率、爆倉數據、持倉變化和ETF資金流。"
suitable = [
  "市場情緒分析",
  "交易輔助",
]
url = "https://coinglass.com/"

[[research_tools]]
title = "DeFiLlama"
category = "數據指標"
tags = ["DeFi", "TVL", "協議收入"]
description = "DeFi數據聚合平臺。"
usage = "查詢TVL、協議收入、鏈生態排名和穩定幣數據。"
suitable = [
  "研究DeFi生態",
  "分析行業趨勢",
]
url = "https://defillama.com/"

[[research_tools]]
title = "SoSoValue"
category = "數據指標"
tags = ["ETF", "市場數據", "週期觀察"]
description = "加密市場綜合數據平臺。"
usage = "查詢ETF資金流、市場數據和行業趨勢。"
suitable = [
  "追蹤機構資金變化",
  "觀察市場週期",
]
url = "https://sosovalue.com/zh/assets/etf/"

[[research_tools]]
title = "RWA.xyz"
category = "數據指標"
tags = ["RWA", "鏈上資產", "機構參與"]
description = "RWA數據分析平臺。"
usage = "查詢現實世界資產規模、鏈上資產發行和機構參與情況。"
suitable = [
  "研究RWA行業發展趨勢",
]
url = "https://app.rwa.xyz/"
+++
