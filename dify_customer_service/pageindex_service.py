#!/usr/bin/env python3
import asyncio
import json
import os
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pageindex.page_index_md import md_to_tree
from pageindex.utils import ChatGPT_API, extract_json, get_nodes


STORE_NAME = "嘉宁测试电商"
MODEL_NAME = os.getenv("PAGEINDEX_MODEL", "deepseek-chat")
DOC_ROOT = os.getenv("PAGEINDEX_DOC_ROOT", "/srv/mock_docs")

SCENE_TO_FILE = {
    "refund": "01_退货与退款政策.md",
    "logistics": "02_物流与签收处理.md",
    "warranty": "03_质保与换新规则.md",
    "usage": "04_安装使用与故障排查.md",
    "other": "05_客服回复模版.md",
}

SCENE_HINTS = {
    "refund": "优先关注退货资格、退款时效、商品完好条件。",
    "logistics": "优先关注发货时效、物流停滞、破损签收、少件错发。",
    "warranty": "优先关注质保期限、质量问题、换新和维修条件。",
    "usage": "优先关注安装步骤、首次使用和常见故障排查。",
    "other": "优先关注客服模版、转人工和资料补充。",
}

TREES = {}


def get_tree_root(tree):
    if isinstance(tree, dict) and isinstance(tree.get("structure"), list) and tree["structure"]:
        return tree["structure"][0]
    return tree


def compact_tree(node):
    node = get_tree_root(node)
    compact = {
        "title": node.get("title"),
        "node_id": node.get("node_id"),
    }
    if node.get("summary"):
        compact["summary"] = node["summary"]
    if node.get("prefix_summary"):
        compact["prefix_summary"] = node["prefix_summary"]
    if node.get("nodes"):
        compact["nodes"] = [compact_tree(child) for child in node["nodes"]]
    return compact


def find_nodes_by_ids(tree, node_ids):
    selected = []
    for node in get_nodes(get_tree_root(tree)):
        if node.get("node_id") in node_ids:
            selected.append(node)
    return selected


def build_scene_tree(scene):
    filename = SCENE_TO_FILE[scene]
    md_path = os.path.join(DOC_ROOT, filename)
    tree = asyncio.run(
        md_to_tree(
            md_path=md_path,
            if_thinning=False,
            if_add_node_summary="yes",
            summary_token_threshold=120,
            model=MODEL_NAME,
            if_add_doc_description="no",
            if_add_node_text="yes",
            if_add_node_id="yes",
        )
    )
    return tree


def ensure_tree(scene):
    if scene not in TREES:
        TREES[scene] = build_scene_tree(scene)


def retrieve_nodes(query, scene):
    ensure_tree(scene)
    tree = TREES[scene]
    root = get_tree_root(tree)
    prompt = f"""
You are given a user query and a PageIndex tree structure of a document.
You need to find all nodes that are likely to contain the answer.

Store: {STORE_NAME}
Scene: {scene}
Expert hint: {SCENE_HINTS.get(scene, '')}
Query: {query}

Document tree structure:
{json.dumps(compact_tree(root), ensure_ascii=False)}

Reply in the following JSON format:
{{
  "thinking": "<reasoning about which nodes are relevant>",
  "node_list": ["0001", "0002"]
}}
Only return JSON.
"""
    response = ChatGPT_API(model=MODEL_NAME, prompt=prompt)
    payload = extract_json(response)
    node_ids = payload.get("node_list") or []
    if not isinstance(node_ids, list):
        node_ids = []
    hits = find_nodes_by_ids(tree, node_ids)
    return payload.get("thinking", ""), hits


def answer_query(query, scene, hits):
    contexts = []
    for hit in hits:
        contexts.append(
            {
                "node_id": hit.get("node_id"),
                "title": hit.get("title"),
                "text": hit.get("text", ""),
            }
        )
    prompt = f"""
你是{STORE_NAME}的售后客服助手。请基于给定文档内容回答用户问题，语气自然、明确、像电商客服。
如果文档里没有足够信息，就明确说“当前文档没有完整说明”，并建议转人工。

场景：{scene}
用户问题：{query}
可用文档片段：
{json.dumps(contexts, ensure_ascii=False)}

请输出 JSON：
{{
  "answer": "<给用户的最终答复>",
  "citations": [{{"node_id": "0001", "title": "..."}}]
}}
只返回 JSON。
"""
    response = ChatGPT_API(model=MODEL_NAME, prompt=prompt)
    payload = extract_json(response)
    return payload


def json_bytes(payload):
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "PageIndexOfficialService/1.0"

    def log_message(self, fmt, *args):
        return

    def _send(self, status, payload):
        body = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def do_GET(self):
        if self.path == "/health":
            self._send(
                200,
                {
                    "ok": True,
                    "store": STORE_NAME,
                    "model": MODEL_NAME,
                    "scenes": sorted(SCENE_TO_FILE.keys()),
                },
            )
            return
        self._send(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/search":
            self._send(404, {"error": "not_found"})
            return

        payload = self._read_json()
        query = (payload.get("q") or "").strip()
        scene = payload.get("scene") or "other"
        if scene not in SCENE_TO_FILE:
            scene = "other"
        if not query:
            self._send(400, {"error": "missing_query"})
            return

        thinking, hits = retrieve_nodes(query, scene)
        answer = answer_query(query, scene, hits)
        response = {
            "store": STORE_NAME,
            "scene": scene,
            "query": query,
            "thinking": thinking,
            "hits": [
                {
                    "node_id": hit.get("node_id"),
                    "title": hit.get("title"),
                    "text": hit.get("text", "")[:1200],
                }
                for hit in hits
            ],
            "answer": answer.get("answer", "当前未检索到足够内容，建议补充问题或转人工处理。"),
            "citations": answer.get("citations", []),
        }
        self._send(200, response)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8790), Handler)
    print(f"pageindex official service listening on http://0.0.0.0:8790 with model {MODEL_NAME}", flush=True)
    server.serve_forever()
