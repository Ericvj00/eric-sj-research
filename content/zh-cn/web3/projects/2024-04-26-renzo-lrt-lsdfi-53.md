---
title: "Renzo：为什么说Renzo表层业务是LRT，底层业务是LSDFi？丨新币挖矿第53期"
content_id: "106"
date: "2024-04-26T15:39:22+08:00"
slug: "2024-04-26-renzo-lrt-lsdfi-53"
category: "Web3"
subcategory: "项目分析"
content_type: "project-analysis"
category_key: "project"
category_label: "项目分析"
categories:
  - "项目分析"
featured: false
status: "已发布"
draft: false
author: "Eric SJ"
source: "Binance Square"
source_url: "https://www.binance.com/zh-CN/square/post/7283692655401"
cover: "/images/covers/2024-04-26-renzo-lrt-lsdfi-53-cover-placeholder.png"
seo_geo_status: "处理失败"
summary: ""
description: ""
key_points: []
seo_keywords: []
tags: []
faq: []
---

## 正文

本次新币挖矿Renzo #REZ 协议的前端是我们普遍理解中的再质押路径：**stETH>ezETH**，后端则是一篮子的再质押收益策略聚合~

**本文重点讲几件事：**

Renzo的前后端路径演示

**为什么说Renzo的表层业务是LRT，而底层业务却是LSDFi❓**

通证经济与TVL情况

**先一句话概括Renzo的核心逻辑🔻**

将使用了EigenLayer服务的项目做成后端的收益集成，通过这种方式给再质押标的带来更多的收益。

### **1.Renzo的前后端演示**

下图是Renzo Protocol的前后端路径演示，前端主要是用户对于Renzo交互过程中基础的质押/再质押资产发送以及Renzo协议对用户的反馈，这个前端路径实际上和市面上的原生质押以及再质押协议相似。

![文章配图](/images/posts/2024-04-26-renzo-lrt-lsdfi-53-image-01.jpg)

**协议的重点在于后端的实现**，即通过将使用了EigenLayer再质押服务的项目打包在一个策略池子里，用户向Renzo发送的可质押资产，**将会进入这个策略池子，而这个池子里的多个协议也会因为Renzo共享的流动性反哺Renzo协议。**

随着未来使用EigenLayer再质押服务的项目越来越多，Renzo未来可实现的收益策略组合也将更丰富。

但是，这里有个需要延伸一下的点就是：**策略的丰富只能说明其未来带来的产品丰富程度，不意味着收益率会嵌套增加。**

买过指数基金的朋友都知道，这个指数里面的份额，如果这个标的占比多了，那个标的占比就会少，放在Renzo里面其实也是一样的逻辑，只是说策略的丰富程度，有可能会**偶尔**带有比较高溢价的收益 。

### 2.**为什么说Renzo的表层业务是LRT，而底层业务却是LSDFi**❓

至于我为什么说其实底层是LSDFi呢，就是因为本质上这个协议做的是服务承包的业务。承包的是各个AVS的上游市场，EigenLayer的下游市场，也就是介于AVS和EigenLayer之间的一个中间协议。

**其本身对于再质押安全性共享的内核，是放置于中间环节，最终输出的结果是用户资产收益率。**

因为除了协议本身提供的积分奖励之外， ezETH还可以因为给各个AVS（即各个使用了EigenLayer的项目）提供流动性与安全性，以此来获得除再质押之外的AVS外部奖励。

**因此这也是我为什么说随着未来AVS池子的增加，有可能会偶尔带有比较高溢价的用户收益。**

在我之前有关ETHFI的分析里我就说过，**再质押这件事本身不是什么护城河，利用再质押这个事情去干什么，才是协议差异化护城河的关键。毕竟大家都在切EigenLayer的再质押这条赛道，谁切的有差异化，能更好构建产品护城河，谁就能抢占市场更多的份额**。

### **3.通证经济与TVL情况**🔻

![文章配图](/images/posts/2024-04-26-renzo-lrt-lsdfi-53-image-02.jpg)

REZ的整体代币分布，初始流通的部分大额主要是来自空投活动，特殊项里面本次新币占2.5%，在初期流通中的比例不大。

其代币的释放曲线在一年后才开始相对比较陡峭，团队和机构都有锁仓设计，一年后会开始释放这两个部分的比例
**值得一提的是，31.6%的投资者占比是较大额的**，对应的看到社区的份额则相应减少了，如果我们将生态系统划归到社区阵营，项目方+投资者阵营的份额也在60%以上
也就是说，能在现阶段单纯归属于社区的份额，**仅在15%以内（含新币挖矿）**

![文章配图](/images/posts/2024-04-26-renzo-lrt-lsdfi-53-image-03.jpg)

**除此之外，Renzo在同类型的协议中TVL排第2，仅次于此前同样上线Binance的ETHFI，但Renzo的业务模式的产品及用户范围，会比**$ETHFI **更多 。**
