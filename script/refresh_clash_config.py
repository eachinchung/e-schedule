import asyncio
from typing import List

import yaml
from aiofile import async_open
from loguru import logger
from pydantic import BaseModel, Field

from components.config import get_real_path
from components.monitor import monitor
from components.requests import Response, close_requests, get, register_requests
from components.retry import retry
from setting import setting

PROXY_GROUP_SET = {
    "ð AdBlock",
    "ð åºç¨åå",
    "ð¯ å¨çç´è¿",
    "ðº å·´åå§ç¹",
    "ð å½å¤åªä½",
    "ð§± å¿«éç ´å¢",
    "ð§ æå¨åæ¢",
    "ð°ð· é©å½èç¹",
    "â»ï¸ èªå¨éæ©",
    "ð¨ð³ å°æ¹¾èç¹",
    "ð æ¼ç½ä¹é±¼",
    "ð¯ æéè½¬ç§»",
    "ð å½ååªä½",
    "ðº åå©åå©",
    "ð å¹¿åæ¦æª",
    "ð è¹ææå¡",
    "ð® æ¸¸æå¹³å°",
    "ðºð² ç¾å½èç¹",
    "ð­ð° é¦æ¸¯èç¹",
    "ð¹ æ²¹ç®¡è§é¢",
    "ð® è´è½½åè¡¡",
    "ð² çµæ¥æ¶æ¯",
    "ð¯ðµ æ¥æ¬èç¹",
    "âï¸ å¾®è½¯äºç",
    "ð èç¹éæ©",
    "âï¸ å¾®è½¯æå¡",
    "ð¶ ç½æé³ä¹",
    "ð¢ è°·æ­FCM",
    "ð¥ å¥é£è§é¢",
    "ð¡ï¸ éç§é²æ¤",
}

PROXY_GROUPS = [
    {
        "name": "ð èç¹éæ©",
        "type": "select",
        "proxies": [
            "ð§± å¿«éç ´å¢",
            "â»ï¸ èªå¨éæ©",
            "ð¯ æéè½¬ç§»",
            "ð® è´è½½åè¡¡",
            "ð­ð° é¦æ¸¯èç¹",
            "ð¨ð³ å°æ¹¾èç¹",
            "ð¯ðµ æ¥æ¬èç¹",
            "ðºð² ç¾å½èç¹",
            "ð°ð· é©å½èç¹",
            "ð§ æå¨åæ¢",
            "DIRECT",
        ],
    },
    {"name": "ð§ æå¨åæ¢", "type": "select", "proxies": []},
    {
        "name": "ð§± å¿«éç ´å¢",
        "type": "url-test",
        "url": "http://www.gstatic.com/generate_204",
        "interval": 300,
        "proxies": [],
    },
    {
        "name": "â»ï¸ èªå¨éæ©",
        "type": "url-test",
        "url": "http://www.gstatic.com/generate_204",
        "interval": 300,
        "proxies": [],
    },
    {
        "name": "ð¯ æéè½¬ç§»",
        "type": "fallback",
        "url": "http://www.gstatic.com/generate_204",
        "interval": 300,
        "proxies": [],
    },
    {
        "name": "ð® è´è½½åè¡¡",
        "type": "load-balance",
        "strategy": "consistent-hashing",
        "url": "http://www.gstatic.com/generate_204",
        "interval": 300,
        "proxies": [],
    },
    {
        "name": "ð² çµæ¥æ¶æ¯",
        "type": "select",
        "proxies": [
            "ð èç¹éæ©",
            "ð§± å¿«éç ´å¢",
            "â»ï¸ èªå¨éæ©",
            "ð­ð° é¦æ¸¯èç¹",
            "ð¨ð³ å°æ¹¾èç¹",
            "ð¯ðµ æ¥æ¬èç¹",
            "ðºð² ç¾å½èç¹",
            "ð°ð· é©å½èç¹",
            "ð§ æå¨åæ¢",
            "DIRECT",
        ],
    },
    {
        "name": "ð¹ æ²¹ç®¡è§é¢",
        "type": "select",
        "proxies": [
            "ð èç¹éæ©",
            "ð§± å¿«éç ´å¢",
            "â»ï¸ èªå¨éæ©",
            "ð­ð° é¦æ¸¯èç¹",
            "ð¨ð³ å°æ¹¾èç¹",
            "ð¯ðµ æ¥æ¬èç¹",
            "ðºð² ç¾å½èç¹",
            "ð°ð· é©å½èç¹",
            "ð§ æå¨åæ¢",
            "DIRECT",
        ],
    },
    {
        "name": "ð¥ å¥é£è§é¢",
        "type": "select",
        "proxies": [
            "ð èç¹éæ©",
            "ð§± å¿«éç ´å¢",
            "â»ï¸ èªå¨éæ©",
            "ð­ð° é¦æ¸¯èç¹",
            "ð¨ð³ å°æ¹¾èç¹",
            "ð¯ðµ æ¥æ¬èç¹",
            "ðºð² ç¾å½èç¹",
            "ð°ð· é©å½èç¹",
            "ð§ æå¨åæ¢",
            "DIRECT",
        ],
    },
    {"name": "ðº å·´åå§ç¹", "type": "select", "proxies": ["ð¨ð³ å°æ¹¾èç¹", "ð èç¹éæ©", "ð§ æå¨åæ¢", "DIRECT"]},
    {"name": "ðº åå©åå©", "type": "select", "proxies": ["ð¯ å¨çç´è¿", "ð¨ð³ å°æ¹¾èç¹", "ð­ð° é¦æ¸¯èç¹"]},
    {
        "name": "ð å½å¤åªä½",
        "type": "select",
        "proxies": [
            "ð èç¹éæ©",
            "ð§± å¿«éç ´å¢",
            "â»ï¸ èªå¨éæ©",
            "ð­ð° é¦æ¸¯èç¹",
            "ð¨ð³ å°æ¹¾èç¹",
            "ð¯ðµ æ¥æ¬èç¹",
            "ðºð² ç¾å½èç¹",
            "ð°ð· é©å½èç¹",
            "ð§ æå¨åæ¢",
            "DIRECT",
        ],
    },
    {
        "name": "ð å½ååªä½",
        "type": "select",
        "proxies": ["DIRECT", "ð­ð° é¦æ¸¯èç¹", "ð¨ð³ å°æ¹¾èç¹", "ð¯ðµ æ¥æ¬èç¹", "ð§ æå¨åæ¢"],
    },
    {
        "name": "ð¢ è°·æ­FCM",
        "type": "select",
        "proxies": [
            "ð èç¹éæ©",
            "ðºð² ç¾å½èç¹",
            "ð­ð° é¦æ¸¯èç¹",
            "ð¨ð³ å°æ¹¾èç¹",
            "ð¯ðµ æ¥æ¬èç¹",
            "ð°ð· é©å½èç¹",
            "ð§ æå¨åæ¢",
            "DIRECT",
        ],
    },
    {
        "name": "âï¸ å¾®è½¯äºç",
        "type": "select",
        "proxies": [
            "DIRECT",
            "ð èç¹éæ©",
            "ðºð² ç¾å½èç¹",
            "ð­ð° é¦æ¸¯èç¹",
            "ð¨ð³ å°æ¹¾èç¹",
            "ð¯ðµ æ¥æ¬èç¹",
            "ð°ð· é©å½èç¹",
            "ð§ æå¨åæ¢",
        ],
    },
    {
        "name": "âï¸ å¾®è½¯æå¡",
        "type": "select",
        "proxies": [
            "ð èç¹éæ©",
            "ðºð² ç¾å½èç¹",
            "ð­ð° é¦æ¸¯èç¹",
            "ð¨ð³ å°æ¹¾èç¹",
            "ð¯ðµ æ¥æ¬èç¹",
            "ð°ð· é©å½èç¹",
            "ð§ æå¨åæ¢",
            "DIRECT",
        ],
    },
    {
        "name": "ð è¹ææå¡",
        "type": "select",
        "proxies": [
            "DIRECT",
            "ð èç¹éæ©",
            "ðºð² ç¾å½èç¹",
            "ð­ð° é¦æ¸¯èç¹",
            "ð¨ð³ å°æ¹¾èç¹",
            "ð¯ðµ æ¥æ¬èç¹",
            "ð°ð· é©å½èç¹",
            "ð§ æå¨åæ¢",
        ],
    },
    {
        "name": "ð® æ¸¸æå¹³å°",
        "type": "select",
        "proxies": [
            "DIRECT",
            "ð èç¹éæ©",
            "ðºð² ç¾å½èç¹",
            "ð­ð° é¦æ¸¯èç¹",
            "ð¨ð³ å°æ¹¾èç¹",
            "ð¯ðµ æ¥æ¬èç¹",
            "ð°ð· é©å½èç¹",
            "ð§ æå¨åæ¢",
        ],
    },
    {"name": "ð¶ ç½æé³ä¹", "type": "select", "proxies": ["DIRECT", "ð èç¹éæ©", "â»ï¸ èªå¨éæ©"]},
    {"name": "ð¯ å¨çç´è¿", "type": "select", "proxies": ["DIRECT", "ð èç¹éæ©", "â»ï¸ èªå¨éæ©"]},
    {"name": "ð å¹¿åæ¦æª", "type": "select", "proxies": ["REJECT", "DIRECT"]},
    {"name": "ð åºç¨åå", "type": "select", "proxies": ["REJECT", "DIRECT"]},
    {"name": "ð AdBlock", "type": "select", "proxies": ["REJECT", "DIRECT"]},
    {"name": "ð¡ï¸ éç§é²æ¤", "type": "select", "proxies": ["REJECT", "DIRECT"]},
    {
        "name": "ð æ¼ç½ä¹é±¼",
        "type": "select",
        "proxies": [
            "ð èç¹éæ©",
            "ð§± å¿«éç ´å¢",
            "â»ï¸ èªå¨éæ©",
            "DIRECT",
            "ð­ð° é¦æ¸¯èç¹",
            "ð¨ð³ å°æ¹¾èç¹",
            "ð¯ðµ æ¥æ¬èç¹",
            "ðºð² ç¾å½èç¹",
            "ð°ð· é©å½èç¹",
            "ð§ æå¨åæ¢",
        ],
    },
    {
        "name": "ð­ð° é¦æ¸¯èç¹",
        "type": "url-test",
        "url": "http://www.gstatic.com/generate_204",
        "interval": 300,
        "proxies": [],
    },
    {
        "name": "ð¨ð³ å°æ¹¾èç¹",
        "type": "url-test",
        "url": "http://www.gstatic.com/generate_204",
        "interval": 300,
        "proxies": [],
    },
    {
        "name": "ðºð² ç¾å½èç¹",
        "type": "url-test",
        "url": "http://www.gstatic.com/generate_204",
        "interval": 300,
        "proxies": [],
    },
    {
        "name": "ð¯ðµ æ¥æ¬èç¹",
        "type": "url-test",
        "url": "http://www.gstatic.com/generate_204",
        "interval": 300,
        "proxies": [],
    },
    {
        "name": "ð°ð· é©å½èç¹",
        "type": "url-test",
        "url": "http://www.gstatic.com/generate_204",
        "interval": 300,
        "proxies": [],
    },
]

DEFAULT_DNS = {
    "enable": True,
    "ipv6": False,
    "listen": "0.0.0.0:53",
    "enhanced-mode": "fake-ip",
    "fake-ip-range": "198.18.0.1/16",
    "fake-ip-filter": ["*.lan", "localhost.ptlogin2.qq.com"],
    "nameserver": [
        "223.5.5.5",
        "180.76.76.76",
        "119.29.29.29",
        "117.50.11.11",
        "117.50.10.10",
        "114.114.114.114",
        "https://dns.alidns.com/dns-query",
        "https://doh.360.cn/dns-query",
    ],
    "fallback": [
        "8.8.8.8",
        "1.1.1.1",
        "tls://dns.rubyfish.cn:853",
        "tls://1.0.0.1:853",
        "tls://dns.google:853",
        "https://dns.rubyfish.cn/dns-query",
        "https://cloudflare-dns.com/dns-query",
        "https://dns.google/dns-query",
    ],
    "fallback-filter": {"geoip": True, "ipcidr": ["240.0.0.0/4"]},
}


class Experimental(BaseModel):
    ignore_resolve_fail: bool = Field(True, description="å¿½ç¥ DNS è§£æå¤±è´¥ï¼é»è®¤å¼ä¸º true", alias="ignore-resolve-fail")


class ClashConfig(BaseModel):
    mixed_port: int = Field(7890, alias="mixed-port")
    socks_port: int = Field(7891, alias="socks-port")
    allow_lan: bool = Field(True, alias="allow-lan")
    bind_address: str = Field("*", alias="bind-address")
    ipv6: bool = False
    mode: str = "rule"
    log_level: str = Field("info", alias="log-level")
    external_controller: str = Field("127.0.0.1:9090", description="Clash ç RESTful API", alias="external-controller")
    experimental: Experimental = Field(Experimental(), description="å®éªæ§åè½")
    dns: dict = DEFAULT_DNS
    proxies: list = []
    proxy_groups: list = Field(alias="proxy-groups")
    rules: List[str]


@retry(retries=5)
async def get_config() -> Response:
    rsp = await get(
        setting.subconverter.host,
        params={
            "target": "clash",
            "url": setting.subconverter.url,
            "insert": "false",
            "config": setting.subconverter.config,
            "emoji": "true",
            "list": "false",
            "tfo": "false",
            "scv": "false",
            "fdn": "false",
            "sort": "false",
            "new_name": "true",
        },
        verify_ssl=False,
    )
    assert rsp.ok, f"è·åéç½®å¤±è´¥, {rsp.status_code}"
    return rsp


async def save_config(config: ClashConfig):
    path = get_real_path("../config/clash.yaml")
    async with async_open(path, "w") as file:
        await file.write(yaml.safe_dump(config.dict(by_alias=True), allow_unicode=True, width=800, sort_keys=False))


@monitor
async def refresh_clash_config():
    logger.info("start refreshing the config of clash")
    result = await get_config()
    config = yaml.safe_load(result.text)
    rules: List[str] = config["rules"]

    for rule in rules:
        try:
            proxy_group = rule.split(",")[2]
        except IndexError as err:
            if "MATCH" not in rule:
                raise ValueError(f"rule {rule} is invalid") from err
        else:
            assert proxy_group in PROXY_GROUP_SET, f"clash éç½®åç°éè¯¯: {rule}"

    await save_config(ClashConfig(**{"proxy-groups": PROXY_GROUPS, "rules": rules}))
    logger.info("refresh clash config successful")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(register_requests())
    loop.run_until_complete(refresh_clash_config())
    loop.run_until_complete(close_requests())
