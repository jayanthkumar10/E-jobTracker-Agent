import json

path = r"C:\Users\HP\.gemini\antigravity\brain\d919dc68-a7ee-423d-9849-92ddabb50eb9\.system_generated\logs\transcript.jsonl"
with open(path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i == 539:
            obj = json.loads(line)
            print("Type:", obj.get("type"))
            if "tool_calls" in obj:
                print(json.dumps(obj["tool_calls"], indent=2))
            break
