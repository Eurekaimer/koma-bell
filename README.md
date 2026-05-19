# koma-bell

`koma` 来自日语「コマ」，可以指漫画分镜或画格；`bell` 是提醒铃。`koma-bell` 的意思就是“漫画更新铃”：安静地守着你的订阅，有新章节时敲一下铃。

koma-bell 是一个轻量的漫画追更提醒器。当前阶段只做 CLI，不做 GUI/TUI、下载器或阅读器；它会读取本机配置里的漫画订阅，检查每本漫画的最新章节。如果网页显示最后更新时间在最近 7 天内，就通过邮箱 SMTP 发送邮件提醒。

这个项目面向个人低频使用，推荐每天运行一次。它不会下载漫画图片，不会绕过反爬，也不会做高频请求。

## 当前功能

- 运行 `uv run koma-bell` 后进入数字菜单。
- 从 URL 自动解析漫画名、最新章节标题和章节链接，并写入配置。
- 支持邮箱 SMTP，当前默认使用 QQ 邮箱 SMTP，菜单保存后可以立刻发送测试邮件。
- 使用 JSON 状态文件保存每本漫画上次检查到的章节。
- 正式检查时只根据网页最后更新时间判断是否提醒：最近 7 天内更新就发送邮件。
- `state.json` 只用于保存当前检查状态和给 GitHub Actions 自动提交，不决定是否发邮件。
- 提供 GitHub Actions 定时检查，每天东八区早上 8 点运行一次。
- 提供 `github-setup`，可以把本地配置写入 GitHub Actions Secrets。

## 邮件内容格式

更新提醒和预览邮件都会尽量保持简洁，不包含别名、热度、题材、书架按钮等网页噪音。每本漫画格式类似：

```text
+ 向笨蛋告白
  最新章节：第 10.1 话
  最后更新：2026-05-19 NEW
  链接：https://www.mangacopy.com/comic/xiangbendangaobai/chapter/...
```

说明：

- `NEW` 表示页面上的最后更新日期是今天。
- 没有解析到最后更新日期时，仍会显示漫画名、最新章节和链接。
- 最近 7 天之前的更新不会出现在邮件里。
- 邮件触发不依赖 `state.json` 里的旧章节记录。

## 未来计划

- 更完整的 TUI。
- 更多漫画源站适配。
- 更丰富的邮件模板。
- 批量导入和导出订阅。

## 安装

本项目使用 Python 和 uv 管理依赖。

环境要求：

- Python `>=3.12`
- uv
- 可选：GitHub CLI `gh`，只在需要一键写入 GitHub Actions Secrets 时使用

仓库内提供 `.python-version`、`pyproject.toml` 和 `uv.lock`。日常运行建议统一使用 `uv run ...`，这样会自动使用项目锁定的依赖环境。NixOS / nix shell 用户也一样，确保当前 shell 里有 `uv` 即可。

先安装 uv：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

进入项目目录后安装依赖：

```bash
uv sync --all-groups
```

检查 CLI 是否可用：

```bash
uv run koma-bell
```

启动后会看到：

```text
################################################################################
#                                                                              #
#     K     K   OOOOO   M     M     A      BBBB    EEEEE   L       L     #
#     K   K    O     O  MM   MM    A A     B   B   E       L       L     #
#     K K      O     O  M M M M   AAAAA    BBBB    EEEE    L       L     #
#     K   K    O     O  M  M  M  A     A   B   B   E       L       L     #
#     K     K   OOOOO   M     M  A     A   BBBB    EEEEE   LLLLL   LLLLL #
#                                                                              #
#                            Manga update notifier                             #
#                                                                              #
################################################################################

1. 配置邮箱
2. 添加订阅
3. 查看订阅 URL
4. 立即检查，有最近更新就发邮件
5. 发送一封预览测试邮件
6. 同步配置到 GitHub Actions
7. 查看本机文件位置
0. 退出
```

## 快速开始

第一次使用建议按这个顺序：

1. 运行 `uv run koma-bell`。
2. 选择 `1`，输入 QQ 邮箱、SMTP 授权码、接收提醒的邮箱。
3. 选择 `2`，粘贴漫画详情页 URL，例如 `https://www.mangacopy.com/comic/xiangbendangaobai`。
4. 选择 `3`，确认订阅 URL 已经保存。
5. 选择 `5`，先发一封预览测试邮件，不写状态。
6. 确认没问题后选择 `4` 正式检查，有最近更新就发邮件。

> [!TIP]
> `接收提醒的邮箱 [你的QQ邮箱]:` 这一行如果直接按回车，就是把提醒发给你自己的 QQ 邮箱。只有想发给其他邮箱时才需要输入另一个地址。

> [!TIP]
> URL 添加订阅分两步：程序会先尝试抓取页面元数据；如果站点连接失败、被重置或当前网络访问不了，它会提示你手动输入 `订阅 ID` 和 `漫画名`，然后仍然把这个 URL 保存到配置里。

> [!TIP]
> 粘贴章节页也可以，例如 `https://www.mangacopy.com/comic/xiangbendangaobai/chapter/xxx`。koma-bell 会自动识别 `/comic/xiangbendangaobai`，把 `xiangbendangaobai` 作为订阅 ID，并保存漫画详情页 URL。

## 本机文件位置

菜单启动时会打印配置文件位置，也可以运行：

```bash
uv run koma-bell paths
```

默认会优先使用当前目录里的 `config.yml` 和 `subscriptions.yml`。如果当前目录没有 `config.yml`，才会使用用户目录：

```text
config        ~/.config/koma-bell/config.yml
subscriptions ~/.config/koma-bell/subscriptions.yml
secrets       ~/.config/koma-bell/secrets.yml
state         ~/.local/state/koma-bell/state.json
```

`config.yml` 保存普通配置，示例：

```yaml
subscriptions_file: subscriptions.yml
request_interval_seconds:
  min: 2
  max: 5
```

`subscriptions.yml` 保存订阅列表，示例：

```yaml
- id: xiangbendangaobai
  name: 向笨蛋告白
  url: https://www.mangacopy.com/comic/xiangbendangaobai
```

字段说明：

- `subscriptions_file`: 订阅列表文件路径。相对路径会相对于 `config.yml` 所在目录解析。
- `request_interval_seconds.min/max`: 检查多本漫画时，每本之间的等待时间，默认 2 到 5 秒。
- `subscriptions[].id`: 订阅 ID，必须唯一。后续状态会用这个 ID 关联漫画。
- `subscriptions[].name`: 可选展示名。填写后邮件和终端里优先显示这个名称。
- `subscriptions[].url`: 拷贝漫画或 mangacopy 漫画详情页 URL。

> [!WARNING]
> `secrets.yml` 保存 QQ 邮箱授权码，只应该留在你自己的电脑上。不要提交到仓库，也不要发给别人。

## 邮箱设置（以 QQ 邮箱为例）

QQ 邮箱不能直接用登录密码发 SMTP 邮件，需要开启 SMTP 并生成“授权码”。

1. 登录网页版 QQ 邮箱。
2. 点击顶部或左侧的 `设置`。
3. 进入 `账户`。
4. 找到 `POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务`。
5. 开启 `POP3/SMTP服务` 或 `IMAP/SMTP服务`。
6. QQ 邮箱会要求短信或安全验证，完成后会给你一串 SMTP 授权码。
7. 回到 `uv run koma-bell` 菜单，选择 `1`，把这串授权码填到 `邮箱 SMTP 授权码`。

注意：

- `MAIL_USER` 是完整 QQ 邮箱地址，例如 `123456@qq.com`。
- `QQ 邮箱 SMTP 授权码` 是 QQ 邮箱生成的授权码，不是 QQ 登录密码。
- `接收提醒的邮箱` 可以和发件邮箱相同。直接回车就是发给自己。
- 不要在终端日志、Issue、Actions 日志或配置文件里打印授权码。

可以用下面命令测试邮箱连通性：

```bash
uv run koma-bell mail-test
```

这封邮件只说明 SMTP 配置可用，不包含漫画章节。

## 常用命令

检查配置文件和必要环境变量：

```bash
uv run koma-bell config-check
```

解析一个漫画详情页，不发邮件、不写状态：

```bash
uv run koma-bell inspect "https://www.mangacopy.com/comic/xiangbendangaobai"
```

自动解析 URL 并写入配置：

```bash
uv run koma-bell add "https://www.mangacopy.com/comic/xiangbendangaobai"
```

查看所有订阅 URL：

```bash
uv run koma-bell subscriptions
uv run koma-bell subscriptions --urls-only
```

如果 URL 当前抓不到元数据，可以手动指定漫画名：

```bash
uv run koma-bell add "https://www.mangacopy.com/comic/xiangbendangaobai" --name "向笨蛋告白"
```

> [!WARNING]
> 如果你看到 `Connection reset by peer`，说明对方站点或当前网络在连接阶段断开了请求。订阅仍然可以先保存，但后续 `check` 也需要你的运行环境能访问这个 URL 才能自动追更。

如果你的网络需要代理，koma-bell 默认会读取系统代理环境变量。也可以显式关闭：

```bash
KOMA_BELL_TRUST_ENV=0 uv run koma-bell inspect "https://www.mangacopy.com/comic/xiangbendangaobai"
```

正式检查所有订阅：

```bash
uv run koma-bell check
```

只打印检查结果，不发邮件、不写 `state.json`：

```bash
uv run koma-bell check --dry-run
```

发送一封“当前最新章节预览”邮件，但不写 `state.json`：

```bash
uv run koma-bell check --dry-run --send-test-mail
```

> [!TIP]
> 你说的“测试邮件里写现在更新到第几章”对应的就是 `check --dry-run --send-test-mail`。普通 `mail-test` 只检查邮箱配置是否能发信。

展示当前状态：

```bash
uv run koma-bell state-show
```

## 提醒规则

koma-bell 不靠 `state.json` 的旧章节记录判断是否发邮件。正式检查时，它只看漫画详情页解析到的 `最后更新`：

- 最后更新时间在最近 7 天内：发送邮件。
- 最后更新时间早于最近 7 天：不发送邮件。
- 没有解析到最后更新时间：不发送正式更新邮件，但 `check --dry-run --send-test-mail` 仍可用于发送预览测试。

`state.json` 仍会保存当前最新章节，用于查看状态和让 GitHub Actions 自动 commit 检查结果。

## GitHub Actions 定时运行

仓库里提供了两个 workflow：

- `.github/workflows/ci.yml`: push、pull request、手动触发时运行 lint、类型检查和测试。
- `.github/workflows/check.yml`: 手动触发或定时运行 `koma-bell check`，如果 `state.json` 有变化会自动 commit 回仓库。

默认推荐把 `config.yml` 和 `subscriptions.yml` 提交到仓库。这样你以后添加订阅只需要：

```bash
uv run koma-bell add "https://www.mangacopy.com/comic/xiangbendangaobai" --config config.yml
git add config.yml subscriptions.yml
git commit -m "chore: update manga subscriptions"
git push
```

在 GitHub 仓库页面进入 `Settings` -> `Secrets and variables` -> `Actions`，只需要添加这些邮箱相关 Repository secrets：

```text
MAIL_USER
MAIL_AUTH_CODE
MAIL_TO
```

`KOMA_BELL_CONFIG_YML` 和 `KOMA_BELL_SUBSCRIPTIONS_YML` 仍然支持，但只是隐私模式的备用方案：只有仓库里没有 `config.yml` 或 `subscriptions.yml` 时，workflow 才会从这两个 Secret 写临时文件。

### 方法一：用 CLI 写入 GitHub Secrets

GitHub 不允许把 Secrets 直接 push 到仓库，这是正常的安全设计。推荐流程是：

1. fork 并 clone 本项目。
2. 本地运行 `uv run koma-bell`，完成 QQ 邮箱和订阅配置。
3. 安装 GitHub CLI。不同系统安装方式不同，可以参考 GitHub CLI 官方文档，或使用你的系统包管理器安装 `gh`。

4. 登录 GitHub CLI：

```bash
gh auth login
```

5. 把邮箱配置写入你 fork 后仓库的 Actions Secrets：

```bash
uv run koma-bell github-setup --repo OWNER/REPO
```

例如：

```bash
uv run koma-bell github-setup --repo eurekaimer/koma-bell
```

这个命令会写入：

```text
KOMA_BELL_CONFIG_YML
KOMA_BELL_SUBSCRIPTIONS_YML
MAIL_USER
MAIL_AUTH_CODE
MAIL_TO
```

> [!WARNING]
> `github-setup` 不会打印邮箱授权码，也不会把它写进 git。它通过 `gh secret set` 调 GitHub API，把值保存到仓库的 Actions Secrets。普通使用时只需要确认 `MAIL_USER`、`MAIL_AUTH_CODE`、`MAIL_TO` 存在即可。

6. push 代码后，可以在 GitHub Actions 页面手动运行 `Daily Check`，之后定时任务会自动运行。

### 方法二：在 GitHub 页面手动添加 Secrets

如果不想安装 GitHub CLI，也可以在网页上手动设置：

1. 打开你 fork 后的 GitHub 仓库页面。
2. 点击仓库顶部的 `Settings`。
3. 左侧找到 `Secrets and variables`。
4. 点击 `Actions`。
5. 进入 `Repository secrets` 区域。
6. 点击 `New repository secret`。
7. 逐个添加下面这些 Secret。

需要添加：

```text
MAIL_USER
MAIL_AUTH_CODE
MAIL_TO
```

填写方式：

- `MAIL_USER`: QQ 邮箱地址，例如 `123456@qq.com`。
- `MAIL_AUTH_CODE`: QQ 邮箱 SMTP 授权码，不是 QQ 登录密码。
- `MAIL_TO`: 接收提醒的邮箱，可以和 `MAIL_USER` 相同。

> [!TIP]
> GitHub 保存 Secret 后不会再显示明文。如果填错了，重新点同名 Secret 更新即可。

定时检查 workflow 当前配置为每天东八区早上 8 点运行一次。GitHub Actions 的 cron 使用 UTC，所以这里写 UTC 00:00：

```yaml
schedule:
  - cron: "0 0 * * *"
```

> [!WARNING]
> 不要把 `secrets.yml`、邮箱授权码提交到仓库。`.gitignore` 已经忽略本地 `state.json`、`secrets.yml` 和 `.env`。`config.yml` 和 `subscriptions.yml` 默认可以提交，用于 GitHub Actions 定时运行。

> [!TIP]
> 如果你不想公开订阅列表，可以删除仓库里的 `subscriptions.yml`，改用 `KOMA_BELL_SUBSCRIPTIONS_YML` Secret。

`check.yml` 会在 `state.json` 有变化时自动 commit 回仓库。`state.json` 不保存密码或授权码，但会包含漫画名、URL 和最新章节；如果你认为订阅列表也属于隐私，请使用私有仓库，或关闭自动 commit state 的步骤。

## 开发和测试

安装开发依赖：

```bash
uv sync --all-groups
```

运行 CI 同款检查：

```bash
uv run ruff check .
uv run pyright
uv run pytest
```

普通测试不会访问真实拷贝漫画网站，也不会真的发送邮件。邮件测试会 mock SMTP。

可选 live test 默认跳过。只有显式设置环境变量才会运行：

```bash
KOMA_BELL_LIVE_TEST=1 \
KOMA_BELL_LIVE_COPYMANGA_URL="https://www.copymanga.tv/comic/example" \
uv run pytest tests/live
```

## 安全边界

- 不要提交邮箱授权码、cookie、token。
- `state.json` 只保存漫画状态，不保存敏感凭据。
- 日志和终端输出不会主动打印密码、授权码、完整 cookie 或 token。
- 默认每本漫画之间 sleep 2 到 5 秒，只适合个人低频追更提醒。
- 不实现漫画图片下载，不实现阅读器，不绕过反爬，不做批量抓取。

## 项目结构

```text
src/koma_bell/
  cli.py                    # CLI 层
  config.py                 # 配置层
  state.py                  # 状态存储入口
  checker.py                # 检查器业务层
  notifier.py               # 通知编排
  sources/copymanga/        # 拷贝漫画源站适配和解析
  mail/smtp.py              # SMTP 邮件发送，当前默认 QQ 邮箱
  storage/json_store.py     # JSON 读写
  utils/                    # 通用工具
tests/
  unit/                     # 单元测试
  integration/              # mock 集成测试
  live/                     # 可选真实站点测试，默认跳过
```
