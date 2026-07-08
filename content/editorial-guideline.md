# Eric SJ Research 写作规范

## 标题格式

- 使用清晰、可搜索的主题标题。
- 优先包含研究对象和分析角度。
- 示例：`Hyperliquid商业模式分析`。

## 摘要格式

- `description` 用于 SEO，控制在一到两句话。
- `summary` 用于页面内的一句话总结，直接说明文章核心结论或测试目标。

## Key Points 格式

- 使用 `key_points` 数组。
- 每条只表达一个观点。
- 建议 2 到 5 条。

```toml
key_points = [
  "核心观点1",
  "核心观点2",
]
```

## FAQ 格式

- 使用 question / answer 结构。
- 每个问题尽量贴近搜索用户会问的自然语言。

```toml
faq = [
  { question = "问题？", answer = "答案。" },
]
```

## 引用来源格式

使用 `source` 字段记录主要来源：

```toml
source = { name = "来源名称", url = "https://example.com" }
```

如果没有外部来源，保持为空：

```toml
source = { name = "", url = "" }
```

## 图片路径规则

封面图：

```text
static/images/covers/
```

图表：

```text
static/images/charts/
```

Logo：

```text
static/images/
```

文章封面写法：

```toml
cover = "/images/covers/example.png"
```

## CTA 规则

- Web3 和综合研究文章：引导继续阅读相关研究。
- Guides 文章：引导查看教程。
- Stocks 文章：引导继续阅读相关研究，并显示免责声明。
