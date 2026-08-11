+++
title = "自用工具"
seo_title = "自用工具箱：交易、支付与研究数据工具"
description = "Eric SJ 自用与研究工具箱，汇集稳定币美股、加密交易、支付、网络连接、学习资源及链上研究数据工具，并提供推荐工具的简明上手指南。"
tool_hub = true
section_label = "工具箱"
hero_title = "自用工具"
hero_description = "Eric SJ 长期使用的自用/研究工具箱，包含交易平台、稳定币支付工具、链上数据网站、RWA数据和学习资源。"
tool_filters = ["交易平台", "数据指标", "其他工具"]
all_tools_label = "全部工具"
recommended_label = "推荐工具"
research_label = "研究数据工具"
research_description = "这些工具主要用于 Eric SJ 日常研究、数据查询和行业分析。"
visit_default_label = "访问网站 →"
expand_label = "展开"
collapse_label = "收起"
scenes_label = "适合场景"
features_label = "特点"
risk_label = "风险提示"
usage_label = "用途"
suitable_label = "适合"
empty_label = "目前分类暂无工具。"
recommended_intro = "推荐工具用于解决交易、支付、网络连接与学习资源获取等具体问题。先用卡片快速判断是否适合，再进入上手教程核对流程、限制和风险。"
intent_label = "我想解决什么"
tutorial_label = "查看上手教程"
recommended_risk = "涉及交易、证券、数字资产或支付服务时，请在注册前确认所在地区的资格限制、KYC、费用、资产规则与服务主体；本文仅提供工具信息，不构成投资建议。"

[[tool_intents]]
label = "使用稳定币配置美股"
slug = "bit-us-stocks"

[[tool_intents]]
label = "进行加密资产交易"
slug = "binance"

[[tool_intents]]
label = "使用稳定币支付"
slug = "pokepay"

[[tool_intents]]
label = "解决多设备网络连接"
slug = "kuli-vpn"

[[tool_intents]]
label = "查找视频学习资源"
slug = "youxuan-video"

[[recommended_faq]]
question = "如何选择推荐工具？"
answer = "先从自己要解决的问题出发：稳定币配置美股对应 BIT，加密资产现货交易对应 Binance，稳定币支付对应 PokePay，海外网络连接对应 Kuli云 VPN，视频学习资源对应优选视频网。"

[[recommended_faq]]
question = "推荐工具和研究数据工具有什么区别？"
answer = "推荐工具提供上手教程与外部服务入口；研究数据工具只用于快速访问公开的数据查询与研究平台。"

[[recommended_faq]]
question = "使用前需要核对什么？"
answer = "涉及账户、交易或支付的工具，应先核对地区资格、KYC、费用、充值与提现规则、支持资产及服务条款；动态规则以工具官方当前页面为准。"

[[recommended_tools]]
title = "BIT"
slug = "bit-us-stocks"
category = "交易平台"
tags = ["交易平台", "美股", "稳定币"]
description = "使用 USDT / USDC 为美股账户入金的交易入口，适合已持有稳定币并希望配置美国上市证券的用户。"
scenes = [
  "稳定币买美股",
  "美股资产配置",
  "USDT / USDC 入金",
]
features = [
  "BIT 为 Matrixport 更新后的品牌名称",
  "提供美股账户申请与稳定币入金路径",
  "交易前需确认 KYC、费用、地区资格与证券账户规则",
]
caution = "证券交易存在亏损风险，服务资格与产品范围以 BIT 当前规则为准。"
button_label = "使用稳定币进行美股交易 →"
url = "https://invest.matrixport.com/newRegister/cn?invite_code=ERICSJ"
sponsored_status = "unknown"

[[recommended_tools]]
title = "Kuli云 VPN"
slug = "kuli-vpn"
category = "其他工具"
tags = ["网络工具", "AI", "海外研究"]
description = "用于访问海外网站与在线服务的网络连接工具，具体节点、套餐和客户端以服务后台为准。"
scenes = [
  "海外研究",
  "访问 AI 工具",
  "浏览海外网站",
]
features = [
  "注册后可查看当前套餐与节点",
  "按照后台说明配置兼容客户端",
  "购买前应确认设备兼容性与流量限制",
]
caution = "网络可用性受地区、设备和服务状态影响，不对速度、隐私或持续可用性作保证。"
button_label = "开始使用 Kuli云 VPN →"
url = "https://kuli1.kuli-online.guru/#/register?code=5jTBMaeF"
sponsored_status = "unknown"

[[recommended_tools]]
title = "Binance"
slug = "binance"
category = "交易平台"
tags = ["交易平台", "加密交易", "Web3"]
description = "提供加密资产充值、提现与现货交易等基础账户功能的平台，适合需要集中管理和交易加密资产的用户。"
scenes = [
  "BTC / ETH 现货交易",
  "加密资产充值与提现",
  "基础账户管理",
]
features_title = "为什么推荐"
features = [
  "现货界面支持市价单与限价单等常用订单类型",
  "充值方式与可用功能会因地区而异",
  "提币前必须核对资产、地址和区块链网络",
]
caution = "并非所有地区都可使用全部产品，注册与交易前应核对当地资格和平台当前条款。"
button_label = "注册 Binance →"
url = "https://www.bsmkweb.cc/register?ref=SJSJSJSJ"
sponsored_status = "unknown"

[[recommended_tools]]
title = "PokePay U卡"
slug = "pokepay"
category = "交易平台"
tags = ["稳定币", "支付", "U卡"]
description = "提供虚拟卡与实体卡申请、加密资产充值和消费入口的支付工具，实际可用范围取决于账户资格与当前产品。"
scenes = [
  "海外消费",
  "线上订阅与支付",
  "加密资产充值后消费",
]
features = [
  "官方页面列出虚拟卡与实体卡",
  "申请需要注册、充值、完成 KYC 并激活卡片",
  "卡类型、费用、资产与地区规则可能变化",
]
caution = "申请前请在官方页面核对卡类型、费用、支持地区、充值资产和退款处理规则。"
button_label = "申请 PokePay →"
url = "https://app.pokepay.cc/pages/invitation/regist?r=537547"
sponsored_status = "unknown"

[[recommended_tools]]
title = "优选视频网"
slug = "youxuan-video"
category = "其他工具"
tags = ["学习资源", "AI", "技能提升"]
description = "聚合讲座、培训课程与下载资料的学习资源网站，适合按主题检索资料并在购买前核对资源说明。"
coverage_title = "覆盖"
coverage = [
  "编程",
  "AI",
  "商业",
  "投资",
  "技能提升",
  "...",
]
scenes_title = "适合"
scenes = [
  "想系统学习新领域的用户",
  "希望持续提升专业能力的用户",
]
caution = "资源授权、交付、会员与售后信息需以网站当前说明为准，购买前应自行确认。"
button_label = "访问优选视频网 →"
url = "http://m.youxuan68.com/users/reg.asp?action=apply&yhh=30426"
sponsored_status = "unknown"

[[research_tools]]
title = "RootData"
category = "数据指标"
tags = ["Web3项目", "融资数据", "早期项目"]
description = "Web3项目研究数据库。"
usage = "查询项目融资信息、投资机构、团队背景和生态关系。"
suitable = [
  "发现早期项目",
  "研究行业趋势",
]
url = "https://rootdata.com/"

[[research_tools]]
title = "CoinGlass"
category = "数据指标"
tags = ["衍生品", "资金费率", "ETF"]
description = "加密市场衍生品数据平台。"
usage = "查询资金费率、爆仓数据、持仓变化和ETF资金流。"
suitable = [
  "市场情绪分析",
  "交易辅助",
]
url = "https://coinglass.com/"

[[research_tools]]
title = "DeFiLlama"
category = "数据指标"
tags = ["DeFi", "TVL", "协议收入"]
description = "DeFi数据聚合平台。"
usage = "查询TVL、协议收入、链生态排名和稳定币数据。"
suitable = [
  "研究DeFi生态",
  "分析行业趋势",
]
url = "https://defillama.com/"

[[research_tools]]
title = "SoSoValue"
category = "数据指标"
tags = ["ETF", "市场数据", "周期观察"]
description = "加密市场综合数据平台。"
usage = "查询ETF资金流、市场数据和行业趋势。"
suitable = [
  "追踪机构资金变化",
  "观察市场周期",
]
url = "https://sosovalue.com/zh/assets/etf/"

[[research_tools]]
title = "RWA.xyz"
category = "数据指标"
tags = ["RWA", "链上资产", "机构参与"]
description = "RWA数据分析平台。"
usage = "查询现实世界资产规模、链上资产发行和机构参与情况。"
suitable = [
  "研究RWA行业发展趋势",
]
url = "https://app.rwa.xyz/"
+++
