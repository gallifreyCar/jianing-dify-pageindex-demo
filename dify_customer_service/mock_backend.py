#!/usr/bin/env python3
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote


STORE_NAME = "嘉宁测试电商"
DOC_ROOT = "/srv/mock_docs"

DOCS = {
    "refund": [
        {
            "title": "七天无理由退货",
            "pageIndex": "after-sales/refund/001",
            "summary": "签收后7天内可申请退货，商品需保持完好，不影响二次销售。",
        },
        {
            "title": "退款时效说明",
            "pageIndex": "after-sales/refund/002",
            "summary": "退货仓确认收货后1到3个工作日原路退款，银行卡到账可能延迟1到5个工作日。",
        },
    ],
    "logistics": [
        {
            "title": "发货与物流时效",
            "pageIndex": "delivery/logistics/101",
            "summary": "现货订单通常24小时内发出，大促期间可能延长至72小时。",
        },
        {
            "title": "签收异常处理",
            "pageIndex": "delivery/logistics/102",
            "summary": "如出现破损、少件、拒收等情况，请在24小时内联系客服并提供照片。",
        },
    ],
    "warranty": [
        {
            "title": "质保政策",
            "pageIndex": "service/warranty/201",
            "summary": "嘉宁测试电商自营商品多数支持12个月质保，配件类商品以页面说明为准。",
        },
        {
            "title": "换新申请条件",
            "pageIndex": "service/warranty/202",
            "summary": "质量问题经售后判定成立，可优先换新；缺货时改为退款或维修。",
        },
    ],
    "usage": [
        {
            "title": "安装使用指南",
            "pageIndex": "help/usage/301",
            "summary": "首次使用请按说明书完成安装与激活，通电前确认配件连接牢固。",
        },
        {
            "title": "常见故障排查",
            "pageIndex": "help/usage/302",
            "summary": "无法启动、异常噪音、配网失败等问题可先执行重启、复位和网络检查。",
        },
    ],
    "other": [
        {
            "title": "联系客服与工单",
            "pageIndex": "service/other/401",
            "summary": "复杂问题可转人工客服，服务时间为每日9:00到21:00。",
        },
        {
            "title": "售后资料补充说明",
            "pageIndex": "service/other/402",
            "summary": "提交售后申请时可补充订单号、联系方式、问题照片与视频，以提升处理效率。",
        },
    ],
}

ORDERS = {
    "JN202603150001": {
        "status": "已发货",
        "tracking_no": "SF1234567890",
        "carrier": "顺丰速运",
        "items": ["嘉宁智能空气炸锅 5L"],
        "payment_amount": 399.0,
        "refund_status": "无退款",
        "latest_progress": "包裹已到达杭州转运中心，预计明日送达。",
    },
    "JN202603150002": {
        "status": "退款中",
        "tracking_no": "",
        "carrier": "",
        "items": ["嘉宁筋膜枪 Pro"],
        "payment_amount": 269.0,
        "refund_status": "商家审核通过，等待原路退款",
        "latest_progress": "退款申请已通过，预计1到3个工作日到账。",
    },
    "JN202603150003": {
        "status": "待签收",
        "tracking_no": "YT9988776655",
        "carrier": "圆通速递",
        "items": ["嘉宁便携榨汁杯"],
        "payment_amount": 129.0,
        "refund_status": "无退款",
        "latest_progress": "快件派送中，请保持电话畅通。",
    },
}


def json_bytes(payload):
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "JiaNingMock/1.0"

    def _send(self, status, payload):
        body = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, status, text, content_type="text/plain; charset=utf-8"):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send(200, {"ok": True, "store": STORE_NAME})
            return
        if parsed.path == "/docs":
            files = sorted(
                f for f in os.listdir(DOC_ROOT) if os.path.isfile(os.path.join(DOC_ROOT, f))
            )
            self._send(200, {"store": STORE_NAME, "files": files})
            return
        if parsed.path.startswith("/docs/"):
            filename = unquote(os.path.basename(parsed.path))
            target = os.path.join(DOC_ROOT, filename)
            if not os.path.isfile(target):
                self._send(404, {"error": "doc_not_found", "filename": filename})
                return
            with open(target, "r", encoding="utf-8") as f:
                self._send_text(200, f.read(), "text/markdown; charset=utf-8")
            return
        self._send(404, {"error": "not_found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/pageindex/search":
            payload = self._read_json()
            scene = payload.get("scene", "other")
            query = payload.get("q", "")
            docs = DOCS.get(scene, DOCS["other"])
            answer = {
                "store": STORE_NAME,
                "scene": scene,
                "query": query,
                "hits": docs,
                "reply": f"{STORE_NAME} 已根据 {scene} 场景检索到 {len(docs)} 条测试文档，可用于售后答复。",
            }
            self._send(200, answer)
            return

        if parsed.path == "/orders/query":
            payload = self._read_json()
            order_no = payload.get("order_no", "").strip()
            phone_tail = payload.get("phone_tail", "").strip()
            order = ORDERS.get(order_no)
            if not order:
                self._send(
                    404,
                    {
                        "store": STORE_NAME,
                        "found": False,
                        "message": "未查询到该测试订单，请使用 JN202603150001 到 JN202603150003 之一。",
                    },
                )
                return

            self._send(
                200,
                {
                    "store": STORE_NAME,
                    "found": True,
                    "order_no": order_no,
                    "phone_tail": phone_tail or "6688",
                    **order,
                },
            )
            return

        self._send(404, {"error": "not_found"})


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8787), Handler)
    print("mock backend listening on http://0.0.0.0:8787", flush=True)
    server.serve_forever()
