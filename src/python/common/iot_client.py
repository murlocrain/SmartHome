import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.signer.signer import DerivationAKSKSigner

from common.config import settings, logger


class _SignedRequest:
    def __init__(self, method, host, path, headers, body):
        self.method = method
        self.host = host
        self.resource_path = path
        self.header_params = headers or {}
        self.query_params = {}
        self.body = body


def _build_credentials():
    return BasicCredentials(
        ak=settings.HUAWEI_IOTDA_AK,
        sk=settings.HUAWEI_IOTDA_SK,
        project_id=settings.HUAWEI_IOTDA_PROJECT_ID,
    )


def _build_headers(with_body: bool = True) -> dict:
    headers = {}
    if with_body:
        headers["Content-Type"] = "application/json"
    if settings.HUAWEI_IOTDA_INSTANCE_ID:
        headers["Instance-Id"] = settings.HUAWEI_IOTDA_INSTANCE_ID
    return headers


def _sign_and_send(method: str, path: str, body: str = None) -> dict:
    credentials = _build_credentials()
    headers = _build_headers(with_body=(body is not None))

    req = _SignedRequest(
        method=method,
        host=settings.HUAWEI_IOTDA_APP_ENDPOINT,
        path=path,
        headers=headers,
        body=body,
    )

    signed = DerivationAKSKSigner(credentials).sign(req, "iotdm", "cn-north-4")
    url = f"https://{signed.host}{signed.resource_path}"

    try:
        if method == "POST":
            r = requests.post(url, headers=signed.header_params, data=signed.body, timeout=10, verify=False)
        else:
            r = requests.get(url, headers=signed.header_params, timeout=15, verify=False)

        logger.info(f"HTTP响应状态码: {r.status_code}，响应体长度: {len(r.content)}")
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text}

        if r.status_code == 200:
            body_error_code = data.get("error_code") if isinstance(data, dict) else None
            if body_error_code == "IOTDA.014111":
                logger.info(
                    f"命令已成功下发到华为云 IoTDA（设备未在指定时间内返回响应，"
                    f"不影响设备实际执行；在板子上加上响应就能消除这个状态码）"
                )
                return {
                    "success": True,
                    "delivered": True,
                    "device_timeout": True,
                    "data": data,
                    "raw_response": r.text,
                    "status_code": r.status_code,
                }
            return {"success": True, "delivered": True, "data": data, "raw_response": r.text, "status_code": r.status_code}

        error_code = data.get("error_code") or ""
        error_msg = data.get("error_msg") or str(data)
        logger.error(f"华为云 API 错误 [{r.status_code}] {error_code}: {error_msg}")

        if error_code == "IOTDA.001006":
            logger.warning("=" * 60)
            logger.warning("==> IOTDA.001006: 标准版实例-授权用户未找到应用")
            logger.warning("    请在IoTDA控制台→应用管理创建应用并授权")
            logger.warning("=" * 60)

        return {
            "error": f"{error_code}: {error_msg}",
            "status_code": r.status_code,
            "error_code": error_code,
            "error_msg": error_msg,
        }
    except Exception as e:
        logger.error(f"HTTP请求异常: {e}")
        return {"error": str(e)}


class RESTClient:
    def __init__(self):
        logger.info(
            f"华为云REST客户端初始化成功，AK: {settings.HUAWEI_IOTDA_AK[:8]}****{settings.HUAWEI_IOTDA_AK[-4:]}，"
            f"Region: cn-north-4，ProjectID: {settings.HUAWEI_IOTDA_PROJECT_ID}，"
            f"InstanceID: {settings.HUAWEI_IOTDA_INSTANCE_ID}，"
            f"设备: {settings.HUAWEI_IOTDA_DEVICE_ID}"
        )

    def send_command(self, command_name: str, paras: dict = None) -> dict:
        body_dict = {
            "service_id": "rk2206远程控制",
            "command_name": command_name,
            "paras": paras or {},
        }
        body_str = json.dumps(body_dict, ensure_ascii=False)

        resource_path = (
            f"/v5/iot/{settings.HUAWEI_IOTDA_PROJECT_ID}/devices/"
            f"{settings.HUAWEI_IOTDA_DEVICE_ID}/commands"
        )

        logger.info(
            f"下发命令 {command_name}，参数={json.dumps(paras or {}, ensure_ascii=False)}，"
            f"设备={settings.HUAWEI_IOTDA_DEVICE_ID}"
        )

        result = _sign_and_send("POST", resource_path, body_str)

        if result.get("success"):
            logger.info(f"命令 {command_name} 下发成功: {json.dumps(result.get('data'), ensure_ascii=False)}")
        return result

    def list_devices(self, limit: int = 10) -> dict:
        resource_path = f"/v5/iot/{settings.HUAWEI_IOTDA_PROJECT_ID}/devices?limit={limit}"
        return _sign_and_send("GET", resource_path)

    def query_device(self, device_id: str) -> dict:
        resource_path = f"/v5/iot/{settings.HUAWEI_IOTDA_PROJECT_ID}/devices/{device_id}"
        return _sign_and_send("GET", resource_path)

    def get_device_shadow(self, device_id: str) -> dict:
        resource_path = f"/v5/iot/{settings.HUAWEI_IOTDA_PROJECT_ID}/devices/{device_id}/shadow"
        return _sign_and_send("GET", resource_path)

    def pull_device_data(self, device_id: str) -> dict:
        resource_path = f"/v5/iot/{settings.HUAWEI_IOTDA_PROJECT_ID}/devices/{device_id}/historydata?limit=10"
        return _sign_and_send("GET", resource_path)


class HuaweiIoTDAClient:
    def __init__(self):
        self.rest_client = None

    @property
    def client(self):
        if self.rest_client is None:
            self.rest_client = RESTClient()
            logger.info("=== HuaweiIoTDAClient.client 创建完成 ===")
        return self.rest_client

    def send_command(self, command_name: str, paras: dict = None) -> dict:
        return self.client.send_command(command_name, paras)

    def list_devices(self, limit: int = 10) -> dict:
        return self.client.list_devices(limit)

    def query_device(self, device_id: str) -> dict:
        return self.client.query_device(device_id)

    def get_device_shadow(self, device_id: str) -> dict:
        return self.client.get_device_shadow(device_id)

    def pull_device_data(self, device_id: str) -> dict:
        return self.client.pull_device_data(device_id)


iot_client = HuaweiIoTDAClient()
