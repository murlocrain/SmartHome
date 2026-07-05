import json
import requests
from sqlalchemy.orm import Session

from common.config import settings, logger
from common.database import SessionLocal
from common.iot_client import iot_client
from common.models import EnvMonitorData, AIPrediction


# ==================== 系统提示词：定义智能体角色 ====================
SMART_HOME_SYSTEM_PROMPT = """你是一个智能家居 AI 助手，负责帮用户管理家里的智能设备和分析居家状态。

## 你可以做的
1. 控制灯光（light/灯）——打开/关闭
2. 控制电风扇（motor/风扇/电扇）——打开/关闭
3. 控制蜂鸣器（beep/蜂鸣器/闹钟）——响一下
4. 回答关于当前环境（温度、湿度、光照、人体红外等）的问题
5. 解读 AI 预测结果（活动强度、场景识别、灯光预判、夜间异常检测），给出人性化建议
6. 根据环境数据和 AI 预测综合给出合理建议

## 系统配置的 AI 模型
- **活动强度预测**：随机森林回归模型。MAE=1.38，R²=0.85。基于加速度计/陀螺仪变化估算活动剧烈程度（0-100+）。数值越高代表当前活动越剧烈。
- **场景识别**：随机森林多分类模型。准确率 83%。识别四种场景：睡眠、离家、室内活动、其他。其中离家场景识别最准（F1=0.95）。
- **灯光开关预测**：随机森林二分类模型。准确率 99.7%。预判未来10分钟内灯光是否需要切换。关键因素是距上次灯光变化的时间。
- **夜间异常检测**：Z-score 统计规则。阈值 2.5 倍标准差。监测夜间睡眠时段是否存在异常活动（如频繁起夜、异常高活动量）。

## 回答风格
- 回答要**简洁、口语化**，不要用技术术语
- 在回答预测相关问题时，自然地融入模型置信度信息（如"根据当前数据，AI 判断……"）
- 如果用户的话和设备/AI预测无关，就正常聊天即可
- 当用户询问"现在情况"时，综合传感器数据和 AI 预测给出完整分析"""


# ==================== 大模型调用（OpenAI 兼容协议） ====================
def chat_with_ai(user_message: str, system_prompt: str = None, extra_context: str = None) -> str:
    """调用大模型完成对话。返回纯文本回答。
    兼容 DeepSeek / 通义千问 / 智谱 / OpenAI 等所有 OpenAI 格式的接口。
    """
    if not settings.AI_ENABLED:
        return "（AI 功能未启用，请在 .env 中填入 API Key 后再试）"

    messages = []
    messages.append({"role": "system", "content": system_prompt or SMART_HOME_SYSTEM_PROMPT})

    if extra_context:
        messages.append({
            "role": "user",
            "content": f"【当前环境数据参考】\n{extra_context}\n\n请基于以上数据回答用户问题。"
        })

    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {settings.AI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.AI_MODEL,
        "messages": messages,
        "temperature": settings.AI_TEMPERATURE,
    }

    try:
        r = requests.post(
            f"{settings.AI_BASE_URL.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
            timeout=settings.AI_TIMEOUT,
        )

        if r.status_code != 200:
            logger.error(f"AI API 返回错误 {r.status_code}: {r.text[:300]}")
            return f"（AI 调用失败，状态码 {r.status_code}）"

        data = r.json()
        return data["choices"][0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        logger.error("AI API 调用超时")
        return "（AI 响应超时，请稍后再试）"
    except Exception as e:
        logger.error(f"AI API 异常: {e}")
        return f"（AI 调用异常: {e}）"


# ==================== 智能体：自然语言 → 控制命令 解析 ====================
INTENT_PARSE_PROMPT = """你的任务是把用户的自然语言解析成结构化的设备控制意图。

可用设备列表：
- light（灯光）: 命令 light_control，参数 onoff=ON/OFF
- motor（电风扇）: 命令 motor_control，参数 onoff=ON/OFF
- beep（蜂鸣器）: 命令 beep_play，无参数

请严格按照以下 JSON 格式回答，**不要输出任何额外文本**：
{
    "intent": "control" | "question" | "chat",
    "target": "light" | "motor" | "beep" | null,
    "action": "ON" | "OFF" | null,
    "reply": "给用户的简洁回复（例如'好的，已经为你打开灯光'）"
}

规则：
- 只有明确要求打开/关闭某个设备时，intent=control
- 询问环境数据、问问题时，intent=question
- 普通聊天（如"你好"），intent=chat
- 如果用户说的话模糊不清，target=null，intent=chat
"""


def parse_intent(user_message: str) -> dict:
    """让 AI 解析用户意图：是要控制设备、问问题，还是随便聊天。"""
    raw = chat_with_ai(user_message, system_prompt=INTENT_PARSE_PROMPT)

    # 尝试从 AI 回复中提取 JSON（有时 AI 会加额外文字）
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        json_str = raw[start:end + 1]
        try:
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"解析 AI 返回的 JSON 失败: {e}，原始内容: {raw}")

    return {"intent": "chat", "target": None, "action": None, "reply": raw}


# ==================== 智能体：执行控制 + 环境分析 ====================
COMMAND_MAP = {
    "light": "light_control",
    "motor": "motor_control",
    "beep": "beep_play",
}


def execute_intent(parsed: dict) -> dict:
    """根据 AI 解析出的意图执行操作，并返回完整结果。"""
    result = {
        "intent": parsed.get("intent"),
        "target": parsed.get("target"),
        "action": parsed.get("action"),
        "ai_reply": parsed.get("reply", ""),
        "device_result": None,
    }

    if parsed.get("intent") == "control" and parsed.get("target"):
        target = parsed["target"]
        if target in COMMAND_MAP:
            command = COMMAND_MAP[target]
            paras = {}
            if command != "beep_play":
                paras = {"onoff": parsed.get("action", "ON")}

            device_result = iot_client.send_command(command, paras)
            result["device_result"] = device_result
            if device_result.get("success"):
                result["ai_reply"] = f"好的，已经为你{'打开' if paras.get('onoff') == 'ON' else '关闭'}{'灯光' if target == 'light' else '电风扇' if target == 'motor' else '蜂鸣器'}。"
            else:
                result["ai_reply"] = f"设备控制失败：{device_result.get('error', '未知错误')}"

    return result


# ==================== 上下文构造器 ====================
def build_agent_context(env_data: dict = None, ai_prediction: dict = None) -> str:
    """统一构造 DeepSeek 的实时上下文，三层数据：
    1. 传感器数据
    2. AI 预测结果
    3. （模型知识已放在 system prompt，不在此重复）
    """
    parts = []

    # 第一层：传感器
    if env_data:
        parts.append("【当前环境数据】")
        parts.append(f"- 温度：{env_data.get('temperature', '--')}°C")
        parts.append(f"- 湿度：{env_data.get('humidity', '--')}%")
        parts.append(f"- 光照：{env_data.get('light', '--')} lux")
        parts.append(f"- 人体红外：{env_data.get('body_state', '--')}")
        motor = env_data.get('motorStatus')
        light = env_data.get('lightStatus')
        if motor is not None:
            parts.append(f"- 电风扇：{'开' if motor else '关'}")
        if light is not None:
            parts.append(f"- 灯光：{'开' if light else '关'}")
        parts.append("")

    # 第二层：AI 预测
    if ai_prediction:
        parts.append("【AI 实时预测结果】")
        activity = ai_prediction.get('activity')
        if activity is not None:
            parts.append(f"- 活动强度：{activity}（0-100+，越高越剧烈）")
        scene = ai_prediction.get('scene')
        scene_prob = ai_prediction.get('scene_probability')
        if scene:
            parts.append(f"- 当前场景：{scene}（置信度 {scene_prob}%）")
        light_change = ai_prediction.get('light_will_change')
        light_prob = ai_prediction.get('light_change_probability')
        parts.append(f"- 灯光预判：{'建议切换' if light_change else '保持现状'}（变化概率 {light_prob}%）")
        night_info = ai_prediction.get('night_anomaly', {})
        if night_info.get('is_anomalous'):
            parts.append(f"- 夜间异常：⚠️ 检测到异常（Z-score={night_info.get('zscore', 0)}，阈值={night_info.get('threshold', 0)}）")
        else:
            parts.append(f"- 夜间异常：未检测到异常")
        parts.append("")

    return "\n".join(parts)


def analyze_environment(env_data: dict = None, ai_prediction: dict = None) -> str:
    """把环境数据和 AI 预测喂给 DeepSeek，让它给出人性化分析和建议。"""
    if not env_data:
        return "当前还没有采集到环境数据。"

    context = build_agent_context(env_data, ai_prediction)
    reply = chat_with_ai(
        "请基于以上环境和AI预测数据，用2-3句话给出综合分析和人性化建议。",
        extra_context=context,
    )
    return reply


# ==================== 便捷入口函数 ====================
def smart_agent(user_message: str, env_data: dict = None, ai_prediction: dict = None) -> dict:
    """一站式智能体接口：解析意图 → 执行操作 → 返回对话结果。"""
    parsed = parse_intent(user_message)
    result = execute_intent(parsed)

    # 对 question / chat 类意图，提供完整上下文分析
    context = build_agent_context(env_data, ai_prediction)
    if parsed.get("intent") == "chat" and context:
        analysis_reply = chat_with_ai(
            user_message,
            extra_context=context,
        )
        result["ai_reply"] = analysis_reply

    result["env_suggestion"] = analyze_environment(env_data, ai_prediction) if env_data else None
    return result


# ==================== 上下文构造（供 agent_router 使用） ====================
def _get_latest_prediction(db: Session) -> dict:
    """获取最新 AI 预测结果。"""
    pred = (
        db.query(AIPrediction)
        .order_by(AIPrediction.predict_time.desc())
        .first()
    )
    if not pred:
        return None
    return {
        "activity": pred.activity_index,
        "scene": pred.scene,
        "scene_probability": pred.scene_probability,
        "light_will_change": pred.light_will_change,
        "light_change_probability": pred.light_change_probability,
        "night_anomaly": {
            "is_anomalous": pred.is_night_anomalous,
            "zscore": pred.night_zscore,
            "current_motion_5min": pred.night_current_motion,
            "threshold": None,
        },
    }


def _build_full_context(db: Session = None) -> str:
    """从 DB 构造完整三层上下文字符串（传感器 + AI预测）。
    如果未传入 db，自动创建临时会话。
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        latest = (
            db.query(EnvMonitorData)
            .order_by(EnvMonitorData.timestamp.desc())
            .first()
        )
        env_data = None
        if latest:
            env_data = {
                "temperature": latest.sht30_temp_raw,
                "humidity": latest.sht30_humi_raw,
                "light": latest.bh1750_raw,
                "body_state": "有人" if latest.pir_gpio == 1 else "无人",
                "timestamp": str(latest.timestamp),
                "lightStatus": (latest.lightStatus or "").upper() == "ON",
                "motorStatus": (latest.motorStatus or "").upper() == "ON",
            }
        return build_agent_context(env_data, _get_latest_prediction(db))
    finally:
        if close_db:
            db.close()
