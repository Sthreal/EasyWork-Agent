#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""办公自动化 Agent 自动化测试（20 黄金 Case / 3 类评分器 / 完整 Trace）。

用法:
    python scripts/smoke_test.py [--rounds 3] [--base-url http://127.0.0.1:8001]
                                 [--include-email] [--cleanup]

退出码: 0=全过 1=有失败 2=环境未就绪
"""
import argparse
import json
import os
import random
import sqlite3
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import openpyxl

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

EXCEL_PATH = PROJECT_ROOT.parent / "Excel数据" / "报名表.xlsx"
APP_LOG = PROJECT_ROOT / "logs" / "app.log"
REPORT_DIR = PROJECT_ROOT / "logs"
TRACE_DIR = PROJECT_ROOT / "logs" / "traces"
DEFAULT_BASE_URL = "http://127.0.0.1:8001"
TIMEOUT = 60


def load_env(path):
    env = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def resolve_db_path(env):
    url = env.get("DATABASE_URL", "sqlite:///./office_agent.db")
    if url.startswith("sqlite:///"):
        p = Path(url[len("sqlite:///"):])
        return p if p.is_absolute() else (PROJECT_ROOT / p)
    return PROJECT_ROOT / "office_agent.db"


def read_sheet():
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active
    return [[ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)] for r in range(1, ws.max_row + 1)]


def log_tail(n=20):
    if not APP_LOG.exists():
        return "(无日志文件)"
    lines = APP_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-n:])


def post_task(api, text, round_no=1):
    return api.post("/api/v1/tasks", json={"text": text, "round": round_no})


def decide(api, cid, approve):
    return api.post(f"/api/v1/confirmations/{cid}/decide", json={"approve": approve})


def find_item(body, tool):
    for item in body.get("tasks", []):
        if item.get("tool") == tool:
            return item
    return None


def rand_suffix():
    return datetime.now().strftime("%H%M%S") + str(random.randint(10, 99))


def get_confirmations(api):
    return api.get("/api/v1/confirmations").json().get("items", [])


def make_trace(case_id, rnd):
    return {
        "trace_id": f"{case_id}_r{rnd}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        "case_id": case_id,
        "round": rnd,
        "input": None,
        "request": None,
        "response": None,
        "planning": None,
        "locate": None,
        "confirmation": None,
        "side_effect": None,
        "log_snippet": None,
        "scoring": None,
        "result": None,
    }


def write_trace(trace):
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    path = TRACE_DIR / f"{trace['trace_id']}.json"
    path.write_text(json.dumps(trace, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def check_env(base_url):
    problems = []
    try:
        resp = httpx.get(f"{base_url.rstrip('/')}/health", timeout=5)
        if resp.status_code != 200 or resp.json().get("status") != "ok":
            problems.append(f"后端健康检查异常（{base_url}/health）")
    except Exception as exc:
        problems.append(f"后端 {base_url} 不可访问：{exc}")
    env = load_env(PROJECT_ROOT / ".env")
    if not (env.get("LLM_API_KEY") and env.get("LLM_BASE_URL") and env.get("LLM_MODEL")):
        problems.append(".env 未配置 DeepSeek")
    db_path = resolve_db_path(env)
    if db_path.exists():
        try:
            con = sqlite3.connect(db_path)
            row = con.execute(
                "select access_token, expires_at, refresh_token from feishu_tokens where user_id=? order by id desc limit 1",
                (1,),
            ).fetchone()
            con.close()
            if not row or not row[0]:
                problems.append("用户 id=1 无飞书令牌（请先飞书登录）")
        except sqlite3.Error as exc:
            problems.append(f"读取数据库失败：{exc}")
    else:
        problems.append(f"数据库不存在：{db_path}")
    if not EXCEL_PATH.exists():
        problems.append(f"表格文件不存在：{EXCEL_PATH}")
    return problems


def gc01_read_sheet(api, rnd, trace):
    text = "读取报名表内容"
    trace["input"] = text
    resp = post_task(api, text, rnd)
    trace["response"] = resp.json()
    body = resp.json()
    item = find_item(body, "sheets")
    ok = resp.status_code == 200 and body.get("status") == "planned" and item and item.get("status") == "executed" and "读取" in item.get("result", "")
    rows = read_sheet() if ok else []
    trace["side_effect"] = {"rows_count": len(rows)}
    return {"pass": ok, "details": item.get("result", "") if item else "未找到子任务", "quality": 100 if ok and len(rows) >= 3 else 60}


def gc02_write_by_key(api, rnd, trace):
    new_phone = "138" + str(random.randint(10000000, 99999999))
    text = f"把报名表里张三的电话更新为{new_phone}"
    trace["input"] = text
    resp = post_task(api, text, rnd)
    body = resp.json()
    trace["response"] = body
    item = find_item(body, "sheets")
    ok_status = resp.status_code == 200 and item and item.get("status") == "pending_confirm" and item.get("confirmation_id")
    pending = get_confirmations(api)
    conf = next((c for c in pending if c["id"] == (item.get("confirmation_id") if item else -1)), None)
    preview = conf["params"] if conf else ""
    trace["locate"] = {"preview": preview}
    trace["confirmation"] = {"id": item.get("confirmation_id") if item else None}
    quality = 0
    if "第2行B列" in preview:
        quality += 40
    if "→" in preview:
        quality += 30
    if "姓名=张三" in preview:
        quality += 30
    if not ok_status:
        return {"pass": False, "details": item.get("result", "") if item else str(body), "quality": quality}
    if not conf or "第2行B列" not in preview:
        return {"pass": False, "details": f"确认页预览缺失：{preview}", "quality": quality}
    before = read_sheet()[1][1]
    dec = decide(api, conf["id"], True)
    trace["confirmation"]["decide"] = dec.json()
    after = read_sheet()[1][1]
    c2 = read_sheet()[1][2]
    trace["side_effect"] = {"before": before, "after": after, "c2": c2}
    ok = dec.status_code == 200 and dec.json().get("execution_result", {}).get("ok") is True and after == new_phone
    if c2 not in (None, ""):
        ok = False
        quality -= 50
    return {"pass": ok, "details": f"B2: {before} -> {after}, C2={c2}", "quality": max(0, quality)}


def gc03_missing_person(api, rnd, trace):
    text = "把报名表里王五的电话更新为13800001111"
    trace["input"] = text
    resp = post_task(api, text, rnd)
    body = resp.json()
    trace["response"] = body
    item = find_item(body, "sheets")
    ok = resp.status_code == 200 and item and item.get("status") == "failed" and "找不到 姓名=王五" in item.get("result", "")
    pending_ids = [c["task_id"] for c in get_confirmations(api)]
    no_conf = str(body.get("task_id")) not in pending_ids
    trace["side_effect"] = {"confirmation_created": not no_conf}
    quality = 100 if ok and no_conf else (50 if item and "找不到" in item.get("result", "") else 0)
    return {"pass": ok and no_conf, "details": item.get("result", "") if item else str(body), "quality": quality}


def gc04_create_calendar(api, rnd, trace):
    suffix = rand_suffix()
    text = f"明天下午3点到4点创建日程：冒烟测试_{suffix}"
    trace["input"] = text
    resp = post_task(api, text, rnd)
    body = resp.json()
    trace["response"] = body
    item = find_item(body, "calendar")
    ok = resp.status_code == 200 and item and item.get("status") == "executed" and "日程已创建" in item.get("result", "")
    event_id = ""
    try:
        event_id = json.loads(item.get("result", "{}")).get("data", {}).get("event_id", "")
    except Exception:
        pass
    trace["side_effect"] = {"event_id": event_id}
    quality = 100
    try:
        start = item.get("args", {}).get("start_ts", "")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        if not start.startswith(tomorrow + "T15:00"):
            quality -= 40
    except Exception:
        pass
    return {"pass": ok and bool(event_id), "details": item.get("result", "") if item else str(body), "quality": max(0, quality), "event_id": event_id}


def gc05_email(api, rnd, trace):
    env = load_env(PROJECT_ROOT / ".env")
    to = env.get("QQ_MAIL_ADDRESS", "")
    text = f"给 {to} 发邮件，主题：冒烟测试，正文：自动化测试邮件 {rand_suffix()}"
    trace["input"] = text
    resp = post_task(api, text, rnd)
    body = resp.json()
    trace["response"] = body
    item = find_item(body, "email")
    if not item or item.get("status") != "pending_confirm":
        return {"pass": False, "details": item.get("result", "") if item else str(body), "quality": 0}
    dec = decide(api, item["confirmation_id"], True)
    trace["confirmation"] = {"id": item["confirmation_id"], "decide": dec.json()}
    ok = dec.status_code == 200 and dec.json().get("execution_result", {}).get("ok") is True
    return {"pass": ok, "details": dec.json().get("execution_result", {}).get("message", ""), "quality": 100 if ok else 50}