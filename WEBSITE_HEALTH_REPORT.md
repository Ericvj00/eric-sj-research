# Eric SJ Research 发布前健康检查报告

检查时间：2026-07-31  
检查范围：当前 Hugo 网站仓库

## 总体结论

当前仓库 production build 通过；新增文章、图片、封面路径没有发现阻塞级问题。  
本次检查中只做了两个低风险修复：转义两处正文中用于数学/说明语义的孤立 `*`，避免 Markdown 误解析为强调标记；未修改文章观点、标题、日期、分类、URL，也未提交或 push。

上线建议：可以上线，但建议提交前排除日志和 `__pycache__`。

## 1. Git 工作区分类

### 应提交

- `content/zh-cn/web3/projects/2024-03-29-neopin-rwa.md`
  - 低风险修复：将正文中的孤立 `*流动性` 转义为 `\*流动性`。
- `content/zh-cn/web3/projects/2025-02-08-solana-pump-fun2-0-pumpkin-fun.md`
  - 低风险修复：将公式说明中的 `*` 转义为 `\*`。

### 不应提交

- `scripts/__pycache__/sync_content.cpython-312.pyc`
  - Python 编译缓存，不应进入 Git。

### 临时文件 / 日志文件

- `logs/content-sync.log`
  - 同步日志，除非需要保留审计记录，否则不建议提交。

### 可能遗漏

- 当前 `git status` 未显示新增文章或新增图片未提交，说明本周新增文章同步提交已经在此前提交中完成。
- 当前未发现未提交的工具页面修改。

## 2. Hugo Production Build

执行命令：

```powershell
hugo --cleanDestinationDir --minify --baseURL https://ericsj.xyz/
```

初次构建结果：通过，无 warning / error。

构建统计：

| Language | Pages | Paginator pages | Static files | Aliases |
|---|---:|---:|---:|---:|
| zh-cn | 336 | 17 | 758 | 9 |
| zh-tw | 518 | 17 | 758 | 8 |

低风险修复后重新构建：通过，无 warning / error。页面数保持不变。

## 3. 站内链接、图片路径、封面路径、favicon、静态资源

### 静态资源与图片

- public HTML 中静态资源缺失：0
- 文章 Front Matter `cover` 指向不存在文件：0
- 文章缺少 `cover`：0
- 最近新增图片：未发现未引用或引用缺失问题。

### 站内链接

扫描到 2 个“缺失链接”样本：

- `zh-cn/search/index.html` → `${e.url}`
- `zh-tw/search/index.html` → `${e.url}`

判断：这是搜索页 JavaScript 模板字符串，不是实际静态链接，属于扫描误报，不阻塞发布。

### favicon

`static/` 下未发现独立 `favicon` / `.ico` 文件。当前 build 未因此报错，但这是品牌完整性可优化项。

## 4. 手机端导航和 JavaScript

当前导航结构：

- `layouts/partials/header.html` 使用 `<details class="nav-group">` + `<summary>` 实现一级导航与下拉。
- 移动端 CSS 在 `static/css/style.css` 中使用 `@media (max-width: 900px)` 将 submenu 改为静态展开区域。

当前 JS：

```js
document.querySelectorAll(".nav-group > summary").forEach(summary => {
  summary.addEventListener("click", event => {
    const group = summary.parentElement;
    if (!window.matchMedia("(max-width: 900px)").matches || !group.open) return;
    event.preventDefault();
    window.location.href = group.dataset.href;
  });
});
```

结论：

- 不是构建错误。
- 移动端第一次点击可展开；如果菜单已经展开，再点一级标题会跳转到一级栏目页。
- 如果预期是“二次点击收起”，这里会产生体验歧义。建议后续产品层面决定是否保留“二次点击跳转”。

## 5. 简体 / 繁体页面数量差异

Hugo build：

- zh-cn：336
- zh-tw：518

内容源统计：

| 语言 | 非 `_index.md` Markdown | 带 title 的文章 | Web3 | Stocks |
|---|---:|---:|---:|---:|
| zh-cn | 167 | 157 | 147 | 10 |
| zh-tw | 158 | 155 | 146 | 9 |

public 输出抽样统计：

| 语言 | html | tags | categories | web3 index | stocks index |
|---|---:|---:|---:|---:|---:|
| zh-cn | 272 | 63 | 9 | 166 | 17 |
| zh-tw | 362 | 159 | 7 | 165 | 16 |

解释：

- 正式文章数量差异很小，页面数差异不是文章大量缺失导致。
- 差异主要来自 taxonomy 页面，尤其是 `tags`：zh-tw tag 页面显著更多。
- 当前不属于阻塞问题；如果想让两语言页面数接近，需要统一 tags / categories 策略。

## 6. 最近新增 Markdown Front Matter

### `content/zh-cn/stocks/earnings/2026-07-24-intel-earnings.md`

- title：存在
- date：`2026-07-24T13:27:14+08:00`
- categories：`财报分析`
- tags / seo_keywords：Intel、英特尔、Intel财报、Intel Foundry、半导体、AI芯片、制造业务、财报分析
- summary：存在
- cover：`/images/covers/2026-07-24-intel-earnings-cover.png`
- slug：`2026-07-24-intel-earnings`
- keywords：未使用独立 `keywords` 字段，但存在 `seo_keywords`
- og：未使用独立 `og_*` 字段；模板应读取 title / summary / cover。

### `content/zh-cn/web3/onchain-financials/2026-07-22-2026.md`

- title：存在
- date：`2026-07-22T13:13:22+08:00`
- categories：`链上财报`
- tags / seo_keywords：加密行业半年报、Web3基础设施、链上交易、永续合约DEX、Hyperliquid、Base、Robinhood Chain、稳定币
- summary：存在
- cover：`/images/covers/2026-07-22-2026-cover.png`
- slug：`2026-07-22-2026`
- keywords：未使用独立 `keywords` 字段，但存在 `seo_keywords`
- og：未使用独立 `og_*` 字段；模板应读取 title / summary / cover。

## 7. `sync_content.py` 封面尺寸逻辑

检查结果：

- 脚本仍硬编码最终输出封面尺寸 `1280x512`。
- 当前逻辑包含 `cover_needs_normalization`、`cover_used_placeholder`、`cover_output_dimensions` 等状态字段。
- 未发现“源封面不是 5:2 就失败”的阻塞逻辑。
- 当前业务语义是：源图可为非 5:2，最终统一输出为 1280×512 网站封面。

结论：硬编码的是网站展示规范，不是源图拒绝条件；目前不阻塞发布。

## 8. 文章时间排序来源

`sync_content.py` 中新文章导入使用 HTML 解析得到的 `published_at`。

检查点：

- 存在 `published_at(document)` 解析函数。
- 新文章报告中写入 `published_at`。
- 未发现使用文件创建时间作为发布时间。
- 脚本中存在 `datetime.now(...)`，用于日志时间戳，不作为文章发布时间。

结论：文章排序使用 HTML 源发布时间，不是文件创建时间。

## 9. 内容残留与结构

检查项：

- 错误的单独 `*`：发现 2 处，已低风险修复。
- `AI总结`：0
- 底部“关注X”：0
- 正文中的原文来源 / Binance URL 残留：0
- 空摘要：0
- 空关键词：0
- 重复 slug：0
- 正文为空：0
- 重复 `## 文章摘要`：0
- 正式 zh-cn 文章 `## 正文`：157 / 157 存在。

说明：

- `source_url` 在 Front Matter 中大量存在，这是预期后台字段，不会作为正文来源残留处理。

## 10. 最近新增图片引用完整性

Intel 文章：

- cover：存在
- 正文图片 3 张：存在
- assets 与 static 镜像均存在
- Markdown 引用已指向 `intel-earnings` 命名

2026 加密半年报：

- cover：存在
- 正文图片 7 张：存在
- assets 与 static 镜像均存在

结论：未发现新增图片缺失或未引用导致的页面破图。

## 11. Cloudflare Pages 构建配置

仓库内未发现：

- `.github/workflows/`
- `wrangler.toml`
- `_headers`
- `_redirects`
- `netlify.toml`
- `vercel.json`

本地 Hugo 配置：

- `hugo.toml`
- baseURL：`https://ericsj.xyz/`
- 当前本地构建命令建议：`hugo --cleanDestinationDir --minify --baseURL https://ericsj.xyz/`
- Hugo 版本：`hugo v0.164.0 extended windows/amd64`

结论：

- 仓库内没有可比对的 Cloudflare Pages 配置文件。
- 需要在 Cloudflare Pages 控制台确认 Build command / Output directory / Hugo version 是否与本地一致。

建议 Cloudflare Pages：

- Build command：`hugo --gc --minify --baseURL https://ericsj.xyz/`
- Output directory：`public`
- HUGO_VERSION：建议与本地接近，至少兼容当前模板；本地为 `0.164.0`。

## 阻塞发布

无。

## 应尽快修复

1. 排除未提交杂项：
   - `logs/content-sync.log`
   - `scripts/__pycache__/sync_content.cpython-312.pyc`

2. Cloudflare Pages 控制台配置需要人工确认：
   - 仓库内没有 Cloudflare 构建配置文件，无法从仓库证明线上构建命令与本地一致。

## 可后续优化

1. favicon：
   - 当前未发现独立 favicon 文件；建议补充品牌 favicon / apple-touch-icon。

2. 移动端导航：
   - 当前二次点击已展开一级导航会跳转一级栏目页。
   - 若希望移动端纯展开/收起，可后续调整 JS。

3. taxonomy 数量一致性：
   - zh-tw tag 页面数量显著多于 zh-cn。
   - 如果追求双语站结构一致，可单独审计 tags / categories。

## 本次低风险修复

已修复：

- `content/zh-cn/web3/projects/2024-03-29-neopin-rwa.md`
- `content/zh-cn/web3/projects/2025-02-08-solana-pump-fun2-0-pumpkin-fun.md`

修复内容：

- 仅将正文中孤立 `*` 转义为 `\*`，避免 Markdown 误解析。
- 未修改文章观点、标题、日期、分类、slug、Front Matter 或图片。

修复后 build：

- 通过
- warning：0
- error：0
- 页面数无变化
