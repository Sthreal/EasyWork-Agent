#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""办公自动化 Agent 冒烟测试：自动连跑 N 轮三场景（A-F），统计成功率。

用法:
    python scripts/smoke_test.py [--rounds 5]
                                 [--base-url http://127.0.0.1:8001]
                                 [--include-email]
                                 [--cleanup]

场景:
    A 读表格   提交「读取报名表内容」→ executed + rows>=3
    B 改表格   提交「把报名表里张三的电话更新为<随机号>」→ 待确认 + 预览含第2行B列
               → 确认 → 已更新 → 读回文件 B2=新号 且 C2 为空
    C 建日历   提交「明天下午3点到4点创建日程：冒烟测试_xxxx」→ executed + event_id
    D 反问     提交「帮我处理一下」→ need_clarify + question 非空
    E 去重     同一句话连发两次 → task_id 相同
    F 坏输入   空文本 / 坏 JSON → 422（不崩）

退出码:
    0 = 全部通过
    1 = 存在失败场景
    2 = 环境未就绪（后端 / DeepSeek 配置 / 飞书令牌 / Excel 文件）
"""
import argparse
import json
import os
import random
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
import openpyxl

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

EXCEL_PATH = Path(__file__).resolve().parents[2] / "Excel数据" / "报名表.xlsx"
APP_LOG = PROJECT_ROOT / "logs" / "app.log"
REPORT_DIR = PROJECT_ROOT / "logs"
SCENARIOS = ["A", "B", "C", "D", "E", "F"]
SCENE_NAMES = {"A": "读表格", "B": "改表格", "C": "建日历", "D": "反问", "E": "去重", "F": "坏输入", "G": "邮件"}
DEFAULT_BASE_URL = "http://127.0.0.1:8001"


# ---------- 工具函数 ----------

def load_env(path: Path) -> dict:
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


def resolve_db_path(env: dict) -> Path:
    url = env.get("DATABASE_URL", "sqlite:///./office_agent.db")
    if url.startswith("sqlite:///"):
        rel = url[len("sqlite:///"):]
        p = Path(rel)
        return p if p.is_absolute() else (PROJECT_ROOT / p)
    return PROJECT_ROOT / "office_agent.db"


def check_feishu_token() -> tuple[bool, str]:
    """用户 id=1 是否有可用飞书令牌（过期但有 refresh_token 视为可用，后端会自动刷新）。"""
    env = load_env(PROJECT_ROOT / ".env")
    db_path = resolve_db_path(env)
    if not db_path.exists():
        return False, f"数据库不存在：{db_path}"
    try:
        con = sqlite3.connect(db_path)
        try:
            row = con.execute(
                "select access_token, expires_at, refresh_token from feishu_tokens "
                "where user_id=? order by id desc limit 1",
                (1,),
            ).fetchone()
        finally:
            con.close()
    except sqlite3.Error as exc:
        return False, f"读取数据库失败：{exc}"
    if row is None:
        return False, "数据库用户 id=1 无飞书令牌（请先完成飞书登录）"
    access, expires_at, refresh = row
    if not access:
        return False, "用户 id=1 飞书令牌为空"
    expired = True
    if expires_at:
        try:
            expired = datetime.utcnow() >= datetime.fromisoformat(expires_at)
        except ValueError:
            expired = True
    if expired and not refresh:
        return False, "用户 id=1 飞书令牌已过期且无 refresh_token，无法自动刷新（请重新登录）"
    return True, ""


def check_env(base_url: str) -> list[str]:
    problems = []
    try:
        resp = httpx.get(f"{base_url.rstrip('/')}/health", timeout=5)
        if resp.status_code != 200 or resp.json().get("status") != "ok":
            problems.append(f"后端健康检查异常（{base_url}/health 返回 {resp.status_code}）")
    except Exception as exc:
        problems.append(f"后端 {base_url} 不可访问：{exc}")
    env = load_env(PROJECT_ROOT / ".env")
    if not (env.get("LLM_API_KEY") and env.get("LLM_BASE_URL") and env.get("LLM_MODEL")):
        problems.append(".env 未配置 DeepSeek（LLM_API_KEY / LLM_BASE_URL / LLM_MODEL）")
    ok, msg = check_feishu_token()
    if not ok:
        problems.append(msg)
    if not EXCEL_PATH.exists():
        problems.append(f"表格文件不存在：{EXCEL_PATH}")
    return problems


def post_task(api: httpx.Client, text: str, round_no: int = 1):
    return api.post("/api/v1/tasks", json={"text": text, "round": round_no})


def find_item(body: dict, tool: str | None = None, action: str | None = None) -> dict | None:
    for item in body.get("tasks", []):
        if tool and item.get("tool") != tool:
            continue
        args = item.get("args") or {}
        if action and args.get("action") != action:
            continue
        return item
    return None


def parse_result(item: dict | None) -> dict:
    try:
        return json.loads((item or {}).get("result") or "{}")
    except (TypeError, json.JSONDecodeError):
        return {}


def tail_log(n: int = 20) -> str:
    try:
        lines = [ln.rstrip() for ln in APP_LOG.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
        return "\n".join(lines[-n:])
    except OSError:
        return "(无法读取 logs/app.log)"


def new_rec(scene: str, rnd) -> dict:
    return {
        "round": rnd, "scene": scene, "name": SCENE_NAMES.get(scene, scene),
        "result": "PASS", "duration_ms": 0, "details": "",
        "task_id": "", "confirmation_id": "", "event_id": "", "log_tail": "",
    }


def pass_rec(rec: dict, details: str = "") -> dict:
    rec["result"] = "PASS"
    if details:
        rec["details"] = details
    return rec


def fail_rec(rec: dict, reason: str) -> dict:
    rec["result"] = "FAIL"
    rec["details"] = reason
    rec["log_tail"] = tail_log()
    return rec


# ---------- 场景 ----------

def scenario_a(api: httpx.Client, rnd: int, rec: dict) -> dict:
    text = "读取报名表内容"
    try:
        resp = post_task(api, text, rnd)
    except httpx.HTTPError as exc:
        return fail_rec(rec, f"请求异常：{exc}")
    if resp.status_code != 200:
        return fail_rec(rec, f"HTTP {resp.status_code}：{resp.text[:300]}")
    body = resp.json()
    rec["task_id"] = body.get("task_id", "")
    item = find_item(body, tool="sheets", action="read")
    if item is None:
        return fail_rec(rec, f"未拆出 sheets.read 子任务：{json.dumps(body, ensure_ascii=False)[:300]}")
    if item.get("status") != "executed":
        return fail_rec(rec, f"子任务状态={item.get('status')}，期望 executed；result={item.get('result', '')[:200]}")
    result = parse_result(item)
    rows = ((result.get("data") or {}).get("rows")) or []
    if not result.get("ok"):
        return fail_rec(rec, f"工具返回失败：{result.get('message', '')}")
    if len(rows) < 3:
        return fail_rec(rec, f"读取行数={len(rows)} < 3（文件应含 3 行）")
    rec["details"] = f"task_id={rec['task_id']} rows={len(rows)} 首行={rows[0]}"
    return pass_rec(rec, rec["details"])


def scenario_b(api: httpx.Client, rnd: int, rec: dict) -> dict:
    phone = f"138{random.randint(10000000, 99999999)}"
    text = f"把报名表里张三的电话更新为{phone}"
    try:
        resp = post_task(api, text, rnd)
    except httpx.HTTPError as exc:
        return fail_rec(rec, f"请求异常：{exc}")
    if resp.status_code != 200:
        return fail_rec(rec, f"HTTP {resp.status_code}：{resp.text[:300]}")
    body = resp.json()
    rec["task_id"] = body.get("task_id", "")
    item = find_item(body, tool="sheets", action="write_by_key")
    if item is None:
        return fail_rec(rec, f"未拆出 sheets.write_by_key 子任务：{json.dumps(body, ensure_ascii=False)[:300]}")
    if item.get("status") != "pending_confirm":
        return fail_rec(rec, f"子任务状态={item.get('status')}，期望 pending_confirm（高危未拦截？）；result={item.get('result', '')[:200]}")
    cid = item.get("confirmation_id")
    rec["confirmation_id"] = str(cid) if cid is not None else ""
    if not cid:
        return fail_rec(rec, "confirmation_id 为空")
    # 预览在第 2 行 B 列：从待确认列表读确认记录 params 验证
    try:
        list_resp = api.get("/api/v1/confirmations")
    except httpx.HTTPError as exc:
        return fail_rec(rec, f"查询待确认列表异常：{exc}")
    preview = ""
    if list_resp.status_code == 200:
        for c in list_resp.json().get("items", []):
            if c.get("id") == cid:
                preview = c.get("params", "")
                break
    if "第2行B列" not in preview:
        return fail_rec(rec, f"预览未包含「第2行B列」：preview={preview[:300]}（确认记录 id={cid}）")
    try:
        resp2 = api.post(f"/api/v1/confirmations/{cid}/decide", json={"approve": True})
    except httpx.HTTPError as exc:
        return fail_rec(rec, f"确认请求异常：{exc}")
    if resp2.status_code != 200:
        return fail_rec(rec, f"确认 HTTP {resp2.status_code}：{resp2.text[:300]}")
    body2 = resp2.json()
    exec_res = body2.get("execution_result") or {}
    if body2.get("status") != "approved" or not exec_res.get("ok"):
        return fail_rec(rec, f"确认后执行失败：status={body2.get('status')} execution_result={json.dumps(body2, ensure_ascii=False)[:300]}")
    # 读回文件二次验证
    try:
        wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
        ws = wb.active
        b2 = ws.cell(row=2, column=2).value
        c2 = ws.cell(row=2, column=3).value
        wb.close()
    except Exception as exc:
        return fail_rec(rec, f"读回文件失败：{exc}")
    if str(b2) != phone:
        return fail_rec(rec, f"文件 B2={b2!r}，期望 {phone}（写入未生效）")
    if c2 not in (None, ""):
        return fail_rec(rec, f"文件 C2={c2!r}，期望为空（其它单元格被破坏？）")
    rec["details"] = f"task_id={rec['task_id']} confirmation_id={cid} phone={phone} B2={b2} C2={c2!r} 预览={preview[:60]}"
    return pass_rec(rec, rec["details"])


def scenario_c(api: httpx.Client, rnd: int, rec: dict, event_ids: list[dict]) -> dict:
    summary = f"冒烟测试_{rnd:04d}"
    text = f"明天下午3点到4点创建日程：{summary}"
    try:
        resp = post_task(api, text, rnd)
    except httpx.HTTPError as exc:
        return fail_rec(rec, f"请求异常：{exc}")
    if resp.status_code != 200:
        return fail_rec(rec, f"HTTP {resp.status_code}：{resp.text[:300]}")
    body = resp.json()
    rec["task_id"] = body.get("task_id", "")
    item = find_item(body, tool="calendar", action="create")
    if item is None:
        return fail_rec(rec, f"未拆出 calendar.create 子任务：{json.dumps(body, ensure_ascii=False)[:300]}")
    if item.get("status") != "executed":
        return fail_rec(rec, f"子任务状态={item.get('status')}，期望 executed；result={item.get('result', '')[:200]}")
    result = parse_result(item)
    event_id = ((result.get("data") or {}).get("event_id")) or ""
    if not result.get("ok") or not event_id:
        return fail_rec(rec, f"创建失败：{result.get('message', '')} data={result.get('data')}")
    rec["event_id"] = event_id
    event_ids.append({"round": rnd, "event_id": event_id, "summary": summary})
    rec["details"] = f"task_id={rec['task_id']} event_id={event_id} summary={summary}"
    return pass_rec(rec, rec["details"])


def scenario_d(api: httpx.Client, rnd: int, rec: dict) -> dict:
    text = "帮我处理一下"
    try:
        resp = post_task(api, text, rnd)
    except httpx.HTTPError as exc:
        return fail_rec(rec, f"请求异常：{exc}")
    if resp.status_code != 200:
        return fail_rec(rec, f"HTTP {resp.status_code}：{resp.text[:300]}")
    body = resp.json()
    rec["task_id"] = body.get("task_id", "")
    if body.get("status") != "need_clarify":
        return fail_rec(rec, f"status={body.get('status')}，期望 need_clarify；body={json.dumps(body, ensure_ascii=False)[:300]}")
    question = body.get("question") or ""
    if not question.strip():
        return fail_rec(rec, "question 为空")
    rec["details"] = f"task_id={rec['task_id']} question={question[:80]}"
    return pass_rec(rec, rec["details"])


def scenario_e(api: httpx.Client, rnd: int, rec: dict) -> dict:
    text = "读取报名表内容"
    try:
        r1 = post_task(api, text, rnd)
        r2 = post_task(api, text, rnd)
    except httpx.HTTPError as exc:
        return fail_rec(rec, f"请求异常：{exc}")
    if r1.status_code != 200 or r2.status_code != 200:
        return fail_rec(rec, f"HTTP r1={r1.status_code} r2={r2.status_code}：{r1.text[:150]} | {r2.text[:150]}")
    t1 = r1.json().get("task_id", "")
    t2 = r2.json().get("task_id", "")
    rec["task_id"] = t1
    if not t1 or not t2 or t1 != t2:
        return fail_rec(rec, f"两次 task_id 不一致：{t1!r} vs {t2!r}")
    rec["details"] = f"task_id={t1}（两次相同，去重生效）"
    return pass_rec(rec, rec["details"])


def scenario_f(api: httpx.Client, rnd: int, rec: dict) -> dict:
    try:
        r1 = api.post("/api/v1/tasks", json={"text": ""})
        r2 = api.post("/api/v1/tasks", content="not-json", headers={"Content-Type": "application/json"})
    except httpx.HTTPError as exc:
        return fail_rec(rec, f"请求异常：{exc}")
    if r1.status_code != 422 or r2.status_code != 422:
        return fail_rec(rec, f"期望 422：空文本={r1.status_code} 坏JSON={r2.status_code}")
    rec["details"] = "空文本=422 坏JSON=422"
    return pass_rec(rec, rec["details"])


def scenario_g(api: httpx.Client, rec: dict) -> dict:
    """可选邮件场景：只发 1 封到专用测试邮箱（即配置的 QQ 邮箱本身），确认后验证发送结果。"""
    env = load_env(PROJECT_ROOT / ".env")
    to = env.get("QQ_MAIL_ADDRESS", "")
    if not to:
        return fail_rec(rec, "未配置 QQ_MAIL_ADDRESS，无法发测试邮件")
    subject = f"冒烟测试邮件_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    text = f"给 {to} 发邮件，主题：{subject}，正文：这是一封办公自动化 Agent 冒烟测试邮件，请忽略。"
    try:
        resp = post_task(api, text)
    except httpx.HTTPError as exc:
        return fail_rec(rec, f"请求异常：{exc}")
    if resp.status_code != 200:
        return fail_rec(rec, f"HTTP {resp.status_code}：{resp.text[:300]}")
    body = resp.json()
    rec["task_id"] = body.get("task_id", "")
    item = find_item(body, tool="email", action="send")
    if item is None or item.get("status") != "pending_confirm" or not item.get("confirmation_id"):
        return fail_rec(rec, f"未拆出待确认 email.send：{json.dumps(body, ensure_ascii=False)[:300]}")
    cid = item["confirmation_id"]
    rec["confirmation_id"] = str(cid)
    try:
        resp2 = api.post(f"/api/v1/confirmations/{cid}/decide", json={"approve": True})
    except httpx.HTTPError as exc:
        return fail_rec(rec, f"确认请求异常：{exc}")
    if resp2.status_code != 200:
        return fail_rec(rec, f"确认 HTTP {resp2.status_code}：{resp2.text[:300]}")
    exec_res = resp2.json().get("execution_result") or {}
    msg = exec_res.get("message", "")
    if not exec_res.get("ok") or "已发送" not in msg:
        return fail_rec(rec, f"邮件发送失败：{json.dumps(resp2.json(), ensure_ascii=False)[:300]}")
    rec["details"] = f"task_id={rec['task_id']} confirmation_id={cid} to={to} subject={subject} message={msg}"
    return pass_rec(rec, rec["details"])


# ---------- 清理 ----------

def cleanup_events(event_ids: list[dict]) -> list[str]:
    results = []
    if not event_ids:
        return ["本次运行未创建日程，无需清理"]
    try:
        from backend.db import SessionLocal
        from backend.feishu.token_store import get_valid_token
        db = SessionLocal()
        try:
            token = get_valid_token(db, 1).access_token
        finally:
            db.close()
    except Exception as exc:
        return [f"获取飞书令牌失败，跳过清理：{exc}"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    for e in event_ids:
        url = f"https://open.feishu.cn/open-apis/calendar/v4/calendars/primary/events/{e['event_id']}"
        try:
            resp = httpx.delete(url, headers=headers, timeout=15)
            body = resp.json()
            ok = resp.status_code == 200 and body.get("code", 0) == 0
            results.append(
                f"第{e['round']}轮 {e['summary']} {e['event_id']} -> {'已删除' if ok else f'失败 code={body.get('code')} msg={body.get('msg')}'}"
            )
        except Exception as exc:
            results.append(f"第{e['round']}轮 {e['summary']} {e['event_id']} -> 删除异常：{exc}")
    return results


# ---------- 汇总与报表 ----------

def compute_summary(results: list[dict]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r["result"] == "PASS")
    failed = total - passed
    rate = (passed / total * 100) if total else 0.0
    return {"total": total, "passed": passed, "failed": failed, "rate": rate}


def format_report(args, results: list[dict], summary: dict, cleanup_results: list[str]) -> str:
    lines = []
    lines.append("=" * 70)
    lines.append("办公自动化 Agent 冒烟测试报告")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(
        f"运行参数：rounds={args.rounds} include_email={args.include_email} "
        f"cleanup={args.cleanup} base_url={args.base_url}"
    )
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"{'轮次':<8}{'场景':<8}{'结果':<6}{'耗时(ms)':<10}详情")
    for r in results:
        lines.append(f"{str(r['round']):<8}{r['name']:<8}{r['result']:<6}{r['duration_ms']:<10}{r['details']}")
    lines.append("")
    lines.append("-" * 70)
    lines.append(
        f"汇总：总场景数={summary['total']}，通过={summary['passed']}，"
        f"失败={summary['failed']}，成功率={summary['rate']:.2f}%"
    )
    lines.append("")
    fails = [r for r in results if r["result"] == "FAIL"]
    if fails:
        lines.append("失败明细：")
        for i, r in enumerate(fails, 1):
            lines.append(f"{i}) 第{r['round']}轮 {r['name']}：{r['details']}")
            if r.get("task_id"):
                lines.append(f"   task_id={r['task_id']}")
            if r.get("confirmation_id"):
                lines.append(f"   confirmation_id={r['confirmation_id']}")
            if r.get("event_id"):
                lines.append(f"   event_id={r['event_id']}")
            if r.get("log_tail"):
                lines.append("   --- 后端日志最近20行 ---")
                for line in r["log_tail"].splitlines():
                    lines.append("   " + line)
                lines.append("   ------------------------")
    else:
        lines.append("无失败，全部通过。")
    if args.cleanup:
        lines.append("")
        lines.append("清理结果：")
        lines.extend(cleanup_results)
    return "\n".join(lines)


# ---------- 主流程 ----------

def parse_args():
    parser = argparse.ArgumentParser(description="办公自动化 Agent 冒烟测试")
    parser.add_argument("--rounds", type=int, default=5, help="连跑轮数（默认 5）")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"后端地址（默认 {DEFAULT_BASE_URL}）")
    parser.add_argument("--include-email", action="store_true", help="额外向专用测试邮箱发 1 封邮件并验证（默认跳过）")
    parser.add_argument("--cleanup", action="store_true", help="跑完后删除本次创建的飞书日程")
    args = parser.parse_args()
    if args.rounds < 1:
        parser.error("--rounds 必须 >= 1")
    return args


def main() -> int:
    args = parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    problems = check_env(args.base_url)
    if problems:
        for p in problems:
            print(f"环境未就绪：{p}")
        return 2
    print("环境检查通过：后端健康 / DeepSeek 已配置 / 飞书令牌可用 / 表格文件存在")
    api = httpx.Client(base_url=args.base_url.rstrip("/"), timeout=60)
    results: list[dict] = []
    event_ids: list[dict] = []
    try:
        for rnd in range(1, args.rounds + 1):
            print(f"\n===== 第 {rnd}/{args.rounds} 轮 =====")
            for scene in SCENARIOS:
                rec = new_rec(scene, rnd)
                start = time.perf_counter()
                if scene == "A":
                    scenario_a(api, rnd, rec)
                elif scene == "B":
                    scenario_b(api, rnd, rec)
                elif scene == "C":
                    scenario_c(api, rnd, rec, event_ids)
                elif scene == "D":
                    scenario_d(api, rnd, rec)
                elif scene == "E":
                    scenario_e(api, rnd, rec)
                elif scene == "F":
                    scenario_f(api, rnd, rec)
                rec["duration_ms"] = int((time.perf_counter() - start) * 1000)
                results.append(rec)
                print(f"  第{rnd}轮 {rec['name']} {rec['result']} ({rec['duration_ms']}ms) {rec['details'][:160]}")
        if args.include_email:
            rec = new_rec("G", "EMAIL")
            start = time.perf_counter()
            scenario_g(api, rec)
            rec["duration_ms"] = int((time.perf_counter() - start) * 1000)
            results.append(rec)
            print(f"  邮件 {rec['result']} ({rec['duration_ms']}ms) {rec['details'][:160]}")
    finally:
        api.close()
    cleanup_results = cleanup_events(event_ids) if args.cleanup else []
    summary = compute_summary(results)
    report = format_report(args, results, summary, cleanup_results)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"smoke_report_{ts}.txt"
    report_path.write_text(report, encoding="utf-8")
    print("\n" + "=" * 70)
    print(f"汇总：总场景数={summary['total']}，通过={summary['passed']}，失败={summary['failed']}，成功率={summary['rate']:.2f}%")
    if summary["failed"]:
        print("失败明细：")
        for i, r in enumerate([x for x in results if x["result"] == "FAIL"], 1):
            print(f"  {i}) 第{r['round']}轮 {r['name']}：{r['details'][:200]}")
    print(f"报表已写入：{report_path}")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())