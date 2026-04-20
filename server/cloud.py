"""Cloud API read-only tools — Hetzner firewalls, Cloudflare DNS."""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request

from state import log_call
from transport import mcp


def _hetzner_get(path: str) -> dict:
    token = os.environ.get("HETZNER_API_TOKEN", "")
    if not token:
        return {"error": "HETZNER_API_TOKEN not set"}
    url = f"https://api.hetzner.cloud/v1{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def _cf_get(path: str) -> dict:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if not token:
        return {"error": "CLOUDFLARE_API_TOKEN not set"}
    url = f"https://api.cloudflare.com/client/v4{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def hetzner_firewall(server: str = "onyx") -> dict:
    """Current Hetzner firewall rules for a server. Read-only.

    Args:
        server: 'onyx' (firewall 10699284) or 'main' (firewall 10646031)
    """
    t0 = time.monotonic()
    fw_ids = {"onyx": 10699284, "main": 10646031}
    if server not in fw_ids:
        return {"ok": False, "error": f"Unknown server '{server}'. Use: {list(fw_ids)}"}
    data = _hetzner_get(f"/firewalls/{fw_ids[server]}")
    if "error" in data:
        return {"ok": False, "error": data["error"]}
    fw = data.get("firewall", {})
    rules = [
        {
            "protocol": r.get("protocol"),
            "port": r.get("port", "any"),
            "sources": r.get("source_ips", []),
            "description": r.get("description", ""),
        }
        for r in fw.get("rules", [])
        if r.get("direction") == "in"
    ]
    result = {"ok": True, "server": server, "firewall_id": fw_ids[server],
              "name": fw.get("name", ""), "inbound_rules": rules, "rule_count": len(rules)}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("hetzner_firewall", {"server": server}, result, ms)
    logging.info("hetzner_firewall %s (%dms)", server, ms)
    return result


@mcp.tool()
def cloudflare_dns(zone: str) -> dict:
    """Current DNS records for a Cloudflare zone. Read-only.

    Args:
        zone: Zone name — edumusik.net, edumusik.com, kita-seminar-manufaktur.de,
              schafliebe.com, evabiallas.com, frid.nu
    """
    t0 = time.monotonic()
    zone_ids = {
        "edumusik.net":               "732a4a0da095167c94fce39b1ea25557",
        "edumusik.com":               "7fa16cc45b82d9593f2faa5f7794933c",
        "kita-seminar-manufaktur.de": "f02fdbb066c0e9ce4221e4ed2488c086",
        "schafliebe.com":             "cb0f8fd6620b2b07e6fd6a80e606f415",
        "evabiallas.com":             "9dc2d9bcbff3ac4aabaeceab3f8bd159",
        "frid.nu":                    "ba84c568d870f43c3ce52a1ab282766b",
    }
    if zone not in zone_ids:
        return {"ok": False, "error": f"Unknown zone '{zone}'. Known: {', '.join(zone_ids)}"}
    data = _cf_get(f"/zones/{zone_ids[zone]}/dns_records?per_page=100")
    if "error" in data:
        return {"ok": False, "error": data["error"]}
    if not data.get("success"):
        return {"ok": False, "error": str(data.get("errors", "unknown"))}
    records = [
        {"type": r["type"], "name": r["name"], "content": r["content"][:80],
         "proxied": r.get("proxied", False), "ttl": r.get("ttl")}
        for r in data.get("result", [])
        if r["type"] in ("A", "AAAA", "CNAME", "MX", "TXT", "NS")
    ]
    result = {"ok": True, "zone": zone, "record_count": len(records), "records": records}
    ms = round((time.monotonic() - t0) * 1000)
    log_call("cloudflare_dns", {"zone": zone}, result, ms)
    logging.info("cloudflare_dns %s (%d records, %dms)", zone, len(records), ms)
    return result
