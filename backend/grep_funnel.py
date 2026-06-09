import json

path = r"C:\Users\HP\.gemini\antigravity\brain\d919dc68-a7ee-423d-9849-92ddabb50eb9\.system_generated\logs\transcript.jsonl"
with open(path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "funnel" in line.lower():
            print(f"Line {i} matches funnel.")
            # print characters around the first occurrence of "funnel"
            idx = line.lower().find("funnel")
            start = max(0, idx - 100)
            end = min(len(line), idx + 200)
            print(f"  Snippet: {line[start:end]}")
