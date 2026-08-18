# spec: SPEC-001
"""领域异常（详细设计 §6）。"""


class GatewayError(Exception):
    """网关基础异常。"""


class NoLLMConfiguredError(GatewayError):
    """未配置 LLM provider —— 触发模板回退（非致命）。"""


class GateRejectedError(GatewayError):
    """验证门双路径均失败 —— 熔断（500）。"""

    def __init__(self, message: str = "validation gate rejected", validation: dict | None = None):
        super().__init__(message)
        self.validation = validation or {}


class StoreError(GatewayError):
    """存储层故障。"""
