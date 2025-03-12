# Cursor Rules

This directory contains custom rules for the Cursor IDE to enhance the development experience for the personal-assistant project.

## What are Cursor Rules?

Cursor rules allow you to customize how the AI assistant behaves when working with your codebase. Rules can:

1. Provide project-specific context
2. Define coding standards and conventions
3. Guide the AI to follow specific patterns
4. Improve code suggestions and completions

## Rules Structure

Each rule is defined in its own file with a specific format:

- `.cursor/rules/*.mdc` - Markdown files containing rules
- `.cursor/rules/*.json` - JSON configuration files

## Available Rules

- `code-style.mdc` - Coding style guidelines
- `project-context.mdc` - Overview of the project architecture
- `rag-implementation.mdc` - Guidelines for RAG (Retrieval Augmented Generation) implementation
- `tree-visualization.mdc` - Guidelines for tree visualization component
- `tree-depth-handling.mdc` - Guidelines for handling depth in tree visualization
- `tree-testing.mdc` - Guidelines for testing tree visualization

## How to Add a New Rule

1. Create a new markdown file with `.mdc` extension in the `.cursor/rules/` directory
2. Start with a clear title and description
3. Use sections to organize different aspects of the rule
4. Be specific and provide examples where possible

## How Rules are Applied

Cursor automatically reads these rules when you open the project and incorporates them into its understanding of your codebase. The AI will reference these rules when:

- Generating code completions
- Answering questions about the codebase
- Making suggestions for improvements
- Helping with debugging and problem-solving 