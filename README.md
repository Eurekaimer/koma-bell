# koma-bell

一个用来盯漫画更新的小工具。

写这个主要是因为有些作者真的太能拖了，我又不想每天点进去看一遍。koma-bell 就负责帮我看一眼：最近更了就发邮件，没更就当无事发生。

现在只有 CLI，功能也很简单，就是个人用来少刷几次网页。

## 安装

需要 Python `>=3.12` 和 `uv`。

```bash
uv sync --all-groups
```

启动：

```bash
uv run koma-bell
```

## 怎么用

第一次用直接走菜单就行：

1. 选 `1`，配置邮箱。QQ 邮箱要用 SMTP 授权码，不是登录密码。
2. 选 `2`，添加漫画详情页 URL。
3. 选 `3`，看订阅有没有存进去。
4. 选 `5`，先发一封预览邮件试试。
5. 选 `4`，正式检查，有最近更新就会发邮件。

菜单长这样：

```text
1. 配置邮箱
2. 添加订阅
3. 查看订阅 URL
4. 立即检查，有最近更新就发邮件
5. 发送一封预览测试邮件
6. 同步配置到 GitHub Actions
7. 查看本机文件位置
0. 退出
```

## 常用命令

```bash
# 添加订阅
uv run koma-bell add "https://www.mangacopy.com/comic/xiangbendangaobai"

# 查看订阅
uv run koma-bell subscriptions

# 检查更新
uv run koma-bell check

# 只看检查结果，不发邮件
uv run koma-bell check --dry-run

# 发一封当前章节预览邮件
uv run koma-bell check --dry-run --send-test-mail

# 看配置文件在哪
uv run koma-bell paths

# 测试邮箱配置
uv run koma-bell mail-test
```

## 配置

默认会优先读当前目录里的：

```text
config.yml
subscriptions.yml
```

`subscriptions.yml` 大概这样写：

```yaml
- id: xiangbendangaobai
  name: 向笨蛋告白
  url: https://www.mangacopy.com/comic/xiangbendangaobai
```

`id` 用来区分订阅，`name` 是邮件里显示的名字，`url` 是漫画详情页。

## GitHub Actions

仓库里带了定时检查 workflow。想让它每天自动跑的话，把 `config.yml` 和 `subscriptions.yml` 放进仓库，再在 GitHub Actions Secrets 里加：

```text
MAIL_USER
MAIL_AUTH_CODE
MAIL_TO
```

也可以用命令写入：

```bash
uv run koma-bell github-setup --repo OWNER/REPO
```

## 提醒规则

正式检查时只看页面上的最后更新时间：

- 最近 7 天内更新：发邮件。
- 超过 7 天：不发。
- 没解析到更新时间：正式检查不发，但预览邮件还能看当前最新章节。

`state.json` 只是记录检查结果，方便看状态和给 Actions 自动提交，不用它判断要不要发邮件。

## 开发

```bash
uv run ruff check .
uv run pyright
uv run pytest
```
