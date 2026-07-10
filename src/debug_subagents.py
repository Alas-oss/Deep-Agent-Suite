import sys
sys.path.insert(0, "src")
from agent import DeepAgent

d = DeepAgent(objective="debug only, not run", user_id="debug")
print("skills discovered:", list(d.available_skills_index.keys()))
subs = d._build_skill_subagents()
print("subagent count:", len(subs))
for s in subs:
    print(" -", s["name"], "| tools:", [t.name for t in s["tools"]], "| prompt length:", len(s["system_prompt"]))