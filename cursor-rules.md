# Cursor Rules for AWS Lambda Development

## Lambda Filesystem Access

**Rule**: Always use the `/tmp` directory for any file operations in AWS Lambda environments.

**Explanation**: The Lambda execution environment has a read-only filesystem except for the `/tmp` directory. Any attempts to write to other directories (like `/var/task`) will result in a "Read-only file system" error.

**Implementation**:
```python
# Check if running in Lambda environment
if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
    # We're running in Lambda, use /tmp directory
    file_path = os.path.join('/tmp', 'filename.json')
else:
    # Local development environment
    file_path = os.path.join(os.path.dirname(__file__), 'data/filename.json')

# Ensure the parent directory exists
os.makedirs(os.path.dirname(file_path), exist_ok=True)
```

## Comprehensive Error Handling in Lambda Functions

**Rule**: Implement detailed logging and error handling in Lambda functions to diagnose issues in production.

**Explanation**: Lambda functions run in a remote environment where direct debugging is not possible. Comprehensive logging and error handling are essential for diagnosing issues.

**Implementation**:
```python
import time
import traceback

def lambda_handler(event, context):
    start_time = time.time()
    
    try:
        print(f"Starting processing for input: {event}")
        
        # Main processing logic
        result = process_data(event)
        
        processing_time = time.time() - start_time
        print(f"Processing completed successfully in {processing_time:.2f} seconds")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"ERROR during processing: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception traceback: {traceback.format_exc()}")
        print(f"Failed after {processing_time:.2f} seconds")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f"Processing failed: {str(e)}"
            })
        }
```

## Token Management for LLM Responses

**Rule**: Reserve tokens for important content (like sources) when generating responses with LLMs.

**Explanation**: When generating responses with token limits, it's important to reserve tokens for critical content that must be included in the response.

**Implementation**:
```python
# Calculate token limit, reserving tokens for sources
base_token_limit = get_token_limit_for_depth(DEFAULT_MAX_TOKENS, depth)
sources_token_estimate = estimate_sources_tokens(sources)
# Reserve tokens for sources plus a buffer
reserved_tokens = min(sources_token_estimate + 100, base_token_limit // 4)
adjusted_token_limit = base_token_limit - reserved_tokens

print(f"Token allocation: Base={base_token_limit}, Reserved={reserved_tokens}, Available={adjusted_token_limit}")

# Generate response with adjusted token limit
response = llm_client.generate(
    prompt=prompt,
    max_tokens=adjusted_token_limit
)
```

## Source Attribution in RAG Applications

**Rule**: Ensure consistent source attribution in RAG (Retrieval-Augmented Generation) applications.

**Explanation**: When using RAG to generate content, it's important to properly attribute sources and ensure they are consistently displayed to users.

**Implementation**:
```python
# Collect and deduplicate sources
sources = []
for doc in relevant_docs:
    if 'metadata' in doc and 'source' in doc['metadata']:
        source_url = doc['metadata']['source']
        source_title = doc['metadata'].get('title', 'Untitled Source')
        sources.append({
            'url': source_url,
            'title': source_title
        })

# Deduplicate sources
unique_sources = []
seen_urls = set()
for source in sources:
    url = source.get('url', '')
    if url and url not in seen_urls:
        unique_sources.append(source)
        seen_urls.add(url)

# Add sources section to the response
if unique_sources:
    sources_html = "<div class=\"sources\"><h2>Sources</h2><ol>"
    for source in unique_sources:
        sources_html += f"<li>{source['title']} - <a href=\"{source['url']}\">{source['url']}</a></li>"
    sources_html += "</ol></div>"
    
    response += f"\n\n{sources_html}"
``` 