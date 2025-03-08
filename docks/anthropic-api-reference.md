# Anthropic API Reference

## Core Concepts

### Models
- `claude-3-7-sonnet-20250219`: Most intelligent model with extended thinking capabilities
- `claude-3-5-sonnet-20241022`: High performance model balancing intelligence and speed
- `claude-3-5-haiku-20241022`: Fast, cost-effective model
- `claude-3-opus-20240229`: Strong performance on complex tasks
- `claude-3-sonnet-20240229`: Balanced intelligence and speed
- `claude-3-haiku-20240307`: Fast, responsive model

### Messages API
Core API for interacting with Claude models.

```python
import anthropic

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    system="System instructions here",
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ]
)
```

#### Parameters
- `model`: Model identifier (required)
- `max_tokens`: Maximum tokens in the response (default: 4096)
- `system`: System prompt to guide Claude's behavior (optional)
- `messages`: List of message objects representing conversation history (required)
- `temperature`: Controls randomness (0.0-1.0, default: 1.0)
- `top_p`: Controls diversity via nucleus sampling (0.0-1.0, default: 1.0)
- `top_k`: Limits vocabulary token selection (default: null)
- `stop_sequences`: Array of strings that will cause the model to stop generating
- `stream`: Boolean to enable streaming responses (default: false)
- `metadata`: Custom metadata to include with the request
- `tool_choice`: Control model's tool selection strategy
- `betas`: Enable beta features

#### Response Object
```json
{
  "id": "msg_01XXX...",
  "type": "message",
  "role": "assistant",
  "content": [{"type": "text", "text": "Hello! How can I help you today?"}],
  "model": "claude-3-7-sonnet-20250219",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 10,
    "output_tokens": 9
  }
}
```

### Content Blocks
Claude can work with different content types in messages:

- `text`: Regular text content
- `image`: Images passed as base64 or URLs
- `tool_use`: Tool usage requests from Claude
- `tool_result`: Results of tool execution
- `thinking`: Reasoning outputs with extended thinking
- `redacted_thinking`: Encrypted reasoning blocks

### Tools
Enable Claude to call functions and use tools to extend capabilities.

```python
tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather in a location",
        "input_schema": {
            "type": "object",
            "properties":                 "type": "document",
                "source": {
                    "type": "text",
                    "media_type": "text/plain",
                    "data": "This document contains important information..."
                },
                "title": "Document Title",
                "citations": {"enabled": true}
            },
            {"type": "text", "text": "What does this document say about X?"}
        ]}
    ]
)
```

Response with citations:
```json
{
  "content": [
    {
      "type": "text",
      "text": "According to the document, ",
      "citations": [{
        "type": "char_location",
        "cited_text": "The document says X is important.",
        "document_index": 0,
        "document_title": "Document Title",
        "start_char_index": 10,
        "end_char_index": 40
      }]
    }
  ]
}
```

### Token Counting
Estimate token usage before sending requests.

```python
token_count = client.messages.count_tokens(
    model="claude-3-7-sonnet-20250219",
    system="You are a helpful assistant.",
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ]
)
print(token_count.input_tokens)  # Shows estimated token usage
```

### Batch Processing
Process multiple requests asynchronously.

```python
batch_response = client.messages.batches.create(
    requests=[
        {
            "custom_id": "request-1",
            "params": {
                "model": "claude-3-7-sonnet-20250219",
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": "Summarize climate change."}
                ]
            }
        },
        {
            "custom_id": "request-2",
            "params": {
                "model": "claude-3-7-sonnet-20250219",
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": "Explain quantum physics."}
                ]
            }
        }
    ]
)

# Check batch status
batch_status = client.messages.batches.retrieve(batch_response.id)

# Retrieve results when processing ends
if batch_status.processing_status == "ended":
    results = client.messages.batches.results(batch_status.id)
    for result in results:
        print(f"Result for {result['custom_id']}: {result['result']}")
```

### Computer Use (Beta)
Enable Claude to interact with a virtual desktop environment.

```python
tools = [
    {
        "type": "computer_20250124",  # Claude 3.7 Sonnet
        "name": "computer",
        "display_width_px": 1024,
        "display_height_px": 768
    },
    {
        "type": "text_editor_20250124",
        "name": "str_replace_editor"
    },
    {
        "type": "bash_20250124",
        "name": "bash"
    }
]

message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=4096,
    messages=[
        {"role": "user", "content": "Save a picture of a cat to my desktop."}
    ],
    tools=tools,
    betas=["computer-use-2025-01-24"]
)
```

Computer actions include:
- `screenshot`: Take a screenshot
- `key`: Press keyboard keys
- `type`: Type text
- `mouse_move`: Move cursor
- `left_click`: Click mouse
- `scroll`: Scroll screen
- `wait`: Wait for a duration

## Utility Features

### Streaming Responses
Get token-by-token responses in real-time.

```python
with client.messages.stream(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Write a short story about a robot."}
    ]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

Event types:
- `message_start`: Start of message
- `content_block_start`: Start of content block
- `content_block_delta`: Content update
- `content_block_stop`: End of content block
- `message_delta`: Message metadata update
- `message_stop`: End of message

### Error Handling
Common error types:
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Invalid API key
- `403 Forbidden`: Permissions issue
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500/502/503/504`: Server errors

```python
try:
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "Hello, Claude!"}
        ]
    )
except anthropic.APIStatusError as e:
    print(f"API error: {e.status_code} - {e.message}")
except anthropic.APIConnectionError:
    print("Connection error")
except anthropic.APITimeoutError:
    print("Request timed out")
except anthropic.APIError as e:
    print(f"Unexpected error: {e}")
```

## Rate Limits

- **Messages API**: Limits based on organization tier (1-4)
- **Token Counting API**: Separate RPM limits
- **Message Batches API**: Batch-specific rate limits

## Additional Notes

### Context Window
- 200K tokens for all Claude 3 models
- Context window = input tokens + output tokens
- With extended thinking: context = (input tokens - previous thinking tokens) + current thinking tokens + text output tokens

### Multilingual Support
Claude performs well in multiple languages, with performance relative to English:
- Spanish: 97.6%
- French: 96.9%
- German: 96.2%
- Chinese: 95.3%
- Japanese: 95.0%
- Hindi: 94.2%

### Security and Compliance
- SOC 2 Type 2 certified
- HIPAA compliance options available
- Data is not stored beyond processing duration
- Organization and workspace isolation

### Pricing
Varies by model:
- Claude 3.7 Sonnet: $3/MTok input, $15/MTok output
- Claude 3.5 Sonnet: $3/MTok input, $15/MTok output
- Claude 3.5 Haiku: $0.80/MTok input, $4/MTok output
- Claude 3 Opus: $15/MTok input, $75/MTok output

Extended thinking tokens count as output tokens.
Prompt caching: Cache writes cost 25% more than base input, cache hits cost 90% less.
Batch processing: 50% off standard API prices.location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The unit of temperature"
                }
            },
            "required": ["location"]
        }
    }
]

message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "What's the weather in San Francisco?"}
    ],
    tools=tools
)
```

#### Tool Response Handling
When Claude requests a tool, it returns:
```json
{
  "type": "tool_use",
  "id": "toolu_01X...",
  "name": "get_weather",
  "input": {
    "location": "San Francisco, CA",
    "unit": "celsius"
  }
}
```

Return tool results to Claude:
```python
message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "What's the weather in San Francisco?"},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "toolu_01X...", "name": "get_weather", 
             "input": {"location": "San Francisco, CA", "unit": "celsius"}}
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_01X...", 
             "content": {"temperature": 18, "condition": "Sunny"}}
        ]}
    ]
)
```

## Extended Features

### Extended Thinking
Available with Claude 3.7 Sonnet, allows seeing Claude's reasoning process.

```python
message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=4096,
    messages=[
        {"role": "user", "content": "Solve this math problem: 27 * 453"}
    ],
    thinking={"type": "enabled", "budget_tokens": 4000}
)
```

Response contains both thinking and text blocks:
```json
{
  "content": [
    {
      "type": "thinking",
      "thinking": "Let me solve this step by step...",
      "signature": "zbbJhbGciOiJFU8zI1NiIsImtakcjsu38219c0..."
    },
    {
      "type": "text",
      "text": "27 * 453 = 12,231"
    }
  ]
}
```

### Vision
Claude can analyze images alongside text.

```python
message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": "base64_encoded_image_data"
                }
            },
            {"type": "text", "text": "Describe this image."}
        ]}
    ]
)
```

Alternative URL-based method:
```python
message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": [
            {
                "type": "image",
                "source": {
                    "type": "url",
                    "url": "https://example.com/image.jpg"
                }
            },
            {"type": "text", "text": "Describe this image."}
        ]}
    ]
)
```

### PDF Support
Process PDFs for analysis and question-answering.

```python
message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": "base64_encoded_pdf_data"
                }
            },
            {"type": "text", "text": "Summarize this document."}
        ]}
    ]
)
```

Or using a URL:
```python
message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": [
            {
                "type": "document",
                "source": {
                    "type": "url",
                    "url": "https://example.com/document.pdf"
                }
            },
            {"type": "text", "text": "Summarize this document."}
        ]}
    ]
)
```

### Prompt Caching
Optimize repeated API calls by caching prompt prefixes.

```python
message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    system={
        "type": "text",
        "text": "You are a helpful assistant.",
        "cache_control": {"type": "ephemeral"}
    },
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ]
)
```

Usage tracking fields:
- `cache_creation_input_tokens`: Tokens written to cache
- `cache_read_input_tokens`: Tokens retrieved from cache
- `input_tokens`: Non-cached tokens processed

### Citations
Enable Claude to provide citations when answering questions about documents.

```python
message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": [
            {
                "