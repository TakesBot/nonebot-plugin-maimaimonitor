from asyncio import Lock
from collections import defaultdict
from typing import Any
from nonebot import on_command, get_driver, require, get_plugin_config
from nonebot.matcher import Matcher
from nonebot.exception import FinishedException
from nonebot.adapters.onebot.v11 import Bot, Event, Message
from nonebot.params import CommandArg
import asyncio
from nonebot import get_plugin_config
from .config import Config
from playwright.async_api import async_playwright
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment
from io import BytesIO
import httpx
from PIL import Image


config = get_plugin_config(Config)
from .client import MaimaiReporter
from .constants import get_help_menu, REPORT_MAPPING, ReportCode

reporter = MaimaiReporter(
    client_id=str(config.maimai_bot_client_id),
    private_key=config.maimai_bot_private_key,
    worker_url=config.maimai_worker_url
)

report_cache: defaultdict[int, list[int]] = defaultdict(list)
cache_lock = Lock()

report_matcher = on_command("report", aliases={"上报"}, priority=5, block=False)
report_preview = on_command("preview", aliases={"舞萌状态"}, priority=20, block=False)

@report_preview.handle()
async def handle_preview():
    try:
        url = "https://mai.chongxi.us/api/og"
        url2 = "https://status.nekotc.cn/status/maimai"
        
        # 获取第一张图片，增加重试机制
        screenshot1 = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=20.0)
                    response.raise_for_status()
                    screenshot1 = response.content
                    print(f"✓ 成功获取第一张图片 (尝试 {attempt + 1}/3)")
                    break
            except Exception as e:
                print(f"✗ 获取第一张图片失败 (尝试 {attempt + 1}/3): {str(e)}")
                if attempt == 2:
                    await report_preview.finish(f"获取页面失败: 无法从 {url} 获取图片，已重试3次\n错误: {str(e)}")
                await asyncio.sleep(2)
        
        # 截取第二个页面，添加延迟
        screenshot2 = None
        browser = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page2 = await browser.new_page(viewport={"width": 1400, "height": 1200})
                await page2.goto(url2, wait_until="domcontentloaded", timeout=30000)
                await page2.wait_for_timeout(2000)  # 增加延迟到2秒
                screenshot2 = await page2.screenshot(full_page=False)
                await browser.close()
                print("✓ 成功截取第二个页面")
        except Exception as e:
            if browser:
                await browser.close()
            print(f"✗ 截取第二个页面失败: {str(e)}")
            await report_preview.finish(f"获取页面失败: 无法截取 {url2} 页面\n错误: {str(e)}\n提示: 请确保已安装 playwright 浏览器 (playwright install chromium)")

        # 将两张图片合并为一张（上下排列）
        try:
            img1 = Image.open(BytesIO(screenshot1))
            img2 = Image.open(BytesIO(screenshot2))
            
            # 将第一张图片等比放大到宽度1400px
            target_width = 1400
            if img1.width != target_width:
                ratio = target_width / img1.width
                new_height = int(img1.height * ratio)
                img1 = img1.resize((target_width, new_height), Image.LANCZOS)
            
            # 创建新图片，高度为两张图片高度之和，宽度取最大值
            total_width = max(img1.width, img2.width)
            total_height = img1.height + img2.height
            combined_img = Image.new('RGB', (total_width, total_height))
            
            # 粘贴两张图片
            combined_img.paste(img1, (0, 0))
            combined_img.paste(img2, (0, img1.height))
            
            # 转换为字节流
            buf = BytesIO()
            combined_img.save(buf, format='PNG')
            buf.seek(0)
            print("✓ 成功合并图片")
            
            await report_preview.finish(MessageSegment.image(buf) + f"可以通过/report上报舞萌服务器状态!")
        except Exception as e:
            print(f"✗ 图片处理失败: {str(e)}")
            await report_preview.finish(f"获取页面失败: 图片处理出错\n错误: {str(e)}")
    except FinishedException:
        raise
    except Exception as e:
        print(f"✗ 未知错误: {str(e)}")
        await report_preview.finish(f"获取页面失败: {type(e).__name__}: {str(e)}")

@report_matcher.handle()
async def handle_report(bot: Bot, event: Event, args: Message = CommandArg()):
    arg_text = args.extract_plain_text().strip()
    arg_parts = arg_text.split()

    if not arg_text or len(arg_parts) == 0:
        await report_matcher.finish(f"指令格式错误。\n{get_help_menu()}")
        return

    if arg_parts[0].lower() in ['help', '帮助']:
        await report_matcher.finish(get_help_menu())
        return

    report_key = arg_parts[0].lower()
    if report_key not in REPORT_MAPPING:
        await report_matcher.finish(f"未知的报告类型: '{report_key}'\n请使用 /report help 查看可用类型。")
        return

    report_code, report_name = REPORT_MAPPING[report_key]
    report_value = 1

    if report_code == ReportCode.WAIT_TIME:
        if len(arg_parts) > 1:
            try:
                report_value = int(arg_parts[1])
            except ValueError:
                await report_matcher.finish("罚站时长参数必须是数字（秒数）")
                return
        else:
            await report_matcher.finish("请输入罚站时长（秒）。\n用法: /report 罚站 [秒数]")
            return

    result_message = await process_maimai_report(
        report_code=report_code,
        report_name=report_name,
        report_value=report_value,
        bot=bot,
        event=event
    )
    await report_matcher.finish(result_message)


async def process_maimai_report(
    report_code: ReportCode,
    report_name: str,
    report_value: Any,
    bot: Bot,
    event: Event
) -> str:
    async with cache_lock:
        report_cache[report_code].append(report_value)
    return f"{report_name}上报成功"


async def trigger_report_by_command_string(
    command_string: str,
    bot: Bot,
    event: Event
) -> str:
    arg_text = command_string.lstrip('/').lstrip("report").strip()
    arg_parts = arg_text.split()

    if not arg_text or len(arg_parts) == 0:
        return f"指令格式错误。\n{get_help_menu()}"

    report_key = arg_parts[0].lower()
    if report_key not in REPORT_MAPPING:
        return f"未知的报告类型: '{report_key}'\n请使用 /report help 查看可用类型。"

    report_code, report_name = REPORT_MAPPING[report_key]
    report_value = 1

    if report_code == ReportCode.WAIT_TIME:
        if len(arg_parts) > 1:
            try:
                report_value = int(arg_parts[1])
            except ValueError:
                return "罚站时长参数必须是数字（秒数）。"
        else:
            return "请输入罚站时长（秒）。\n用法: /report 罚站 [秒数]"

    return await process_maimai_report(
        report_code=report_code,
        report_name=report_name,
        report_value=report_value,
        bot=bot,
        event=event
    )

COUNT_BASED_TYPES = {
    ReportCode.ERR_NET_LOST, ReportCode.ERR_LOGIN, ReportCode.ERR_MAI_NET,
    ReportCode.ACC_INVOICE, ReportCode.ACC_BAN, ReportCode.ACC_SCAN
}

async def send_aggregated_reports():
    final_payload = []
    
    async with cache_lock:
        if not report_cache:
            return
        
        cached_items = list(report_cache.items())
        report_cache.clear()

    for report_type, values in cached_items:
        if report_type in COUNT_BASED_TYPES:
            total_value = sum(values)
            if total_value > 0:
                final_payload.append({"t": report_type, "v": total_value, "r": "BOT"})
        else:
            for value in values:
                final_payload.append({"t": report_type, "v": value, "r": "BOT"})
    
    if not final_payload:
        return

    try:
        print("--- Sending aggregated bot report... ---")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, reporter.send_report, final_payload, config.maimai_bot_display_name)
    except Exception as e:
        print(f"Error sending aggregated report: {e}")


def create_dynamic_alias_matcher(trigger_cmd: str, target_cmd_string: str):
    dynamic_matcher = on_command(trigger_cmd, block=False, priority=5)

    @dynamic_matcher.handle()
    async def handle_dynamic_alias(bot: Bot, event: Event, args: Message = CommandArg()):
        result_message = await trigger_report_by_command_string(
            command_string=target_cmd_string,
            bot=bot,
            event=event
        )
        await dynamic_matcher.finish(f"命令联动触发 [{trigger_cmd}]: {result_message}")


for trigger_cmd, target_cmd_string in config.command_aliases.items():
    create_dynamic_alias_matcher(trigger_cmd, target_cmd_string)


require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

scheduler.add_job(send_aggregated_reports, "interval", seconds=30, id="maimai_report_scheduler_v11")