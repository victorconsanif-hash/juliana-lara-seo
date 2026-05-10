#!/usr/bin/env python3
"""
Cria o workflow n8n 'seo-juliana-agendor' clonando o workflow da LP.

Diferenças vs LP:
- Webhook path: 'seo-juliana-agendor' (era 'lp-juliana-agendor')
- Mapeamento de 2 novos custom fields no body do "Criar Deal":
  - motivo (vem do select do FormContato)
  - conversion_url (URL da página onde o lead converteu)

Uso: python3 setup_n8n_workflow.py [--dry-run]
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

LP_ENV = Path(__file__).resolve().parent.parent.parent / "juliana-lara-lps" / ".env"
SOURCE_WORKFLOW_ID = "arEkd9uafweHY28q"
NEW_NAME = "SEO Juliana → Agendor"
NEW_WEBHOOK_PATH = "seo-juliana-agendor"


def load_env():
    env = {}
    for line in LP_ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    return env


def n8n_request(env, method, path, body=None):
    url = f"{env['N8N_BASE_URL']}/api/v1{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "X-N8N-API-KEY": env["N8N_API_KEY"],
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw)
        except Exception:
            payload = raw.decode(errors="replace")
        return e.code, payload


def patch_nodes(nodes):
    """Mutate node list in place: change webhook path + add motivo/conversion_url to deal body."""
    for node in nodes:
        ntype = node.get("type", "")
        name = node.get("name", "")
        params = node.get("parameters", {})

        # 1. Webhook node — trocar path
        if ntype == "n8n-nodes-base.webhook":
            params["path"] = NEW_WEBHOOK_PATH

        # 2. Node "Criar Deal" — adicionar motivo + conversion_url em customFields
        if "deal" in name.lower() and "httprequest" in ntype.lower():
            body = params.get("body", "")
            extra = (
                ',\n    "motivo": "{{ $(\'Webhook\').item.json.body.motivo }}"'
                ',\n    "conversion_url": "{{ $(\'Webhook\').item.json.body.conversion_url }}"'
            )
            target = '"page_url": "{{ $(\'Webhook\').item.json.body.page_url }}"'
            if target in body and '"motivo"' not in body:
                params["body"] = body.replace(target, target + extra)
                print("  ✓ injetado motivo + conversion_url no body do 'Criar Deal'")
            elif '"motivo"' in body:
                print("  (motivo já presente — não duplicando)")
            else:
                print("  WARN: âncora 'page_url' não encontrada no body — verificar manualmente")

    # Limpar IDs internos pra criar como novo workflow
    for node in nodes:
        node.pop("id", None)
        node.pop("webhookId", None)


def main():
    dry = "--dry-run" in sys.argv
    env = load_env()

    print(f"→ buscando workflow origem {SOURCE_WORKFLOW_ID}...")
    code, src = n8n_request(env, "GET", f"/workflows/{SOURCE_WORKFLOW_ID}")
    if code != 200:
        print(f"FAIL: GET workflow → {code}: {src}")
        sys.exit(1)
    print(f"  ok: '{src.get('name')}' ({len(src.get('nodes', []))} nodes)")

    nodes = json.loads(json.dumps(src["nodes"]))  # deep copy
    connections = json.loads(json.dumps(src.get("connections", {})))
    settings = src.get("settings", {})

    patch_nodes(nodes)

    # Mostrar nodes pra inspeção
    print("\n→ nodes (após patch):")
    for n in nodes:
        print(f"   - {n['name']} | {n['type']}")
        if n.get("type") == "n8n-nodes-base.webhook":
            print(f"       webhook path: {n['parameters'].get('path')}")

    # Localizar o body do node "Criar Deal" pra mostrar e o user decidir como adicionar
    deal_node = next(
        (n for n in nodes if "deal" in n["name"].lower() and "http" in n["type"].lower()),
        None,
    )
    if deal_node:
        print("\n→ body do node 'Criar Deal' (inspeção — vou adicionar motivo e conversion_url depois):")
        body = deal_node["parameters"].get("jsonBody") or deal_node["parameters"].get("body") or deal_node["parameters"].get("bodyParametersJson")
        print(json.dumps(deal_node["parameters"], indent=2, ensure_ascii=False)[:2000])

    new_workflow = {
        "name": NEW_NAME,
        "nodes": nodes,
        "connections": connections,
        "settings": settings,
    }

    if dry:
        print("\n[dry-run] não criando. Adicione --no-dry pra criar.")
        Path("/tmp/seo_workflow_payload.json").write_text(json.dumps(new_workflow, indent=2, ensure_ascii=False))
        print("payload salvo em /tmp/seo_workflow_payload.json")
        return

    print(f"\n→ criando novo workflow '{NEW_NAME}'...")
    code, created = n8n_request(env, "POST", "/workflows", new_workflow)
    if code not in (200, 201):
        print(f"FAIL: POST workflow → {code}: {json.dumps(created, ensure_ascii=False)[:1000]}")
        sys.exit(1)
    new_id = created.get("id")
    print(f"  criado: id={new_id}")

    print(f"→ ativando workflow {new_id}...")
    code, act = n8n_request(env, "POST", f"/workflows/{new_id}/activate")
    if code not in (200, 201):
        print(f"WARN: ativação retornou {code}: {act}")
    else:
        print("  ativo")

    print(f"\n✓ Webhook produção: {env['N8N_BASE_URL']}/webhook/{NEW_WEBHOOK_PATH}")


if __name__ == "__main__":
    main()
