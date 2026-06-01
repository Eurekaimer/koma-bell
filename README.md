# koma-bell

一个用来盯漫画更新的小工具。

写这个主要是因为有些作者真的太能拖了，我又不想每天点进去看一遍。koma-bell 就负责帮我看一眼：最近更了就发邮件，没更就当无事发生。

现在只有 CLI，功能也很简单，就是个人用来少刷几次网页。

目前支持 CopyManga 漫画详情页 URL，地址里需要包含 `/comic/{comic_id}`。
除了本地手动检查，也可以交给 GitHub Actions 每天定时运行。

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

# 查看单个详情页能否正确解析
uv run koma-bell inspect "https://www.mangacopy.com/comic/xiangbendangaobai"

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

# 查看已经保存的检查状态
uv run koma-bell state-show
```

## 配置

如果当前目录里存在 `config.yml`，会优先读取它；否则使用：

```text
~/.config/koma-bell/config.yml
```

`subscriptions.yml` 的位置由 `config.yml` 里的 `subscriptions_file` 决定。使用相对路径时，
它会相对于 `config.yml` 所在目录解析。

`subscriptions.yml` 大概这样写：

```yaml
- id: xiangbendangaobai
  name: 向笨蛋告白
  url: https://www.mangacopy.com/comic/xiangbendangaobai
```

`id` 用来区分订阅，`name` 是邮件里显示的名字，`url` 是漫画详情页。

邮箱授权码保存在 `~/.config/koma-bell/secrets.yml`，检查状态默认保存在
`~/.local/state/koma-bell/state.json`。运行 `uv run koma-bell paths` 可以查看当前实际使用的路径。

## GitHub Actions

仓库里带了定时检查 workflow：每天北京时间 `08:00` 自动运行，也可以在 Actions 页面手动触发。

最省事的配置方式是先安装并登录 GitHub CLI，然后把本地配置同步到 Actions Secrets：

```bash
gh auth login
uv run koma-bell github-setup --repo OWNER/REPO
```

这个命令会写入：

```text
KOMA_BELL_CONFIG_YML
KOMA_BELL_SUBSCRIPTIONS_YML
MAIL_USER
MAIL_AUTH_CODE
MAIL_TO
```

workflow 启动时，如果仓库里没有 `config.yml` 或 `subscriptions.yml`，会从前两个 Secrets
恢复配置。也可以直接把这两个不含邮箱授权码的文件提交进仓库；仓库内文件存在时会优先使用。
邮箱授权码不要提交进仓库。

每次检查结束后，workflow 会更新并自动提交 `state.json`，方便保留最近一次检查结果。

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
