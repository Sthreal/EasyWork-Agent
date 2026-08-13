"""高危判定（删除/覆盖/发送/外发等）。"""
_HIGH_RISK_KEYWORDS = ("删除", "覆盖", "发送", "外发", "更新", "修改", "写入", "编辑")


def is_high_risk(action: str, target: str = "", params: str = "") -> bool:
    """动作/对象/参数包含高危关键词则判定为高危。"""
    text = f"{action} {target} {params}"
    return any(k in text for k in _HIGH_RISK_KEYWORDS)