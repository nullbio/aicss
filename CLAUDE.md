# CLAUDE.md - AI CSS FRAMEWORK

Natural language AI machine learning CSS compiler/transpiler with watch mode.

## Code Style Guidelines

- Type hints required for all functions and classes (PEP 484)
- Docstrings using PEP 257 convention for all functions/classes
- Descriptive variable/function names (no abbreviations)
- Clear error handling for missing entities or bindings
- Document tensor shapes and normalization expectations
- Modularized code
- Unit tests

## Project Structure

- Modular design with separate files for models, services, and utilities
- Tests should be in ./tests with pytest (no unittest)

## Dependencies

- TBD

## MCP Usage Guidelines

Use MCPs only when more efficient than standard tools:

- **Filesystem MCP**: Use for bulk operations (listing directories, recursive searches) or when searching for patterns across many files. Use standard View/Edit tools for individual file operations. Do not use to write files.

- **GitHub MCP**: Only use for GitHub operations; prefer standard tools for local operations.

- **Brave Search MCP**: Only use when external information is needed that's not in the codebase or your memory.

- **Sequential Thinking MCP**: Reserve for complex multi-step reasoning that requires maintaining state or exploring multiple paths.

- **Python with Conda MCP**: Use for running code that needs to be tested, or when complex computation is required.

- **Memory MCP**: Use for information that needs to persist across separate conversations.

## Behaviour

Be proactive and helpful. While you're performing tasks, also consider other tasks that might be relevant and useful to perform, and complete them as well. Take initiative.

If you're not sure about something, make the most rational assumption and take action, but if there is no clear answer or path forward, consult the user for clarification.

Begin your first action by understanding the codebase, starting with the .cursor/rules/*.mdc files, and then the README.md file, and following directions from there.

At the end of every lengthy response, consider all of the actions you took in the last steps since you last updated the CLAUDE.md file. Assess whether there are any important notes or memories you wish to store, and store those in your graph memory structure using the MCP. Also determine whether we need to make any additions to the CLAUDE.md file in terms of short, behavioural adjustments, tweaks, or additions. If so, add them to the file.

If any of our core dependencies change, add them (or adjust them) in our CLAUDE.md file.

If executing python code, make sure you've activated the venv first in this root project directory.
