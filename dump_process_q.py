from pathlib import Path
content = Path("ai_service_n1n.py").read_text(encoding="utf-8")
idx = content.find("async def process_question")
if idx < 0:
    print("NOT FOUND")
else:
    end = content.find("\n    async def ", idx + 10)
    if end < 0:
        end = content.find("\n    def ", idx + 10)
    if end < 0:
        end = len(content)
    Path("dump_process_q.txt").write_text(content[idx:end], encoding="utf-8")
    print(f"OK ({len(content[idx:end])} B)")