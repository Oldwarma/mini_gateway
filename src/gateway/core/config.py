# spec: SPEC-001
"""配置加载（详细设计 §4.14）。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ..exceptions import GatewayError


@dataclass
class LLMConfig:
    provider: str = "none"  # openai | anthropic | none
    model: str = ""
    api_key_env: str = ""


@dataclass
class GateConfig:
    latency_budget_seconds: float = 5.0


@dataclass
class CompositionConfig:
    default: str = "llm"  # llm | template
    fallback: str = "template"


@dataclass
class SourceConfig:
    id: str
    name: str
    type: str = "file"
    path: str = ""
    url: str = ""
    policy: str = "allowed"


@dataclass
class ExternalAgentConfig:
    name: str
    url: str
    description: str = ""


@dataclass
class Config:
    llm: LLMConfig
    gate: GateConfig
    composition: CompositionConfig
    sources: list[SourceConfig] = field(default_factory=list)
    data_dir: str = "data"
    external_agents: list[ExternalAgentConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Config":
        llm_d = d.get("llm", {}) or {}
        gate_d = d.get("gate", {}) or {}
        comp_d = d.get("composition", {}) or {}
        return cls(
            llm=LLMConfig(
                provider=llm_d.get("provider", "none"),
                model=llm_d.get("model", ""),
                api_key_env=llm_d.get("api_key_env", ""),
            ),
            gate=GateConfig(latency_budget_seconds=gate_d.get("latency_budget_seconds", 5.0)),
            composition=CompositionConfig(
                default=comp_d.get("default", "llm"),
                fallback=comp_d.get("fallback", "template"),
            ),
            sources=[SourceConfig(**s) for s in d.get("sources", [])],
            data_dir=d.get("data_dir", "data"),
            external_agents=[ExternalAgentConfig(**x) for x in d.get("external_agents", [])],
        )


def load_config(path: str | Path = "config.yaml") -> Config:
    """读取 YAML 配置，生成 Config 对象。"""
    p = Path(path)
    if not p.exists():
        raise GatewayError(f"config file not found: {path}")
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return Config.from_dict(data)
