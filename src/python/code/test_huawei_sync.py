"""
测试华为云IoTDA数据查询并同步到本地数据库
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import settings

print("=" * 60)
print("  华为云IoTDA 数据验证 & 同步")
print("=" * 60)

# 检查配置
print(f"\n[1] 配置检查")
print(f"  Device ID: {settings.HUAWEI_IOTDA_DEVICE_ID}")
print(f"  AK: {settings.HUAWEI_IOTDA_AK[:10]}..." if settings.HUAWEI_IOTDA_AK else "  AK: 未配置")
print(f"  SK: {settings.HUAWEI_IOTDA_SK[:10]}..." if settings.HUAWEI_IOTDA_SK else "  SK: 未配置")
print(f"  Project ID: {settings.HUAWEI_IOTDA_PROJECT_ID}")

if not all([settings.HUAWEI_IOTDA_AK, settings.HUAWEI_IOTDA_SK]):
    print("\n[错误] 缺少AK/SK配置，无法继续")
    sys.exit(1)

# 创建客户端
print(f"\n[2] 创建IoTDA客户端...")
try:
    from huaweicloudsdkcore.auth.credentials import BasicCredentials
    from huaweicloudsdkcore.http.http_config import HttpConfig
    from huaweicloudsdkiotda.v5.iotda_client import IoTDAClient

    credentials = BasicCredentials(
        ak=settings.HUAWEI_IOTDA_AK,
        sk=settings.HUAWEI_IOTDA_SK,
        project_id=settings.HUAWEI_IOTDA_PROJECT_ID
    )
    config = HttpConfig(ignore_ssl_verification=True)
    client = IoTDAClient.new_builder() \
        .with_credentials(credentials) \
        .with_endpoint("iotda.cn-north-4.myhuaweicloud.com") \
        .with_http_config(config) \
        .build()
    print("  客户端创建成功")
except Exception as e:
    print(f"  [错误] 创建客户端失败: {e}")
    sys.exit(1)

# 查询设备状态
print(f"\n[3] 查询设备状态...")
try:
    from huaweicloudsdkiotda.v5.model.show_device_request import ShowDeviceRequest
    request = ShowDeviceRequest(device_id=settings.HUAWEI_IOTDA_DEVICE_ID)
    response = client.show_device(request)
    if response:
        device_info = response.to_dict()
        print(f"  设备名称: {getattr(device_info, 'device_name', 'N/A')}")
        print(json.dumps(device_info, indent=4, ensure_ascii=False))
    else:
        print("  无响应数据")
except Exception as e:
    err_str = str(e)
    if "403" in err_str or "IOTDA.000021" in err_str:
        print("  [403权限错误] AK/SK用户无IoTDA访问权限")
        print("  请到华为云控制台 > IAM > 用户 > 权限 > 添加 IoTDA FullAccess")
    else:
        print(f"  [错误] {type(e).__name__}: {e}")

# 查询设备影子（最新数据）
print(f"\n[4] 查询设备影子（最新上报数据）...")
shadow_data = None
try:
    from huaweicloudsdkiotda.v5.model.show_device_shadow_request import ShowDeviceShadowRequest
    request = ShowDeviceShadowRequest(device_id=settings.HUAWEI_IOTDA_DEVICE_ID)
    response = client.show_device_shadow(request)
    if response:
        result = response.to_dict()
        shadow = getattr(result, 'shadow', None) or []
        print(f"  服务数量: {len(shadow)}")

        all_props = {}
        for svc in shadow:
            svc_id = getattr(svc, 'serviceId', 'unknown')
            reported = getattr(svc, 'reported', None) or {}
            props = getattr(reported, 'properties', None) or {}
            all_props.update(props)
            print(f"\n  服务 [{svc_id}]:")
            for key, value in props.items():
                print(f"    {key}: {value} ({type(value).__name__})")

        shadow_data = all_props
    else:
        print("  无响应数据")
except Exception as e:
    err_str = str(e)
    if "403" in err_str or "IOTDA.000021" in err_str:
        print("  [403权限错误] AK/SK用户无IoTDA访问权限")
        print("  请到华为云控制台 > IAM > 用户 > 权限 > 添加 IoTDA FullAccess")
    else:
        print(f"  [错误] {type(e).__name__}: {e}")

# 同步到本地数据库
if shadow_data:
    print(f"\n[5] 同步数据到本地数据库...")
    try:
        import asyncio
        from common.database import async_session_factory
        from services.device_service.service import DeviceService

        async def do_sync():
            async with async_session_factory() as db:
                result = await DeviceService.sync_huawei_history(db, family_id=1, days=7)
                return result

        result = asyncio.run(do_sync())
        print(f"  同步结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"  [错误] 同步失败: {e}")
else:
    print(f"\n[5] 跳过同步（无可同步的设备影子数据）")

print(f"\n{'=' * 60}")
