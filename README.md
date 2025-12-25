# NoneBot Plugin: Maimai Monitor

一个为 NoneBot2 框架设计的插件，用于上报 maimai 服务器状态

## 功能
- [x] **状态上报**: 通过简单的聊天指令（如 `/report 断网`）上报机台当前状态。
- [x] **数据聚合**: 自动缓存用户上报数据，每 30 秒批量发送至后端 API
- [ ] **自动渲染**：待实现，您现在需要主动截取`https://mai.chongxi.us/?share=true&dark=auto`获取数据
*   **OneBot V11 适配**: 基于 NoneBot2 的 OneBot V11 适配器实现。

## 安装

你可以通过 NoneBot 的脚手架工具 nb-cli 安装：

```bash
nb plugin install nonebot-plugin-maimaimonitor
```

或者通过 pip 安装：

```bash
pip install nonebot-plugin-maimaimonitor
```

## 配置

插件的配置项通过 NoneBot 的统一配置方式进行管理，你需要在你的 NoneBot 项目根目录下的 `.env` 文件中设置以下环境变量。

## 获取凭证

为了向后端 API 发送数据，你需要一个 `ClientID` 和 `PRIVATE_KEY`。请联系 email:qwq@chongxi.us 或 QQ:2623993663 获取。`ClientID`由您提供，一般以您的QQ号作为`ClientID`。

**请妥善保管你的 `PRIVATE_KEY`，不要泄露给任何人。**

### 环境变量

| 环境变量              | 类型   | 默认值                  | 说明                                   |
| :-------------------- | :----- | :---------------------- | :------------------------------------- |
| `MAIMAI_BOT_CLIENT_ID` | `str`  | 无                      | ClientID (必要)             |
| `MAIMAI_BOT_PRIVATE_KEY` | `str`  | 无                      | 私钥 (必要)                  |
| `MAIMAI_BOT_DISPLAY_NAME` | `str`  | `qwq`                   | 您bot的名称           |
| `MAIMAI_WORKER_URL`   | `str`  | `https://maiapi.chongxi.us` | 上报数据后端的 API 地址  |

示例 `.env` 配置：

```
# .env 文件 (位于你的 NoneBot 项目根目录)

MAIMAI_BOT_CLIENT_ID="YOUR_BOT_CLIENT_ID"
MAIMAI_BOT_PRIVATE_KEY="YOUR_BOT_PRIVATE_KEY"
MAIMAI_BOT_DISPLAY_NAME="qwqbot"
# MAIMAI_WORKER_URL="https://maiapi.chongxi.us" # 
```

## 使用

在你的 NoneBot 项目 `bot.py` 文件中加载插件：

```python
# bot.py
import nonebot

# ... 其他初始化代码 ...

nonebot.load_plugin("nonebot_plugin_maimaimonitor")

# ... nonebot.run() ...
```

插件加载成功后，你可以在与机器人聊天的任何地方发送以下指令：

*   `/report help` 或 `/report 帮助`: 查看全部可用的上报类型和帮助信息。

部分命令示例
*   `/report 断网`: 上报一次机台网络断开事件。
*   `/report 罚站 [秒数]`: 上报玩家罚站时长，例如 `/report 罚站 300` 表示罚站 5 分钟

## 主动 Dashboard 渲染
未来将会支持直接将前端渲染为SVG并转化为图片，当前仍需要截取`https://mai.chongxi.us/?share=true&dark=auto`

`share`为bot特殊优化的页面，`dark`用于切换深色模式，auto会自动根据时间切换

## 贡献

欢迎提交PR
