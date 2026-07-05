#!/bin/bash
# 鏅鸿兘瀹跺眳鏁版嵁鏈嶅姟鍚姩鑴氭湰

echo "=========================================="
echo "  鏅鸿兘瀹跺眳鏁版嵁鏈嶅姟鍚姩鑴氭湰"
echo "=========================================="

# 鑾峰彇绔彛鍙傛暟锛堥粯璁?000锛?
PORT=${1:-8000}

# 妫€鏌ヨ櫄鎷熺幆澧?
if [ ! -d "venv" ]; then
    echo "鍒涘缓铏氭嫙鐜..."
    python3.11 -m venv venv
fi

# 婵€娲昏櫄鎷熺幆澧?
echo "婵€娲昏櫄鎷熺幆澧?.."
source venv/bin/activate

# 瀹夎渚濊禆
echo "瀹夎渚濊禆..."
pip install -r simple_requirements.txt

# 鍚姩鏈嶅姟
echo "鍚姩鏈嶅姟..."
echo "=========================================="
echo "鏈嶅姟鍦板潃: http://localhost:${PORT}"
echo "鍗庝负浜戝洖璋? http://localhost:${PORT}/api/v1/devices/huawei-callback"
echo "API鏂囨。: http://localhost:${PORT}/docs"
echo "鎸?Ctrl+C 鍋滄鏈嶅姟"
echo "=========================================="

# 璁剧疆绔彛鐜鍙橀噺
export APP_PORT=$PORT

python app.py
