# PromptOps Toolkit

Local-first prompt workflow tools for AI-assisted builders.

PromptOps Toolkit helps maintainers keep prompts reviewable, reusable, and safer before they are copied into ChatGPT, Codex, Claude, Cursor, or other AI tools.

## Features

- Lint prompt files in `prompts/*.md`
- Check for role sections: system, developer, user
- Detect undeclared template variables like `{topic}` and `{audience}`
- Warn about secret-like or personal-information-like content
- Generate a prompt inventory report
- Run without network access or external dependencies

## Usage

```bash
python3 -m promptops_toolkit lint prompts
python3 -m promptops_toolkit inventory prompts
```

## Why This Exists

Many non-professional developers and working professionals now build with AI by saving prompts in notes, docs, and chat history. That makes prompts hard to review, test, and safely reuse.

This project treats prompts like small source files: structured, documented, checked, and safe to publish.

## Example Prompt Format

```markdown
---
name: blog-outline
variables: topic, audience
---

## System
You are a careful writing assistant.

## Developer
Write clearly and do not invent citations.

## User
Create an outline about {topic} for {audience}.
```

## License

MIT
