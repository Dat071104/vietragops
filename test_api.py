import requests
import json
import sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

url_ask = 'http://127.0.0.1:8000/ask'
url_agent = 'http://127.0.0.1:8000/agent/ask'

payload = {
    'question': 'Ngành Khoa học máy tính cần bao nhiêu tín chỉ để tốt nghiệp?',
    'top_k': 5,
    'use_reranker': True,
    'use_guardrail': True,
    'return_debug': True
}

print('=== TEST /ask ===')
try:
    res = requests.post(url_ask, json=payload)
    print("Status:", res.status_code)
    print(json.dumps(res.json(), ensure_ascii=False, indent=2)[:500])
except Exception as e:
    print(e)

print('\n=== TEST /agent/ask ===')
try:
    res = requests.post(url_agent, json=payload)
    print("Status:", res.status_code)
    try:
        print(json.dumps(res.json(), ensure_ascii=False, indent=2))
    except:
        print(res.text)
except Exception as e:
    print(e)
