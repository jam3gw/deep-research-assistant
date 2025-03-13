# Architecture Diagrams

This folder contains PlantUML diagrams that illustrate the architecture of the personal research assistant system, with a focus on the integration of different AI components (OpenAI, Brave, Anthropic) and how they are utilized in the research generation process.

## Diagrams Overview

1. **system_architecture.puml** - Overall system architecture showing all components and their interactions
2. **question_tree_process.puml** - Sequence diagram showing the question tree generation process
3. **rag_process.puml** - Sequence diagram showing the Retrieval-Augmented Generation (RAG) process
4. **ai_integration.puml** - Component diagram showing detailed AI service integration

## Viewing the Diagrams

These diagrams are written in PlantUML, a text-based diagramming tool. To view them, you have several options:

### Option 1: Online PlantUML Server

1. Go to [PlantUML Online Server](https://www.plantuml.com/plantuml/uml/)
2. Copy and paste the content of any .puml file into the text area
3. The diagram will be rendered automatically

### Option 2: VS Code Extension

1. Install the "PlantUML" extension in VS Code
2. Open any .puml file
3. Use Alt+D to preview the diagram

### Option 3: Generate Images Locally

If you have Java installed, you can use the PlantUML JAR to generate images:

```bash
java -jar plantuml.jar diagrams/*.puml
```

This will generate PNG images for all the diagrams in the folder.

## AI Components Integration

The diagrams highlight how different AI services are integrated into the system:

### Anthropic Claude
- Used for question analysis, sub-question generation, and answer synthesis
- Model: claude-3-5-sonnet-20240620
- Handles the natural language understanding and generation aspects

### OpenAI Embeddings
- Used for text embedding generation and vector similarity search
- Model: text-embedding-3-small
- Enables semantic search capabilities in the RAG process

### Brave Search API
- Used for real-time web search and source retrieval
- Provides up-to-date information for the knowledge base
- Supplies source metadata for attribution

## Architecture Highlights

- **Question Tree Approach**: Complex questions are broken down into sub-questions, creating a hierarchical structure
- **Dynamic Knowledge Base**: The system populates its knowledge base on-demand based on the query
- **Source Attribution**: All answers include citations to their sources
- **Recursive Processing**: Sub-questions are processed recursively to build a comprehensive answer 