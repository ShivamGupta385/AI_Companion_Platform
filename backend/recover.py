import json
import os

transcript_path = r"C:\Users\shiva\.gemini\antigravity-ide\brain\0b7f8c18-c4fa-473d-9e44-97fc17c66362\.system_generated\logs\transcript_full.jsonl"

found_content = ""

with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            if "tool_calls" in data:
                for tc in data["tool_calls"]:
                    if tc.get("function", {}).get("name") == "default_api:replace_file_content":
                        args_str = tc["function"]["arguments"]
                        args = json.loads(args_str)
                        if "TargetContent" in args and "canvas_show_question" in args["TargetContent"]:
                            found_content = args["TargetContent"]
        except Exception as e:
            pass

with open(r"c:\Users\shiva\ai-companion-platform\backend\recovered_canvas.tsx", 'w', encoding='utf-8') as out:
    out.write(found_content)
