"""
配置管理模块
集中管理系统配置和用户偏好
"""
import os
import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class ConfigSchema:
    """配置结构定义"""
    collection: dict[str, Any]
    processing: dict[str, Any]
    ui: dict[str, Any]
    system: dict[str, Any]


@dataclass
class ConfigValidator:
    """配置验证器"""
    errors: list[str] = field(default_factory=list)

    def validate(self, config: dict[str, Any]) -> bool:
        """
        验证配置有效性

        Args:
            config: 配置字典

        Returns:
            是否验证通过
        """
        self.errors = []

        # 验证顶层结构
        required_sections = ["collection", "processing", "ui", "system"]
        for section in required_sections:
            if section not in config:
                self.errors.append(f"缺少必需的配置节: {section}")

        # 验证 collection 配置
        if "collection" in config:
            collection = config["collection"]
            if "keywords" in collection and not isinstance(collection["keywords"], list):
                self.errors.append("collection.keywords 必须是列表")
            if "cities" in collection and not isinstance(collection["cities"], list):
                self.errors.append("collection.cities 必须是列表")
            if "max_results_per_source" in collection:
                if not isinstance(collection["max_results_per_source"], int) or collection["max_results_per_source"] <= 0:
                    self.errors.append("collection.max_results_per_source 必须是正整数")

        # 验证 system 配置
        if "system" in config:
            system = config["system"]
            if "request_delay" in system:
                if not isinstance(system["request_delay"], (int, float)) or system["request_delay"] < 0:
                    self.errors.append("system.request_delay 必须是非负数")
            if "max_retries" in system:
                if not isinstance(system["max_retries"], int) or system["max_retries"] < 0:
                    self.errors.append("system.max_retries 必须是非负整数")

        return len(self.errors) == 0

    def get_errors(self) -> list[str]:
        """获取验证错误列表"""
        return self.errors.copy()


class ConfigManager:
    """
    配置管理器
    支持配置加载、验证、热更新和多环境
    """

    DEFAULT_CONFIG_FILE = "config/default.yaml"
    USER_CONFIG_FILE = "config/user.yaml"
    ENV_CONFIG_PREFIX = "DEEPRESEARCH_"

    def __init__(
        self,
        config_file: Optional[str] = None,
        validate: bool = True
    ) -> None:
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径
            validate: 是否在加载时验证
        """
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.validate_on_load = validate
        self._config: dict[str, Any] = {}
        self._original_config: dict[str, Any] = {}
        self._validator = ConfigValidator()
        self._hot_update_listeners: list[callable] = []

    def _get_default_config(self) -> dict[str, Any]:
        """获取默认配置"""
        return {
            "collection": {
                "keywords": ["Python", "后端开发"],
                "exclude_keywords": ["实习", "兼职"],
                "cities": ["北京", "上海", "深圳"],
                "salary_range": {"min": 15000, "max": 50000},
                "max_results_per_source": 50,
            },
            "processing": {
                "deduplicate": True,
                "similarity_threshold": 0.85,
                "normalize_salary": True,
                "normalize_location": True,
            },
            "ui": {
                "report_format": "markdown",
                "page_size": 20,
                "theme": "light",
            },
            "system": {
                "request_delay": 1.0,
                "max_retries": 3,
                "timeout": 30,
                "log_level": "INFO",
            }
        }

    def _load_from_file(self, file_path: str) -> dict[str, Any]:
        """从文件加载配置"""
        import yaml

        path = Path(file_path)
        if not path.exists():
            return {}

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _load_from_env(self) -> dict[str, Any]:
        """从环境变量加载配置"""
        env_config: dict[str, Any] = {}

        # 检查环境变量前缀
        for key, value in os.environ.items():
            if key.startswith(self.ENV_CONFIG_PREFIX):
                # 解析嵌套键，如 DEEPRESEARCH_COLLECTION_KEYWORDS -> collection.keywords
                config_key = key[len(self.ENV_CONFIG_PREFIX):].lower()
                parts = config_key.split("_", 1)

                if len(parts) >= 2:
                    section = parts[0]
                    field = parts[1]

                    if section not in env_config:
                        env_config[section] = {}

                    # 尝试解析为适当的类型
                    if field == "keywords" or field == "cities" or field == "exclude_keywords":
                        env_config[section][field] = [v.strip() for v in value.split(",")]
                    elif field == "max_results_per_source" or field == "max_retries" or field == "timeout":
                        env_config[section][field] = int(value)
                    elif field == "request_delay":
                        env_config[section][field] = float(value)
                    elif value.lower() in ("true", "false"):
                        env_config[section][field] = value.lower() == "true"
                    else:
                        env_config[section][field] = value

        return env_config

    def _merge_config(
        self,
        base: dict[str, Any],
        override: dict[str, Any]
    ) -> dict[str, Any]:
        """深度合并配置"""
        result = copy.deepcopy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = copy.deepcopy(value)

        return result

    def load(self, env: Optional[str] = None) -> "ConfigManager":
        """
        加载配置

        Args:
            env: 环境名称 (dev, test, prod)

        Returns:
            self
        """
        # 获取默认配置
        self._config = self._get_default_config()
        self._original_config = copy.deepcopy(self._config)

        # 加载环境特定配置
        if env:
            env_file = f"config/{env}.yaml"
            env_config = self._load_from_file(env_file)
            self._config = self._merge_config(self._config, env_config)

        # 加载默认用户配置
        user_config = self._load_from_file(self.USER_CONFIG_FILE)
        self._config = self._merge_config(self._config, user_config)

        # 加载环境变量配置（最高优先级）
        env_config = self._load_from_env()
        self._config = self._merge_config(self._config, env_config)

        # 验证配置
        if self.validate_on_load:
            if not self._validator.validate(self._config):
                raise ValueError(f"配置验证失败: {self._validator.get_errors()}")

        return self

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key_path: 配置键路径，如 "collection.keywords"
            default: 默认值

        Returns:
            配置值
        """
        keys = key_path.split(".")
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> "ConfigManager":
        """
        设置配置值

        Args:
            key_path: 配置键路径，如 "collection.keywords"
            value: 配置值

        Returns:
            self
        """
        keys = key_path.split(".")
        config = self._config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = copy.deepcopy(value)
        return self

    def hot_update(self, key_path: str, value: Any) -> "ConfigManager":
        """
        热更新配置（通知监听器）

        Args:
            key_path: 配置键路径
            value: 新配置值

        Returns:
            self
        """
        self.set(key_path, value)

        # 通知所有监听器
        for listener in self._hot_update_listeners:
            listener(key_path, value)

        return self

    def add_hot_update_listener(self, listener: callable) -> "ConfigManager":
        """
        添加热更新监听器

        Args:
            listener: 回调函数 (key_path, value) -> None

        Returns:
            self
        """
        self._hot_update_listeners.append(listener)
        return self

    def remove_hot_update_listener(self, listener: callable) -> "ConfigManager":
        """移除热更新监听器"""
        if listener in self._hot_update_listeners:
            self._hot_update_listeners.remove(listener)
        return self

    def get_all(self) -> dict[str, Any]:
        """获取完整配置副本"""
        return copy.deepcopy(self._config)

    def get_section(self, section: str) -> dict[str, Any]:
        """获取配置节"""
        if section in self._config:
            return copy.deepcopy(self._config[section])
        return {}

    def reset(self) -> "ConfigManager":
        """重置为初始配置"""
        self._config = copy.deepcopy(self._original_config)
        return self

    def validate(self) -> tuple[bool, list[str]]:
        """
        验证当前配置

        Returns:
            (是否通过, 错误列表)
        """
        is_valid = self._validator.validate(self._config)
        return is_valid, self._validator.get_errors()

    def get_environments(self) -> list[str]:
        """获取可用的环境列表"""
        config_dir = Path("config")
        if not config_dir.exists():
            return []

        envs = []
        for f in config_dir.iterdir():
            if f.suffix == ".yaml" and f.stem not in ("default", "user"):
                envs.append(f.stem)

        return sorted(envs)

    def save_user_config(self) -> None:
        """保存用户配置到文件"""
        user_config_path = Path(self.USER_CONFIG_FILE)
        user_config_path.parent.mkdir(parents=True, exist_ok=True)

        # 只保存与默认配置的差异部分
        import yaml

        with open(user_config_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)


def create_default_manager() -> ConfigManager:
    """创建默认配置管理器"""
    return ConfigManager().load()


def create_manager_with_env(env: str) -> ConfigManager:
    """创建指定环境的配置管理器"""
    return ConfigManager().load(env=env)
