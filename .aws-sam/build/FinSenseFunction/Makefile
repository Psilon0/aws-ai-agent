.PHONY: dev smoke
dev:
\tuvicorn src.api.app:app --reload --port 8000

smoke:
\tpython - <<'PY'\nimport json,urllib.request\nbase='http://127.0.0.1:8000'\nprint('health:',urllib.request.urlopen(base+'/health').read().decode())\nreq=urllib.request.Request(base+'/chat',data=json.dumps({'message':'hello'}).encode(),headers={'content-type':'application/json'})\nprint('chat:',urllib.request.urlopen(req).read().decode())\nPY
