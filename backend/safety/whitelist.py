"""敏感操作白名单：只允许明确授权的工具动作。"""
ALLOWED_OPERATIONS = {
    "email": {"send", "read"},
    "sheets": {"read", "write", "write_by_key", "aggregate"},
    "calendar": {"create", "update"},
}


def is_allowed(tool: str, action: str) -> bool:
    """工具+动作是否在白名单内。"""
    return tool in ALLOWED_OPERATIONS and action in ALLOWED_OPERATIONS[tool]