# Project Report: Deep Agent Suite

## 1. Purpose

This project builds a "deep agent" supervisor model that delegates work to isolated subagents, for a specific task domain currently including: reading, generating, and editing Office documents (`.pptx`, `.docx`, `.xlsx`). The goal was not just to get a model calling tools, but to use a genuine skill system: personally-written constraint documents (SKILL.md) that govern how each document type should be handled, combined with the LangChain orchestration library so the reliability work goes to the library rather than being written-up from scratch.

## 2. Architecture

**Supervisor/subagent split via `deepagents`**: `create_deep_agent(...)` builds a LangChain agent from a model, a backend, a list of subagents, a `system_prompt`, and a list of permissions. The supervisor delegates to a named subagent through deepagents' native task tool. Each subagent is declared up front - once per skill folder - with its own `system_prompt` (that's custom built from the `SKILL.md` file) and its own restricted tool list, so tool restriction and context isolation come from the library's own subagent middleware, not a custom sandbox.

**Skills as data**: Each skill is a folder under `skills/` with a `SKILL.md`: providing a YAML-style frontmatter (including: name, description, tools, triggers) plus a constraints body. They are directly loaded into the subagents prompt. 

**Native tool calling**: The tools are simple `@tool`-identified Langchain functions with real hints, letting LangChain infer the argument schema. 

**Filesystem access via `FilesystemBackend` and `FilesystemPermissions`**: `FilesystemBackend(root_dir=repo_root, virtual_mode=True)` gives the agent scoped `ls/glob/read_file/write_file/edit_file` tools. On top of that, FilesystemPermission rules enforce two hard, code-level rules: reading/writing `.pptx/.docx/.xlsx` through the generic filesystem tools is denied outright (forcing the use of the dedicated office-file tools instead), and any write into `outputs/` triggers a human-in-the-loop interruption. Custom tools still resolve their own `filepath` argument via a `_resolve()` helper, since `FilesystemBackend`'s scoping only covers deepagents' own built-in tools, not tools that call `openpyxl/python-docx/python-pptx` directly.

**Multi-provider fallback**: The supervisor loop tries multiple models in the progression of Cerebras, then Groq, then Gemini, rebuilding the agent graph fresh for each attempts. Any failure at a given provider such as: quota exhaustion, an oversized request, a malformed response, a deprecated model - is logged with its type and the loop moves to the next provider; if all three fail, one readable error is raised listing what happened at each.

## 3. Building process

The migration from a hand-built ReAct loop to `deepagents` brought to the surface a mix of logic and structural bugs. 

The pure Python bugs, unrelated to the AI layer, included: an incorrectly indented return statement that failed silently — no error was raised, it just didn't provide the necessary capability, and was found via a local script that constructs the agent without invoking it; and undefined names plus a call to a function deleted during an earlier edit. These and other few bugs had nothing to do with model behavior, and they were all caught simply with `pytest` and a agent-construction script, which was considerably faster than the live-LLM run cycle that found the first few.

Another "safety" precursor of the early version of the model was the xlsx tool that would write hardcoded placeholder numbers into a spreadsheet if the model's data argument looked malformed, and report success regardless, which was worse than a crash, since it would produce a plausible-looking but wrong Excel spreadsheet with no visible failure signal.

The path handling needed a rewrite, not a patch. Since `Path.is_absolute()` treats a leading `/` as an absolute (on Windows) even when it's actually a `FilesystemBackend` virtual path (e.g. `/outputs/somedoc.xlsx`), so an initial fix that branched on `is_absolute()` still resolved to a nonexistent real path. The fix that held up was - to never trust the path style at all, and to always extract just the filename and force it into `outputs/`.

Model choice and version significantly affected reliability and performance. Additionally per-request (TPM) ceiling turned out to be more of an issue than originally thought of. So the best solution that is currently employed is a file-based handoff design, where subagents write large results to a file and report back a short confirmation, instead of the supervisor accumulating and re-sending full content across every subsequent turn.

Prompt-only enforcement proved unreliable for content quality. Multiple rounds of instructing the docx skill to prefer narative and written out outputs over bullet points were followed inconsistently. The fix that held up was moving the check into the tool itself - `create_word_document` now computes the actual bullet-to-total-line ratio and rejects content over a 35% threshold with a specific rewrite instruction, which produces a deterministic result regardless of whether the model "remembers" a prompt rule three turns later. The same pattern (library/code-level enforcement over prompt-only instruction) was applied for filesystem safety via `FilesystemPermission`'s `deny/interrupt` modes rather than asking the model nicely not to touch certain paths.

One library-fit lesson worth recording is: `Runnable.with_fallbacks()` is a real, general LangChain mechanism for chaining models with automatic fallback, but it's incompatible with `create_deep_agent`'s `model=parameter` specifically, so deepagents inspects the model at construction time to apply a provider-specific profile, and a fallback-wrapped runnable doesn't resolve to a single identifiable provider. The working design ended up being a manual per-attempt loop that rebuilds a plain, single-provider model on each try, a case where a generically "more correct" library feature didn't hold up against a specific downstream consumer's assumptions, which is now worth verifying against the actual call site rather than the method's existence alone.


# 4. Current status

- Skill-based subagent delegation, native tool calling, `FilesystemPermission`-based safety rules, and the provider fallback chain are all working and have been verified across the 5 example scenarios provided via `run_all_scenarios.py`, plus several extra prompts exercising cross-provider fallback and content-quality enforcement
- A `tests/` directory with `pytest` unit tests covers path resolution, xlsx formula preservation, and the bullet-vs-text content gate - all runnable with zero API cost, added specifically because most bugs found during this migration were deterministic Python logic errors that a live LLM run was tedious to use for discovery
- `debug_subagents.py` provides a zero-cost structural check that all skill subagents actually build correctly, the kind of check that would have caught the `return`-in-loop bug instantly instead of via a live trace
- Terminal output uses rich-based colored panels with timestamps, streamed live from `agent.stream()`, including through `run_all_scenarios.py` (which no longer buffers subprocess output)
- Langfuse tracing is wired in with nested spans per subagent delegation and per model call, tagged with objective and user id, which has repeatedly been the deciding factor in diagnosing issues that terminal output alone didn't fully explain
- Open items: missing-file handling has prompt-level instruction but no code-level backstop yet; `memory.py`'s long-term store is unbounded and worth capping before it becomes its own token-budget problem; document formatting quality checks currently cover bullet-vs-text but not tables or richer slide layouts