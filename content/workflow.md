# Eric SJ Research 内容生产工作流

## 文章分类规则

### articles

用于：

- 研究型长文
- 观点文章

推荐路径：

```text
content/zh-cn/articles/
```

### web3

用于：

- 链上研究
- 协议分析
- RWA
- 稳定币
- 基础设施

推荐路径：

```text
content/zh-cn/web3/
```

### stocks

用于：

- 财报
- 公司分析
- 行业研究

推荐路径：

```text
content/zh-cn/stocks/
```

### guides

用于：

- 交易平台教程
- 工具教程
- 投资入门

推荐路径：

```text
content/zh-cn/guides/
```

## Front Matter 如何填写

```toml
+++
title = "文章标题"
date = "2026-07-07T00:00:00+08:00"
lastmod = "2026-07-10T00:00:00+08:00"
author = "Eric SJ"
description = "用于 SEO 的页面描述。"
tags = ["标签1", "标签2"]
categories = ["Web3"]
summary = "一句话总结。"
cover = "/images/covers/example.png"
featured = false
content_type = "web3"
reading_time = ""
source = { name = "数据来源名称", url = "https://example.com" }
updated_note = "本次更新说明。"
disclaimer = "本文仅用于研究和投资者教育，不构成投资建议。"
key_points = [
  "核心观点1",
  "核心观点2",
]
faq = [
  { question = "问题？", answer = "答案。" },
]
related = []
draft = false
+++
```

## 专题页自动归类规则

文章通过 `categories` 自动进入对应专题页。

### Web3

文章推荐放在：

```text
content/zh-cn/web3/
```

分类填写：

```toml
categories = ["Web3", "板块研究"]
categories = ["Web3", "链上财报"]
categories = ["Web3", "项目分析"]
categories = ["Web3", "逻辑拆解"]
```

对应专题页：

```text
/zh-cn/web3/sector/
/zh-cn/web3/onchain-financials/
/zh-cn/web3/projects/
/zh-cn/web3/thesis/
```

### 美股

文章推荐放在：

```text
content/zh-cn/stocks/
```

分类填写：

```toml
categories = ["美股", "财报分析"]
categories = ["美股", "个股研究"]
categories = ["美股", "产业报告"]
```

对应专题页：

```text
/zh-cn/stocks/earnings/
/zh-cn/stocks/company/
/zh-cn/stocks/industry/
```

## content_type 可选值

- `web3`
- `stocks`
- `guides`
- `articles`

## 图片流程

封面图放在：

```text
static/images/covers/
```

图表放在：

```text
static/images/charts/
```

Logo 放在：

```text
static/images/
```

文章封面写法：

```toml
cover = "/images/covers/example.png"
```
