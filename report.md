# Project Report: Deep Agent Suite

## 1. Purpose

This project builds a "deep agent" supervisor model that delegates work to isolated subagents, for a specific task domain currently including: reading, generating, and editing Office documents (`.pptx`, `.docs`, `.xlsx`). The goal was not just to get a model calling tools, but to make it use a genuine skill system: personally-written contraint documents (SKILL.md) that govern how each document type should be handled, loaded on demand rather than embeded permenantly into the system prompt.

## 2. Architecture

**Supervisor/subagent split**: A single supervisor loop `DeepAgent.execute_react_loop` plans and either calls tools directly or delegates a subtask to a subagent scoped to one skill `spawn_worker_subagent`. Each subagent runs its own bounded tool-calling loop, restricted to only the tools its assigned skill's frontmatter lists, which keep a subagent from calling on the wrong/unrelated skill.

**Skills as data, not as prompts**: Each skill is a folder under `skills/` with a `SKILL.md`: providing a YAML-style frontmatter (including: description, tools, triggers) which the supervisor sees as a one-line summary, plus a full constraints body that only the subagent sees after explicitly requesting it via the `load_skill_blueprint` tool call. Multi-file skills: currently it's onyl pptx, that has `editing.md` and `pptxgenjs.md` above just having `SKILL.md`, the model uses `folder/file-stem` addressing to reach a specific reference file.

**Native tool calling**: Early versins parsed JSON action blocks out of plain model text. This disrupted the process during practice as some models spontaneously emit their own internal function-call syntax regardless of prompting, which the API layer then rejects if no formal `tools=` schema was declared. This fix that I applied here was declaring a real tool schema, `TOOL_SCHEMA` in tools.py and read structured `tool_calls` off the reponse directly, in turn eliminating an entire class of slient failures where the subagent appeared to do nothing because its actual tool-call attempt was never being read form the right place in the response object.

**Sandboxed, location-independent output**: All file writings are resolved through `AgentSandbox`, which maps any relative filname that a tool receives into an absolute path inside `outputs/` at the repo root. This replaced an earlier design where file location depended on the processe's working directory at launch time, which creted confusion with "file not found" failures when the harness and direct runs had different working directories.

## 3. Building process




# 4. Current status

- Skill system, native tool calling, and sandbox output are all working and have been verified across the 5 example scenarios via `run_all_scenarios.py`
- Interactive sessions mode accepts arbitrary free-form prompts, not just the built-in scenarios
- Terminal output uses rich-based colored panels distinguishing supervisor thoughts, tool calls, tool outputs, and subagent activity
- Langfuse tracing is wired in, tagging each run with its objective and user id for reviewing whether skill delegation is actually happening as intended
