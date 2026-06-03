import json
from typing import Optional

import db
import config_schema as schema

_cached: Optional[dict] = None


async def load_active_config() -> dict:
    raw_json = await db.load_active_config()
    if raw_json:
        try:
            raw = json.loads(raw_json)
        except Exception:
            raw = None
    else:
        raw = None
    cfg = schema.normalize_config(raw)
    cfg["style"]["report_css"]["valuation_engine"] = "matplotlib"
    return cfg


async def save_config(config: dict, updated_by: str = "admin") -> int:
    config["style"]["report_css"]["valuation_engine"] = "matplotlib"
    return await db.save_config(json.dumps(config), updated_by)


def get_sync_default() -> dict:
    cfg = schema.normalize_config(None)
    cfg["style"]["report_css"]["valuation_engine"] = "matplotlib"
    return cfg
