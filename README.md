# 🌍 Phileas - AI Travel Assistant

An advanced AI travel concierge that demonstrates effective LLM conversation design, sophisticated prompt engineering, and seamless tool integration. Built with a focus on natural dialogue, context awareness, and practical travel planning capabilities.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.0+-red.svg)
![OpenRouter](https://img.shields.io/badge/OpenRouter-API-green.svg)

## 🚀 Try It Now - No Setup Required!

**🌐 Live Demo**: [https://travel-assistant-agent.streamlit.app/](https://travel-assistant-agent.streamlit.app/)

Experience Phileas directly in your browser with no API keys or installation needed. The hosted version includes all features and demonstrates the full conversation capabilities.

> **Note**: For local development or CLI usage, you'll need your own API keys (see setup instructions below).

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │       CLI        │    │     Tests       │
│   Web App       │    │    Interface     │    │   & Utilities   │
└─────────┬───────┘    └─────────┬────────┘    └─────────────────┘
          │                      │
          └──────────┬───────────┘
                     │
┌────────────────────▼────────────────────┐
│         Conversation Manager            │
│   • Message routing & validation        │
│   • Tool orchestration                  │
│   • Response generation                 │
└─┬─────┬─────────────────────────┬───────┘
  │     │                         │
  │     │                    ┌────▼──────┐
  │     │                    │  Context  │
  │     │                    │  Manager  │
  │     │                    └─────┬─────┘
  │     │                          │
  │ ┌───▼────────┐          ┌──────▼──────┐
  │ │  Weather   │          │  OpenRouter │◄─┐
  │ │  Client    │          │   Client    │  │
  │ └─────┬──────┘          └──────┬──────┘  │
  │       │                        │         │
  │ ┌─────▼─────┐            ┌─────▼─────┐   │
  │ │OpenWeather│            │ DeepSeek/ │   │
  │ │    API    │            │  Llama/   │   │
  │ └───────────┘            │   Qwen    │   │
  │                          │  Models   │   │
  │                          └───────────┘   │
  │                                          │
  └──────────────────────────────────────────┘
```

### 📂 Example Conversations

See the `Demos/` folder for comprehensive conversation examples showcasing:
- Budget travel planning with constraint handling
- Multi-destination trip coordination
- Weather-aware activity recommendations
- Context evolution and user preference learning
- Tool integration demonstrations

## 🤖 AI Models & Capabilities

Phileas leverages multiple state-of-the-art language models for different conversation needs:

### **Primary Models**
- **Chat & Conversation**: `deepseek/deepseek-chat-v3-0324` - Fast, natural dialogue
- **Deep Planning**: `deepseek/deepseek-r1` - Advanced reasoning for detailed itineraries
- **Context Analysis**: `deepseek/deepseek-chat-v3-0324` - User preference understanding

### **Backup Models** (Automatic Fallback)
- **Chat Backup**: `meta-llama/llama-3.3-70b-instruct`
- **Planning Backup**: `qwen/qwen3-235b-a22b`

### **Model Selection Strategy**
- **Smart Routing**: Automatically selects the best model for each task
- **Graceful Fallbacks**: Switches to backup models if primary models are unavailable
- **Cost Optimization**: Uses free-tier models without compromising quality

#### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd phileas-travel-assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys** (Required for local usage)
   
   Create a `.env` file in the project root:
   ```env
   OPENROUTER_API_KEY=sk-or-your-api-key-here
   OPENWEATHER_API_KEY=your-weather-api-key-here  # Optional
   ```

4. **Run locally**
   
   **Web Interface:**
   ```bash
   streamlit run app.py
   ```
   
   **CLI Interface** (requires API keys):
   ```bash
   python cli_run.py
   ```

## 💻 Usage Examples

### Web Interface
Launch the Streamlit app and start chatting with Phileas. The assistant will:

1. **Understand your needs**: "I want to plan a relaxing vacation"
2. **Ask focused questions**: "Are you picturing a secluded beach or somewhere with activities nearby?"
3. **Use tools when helpful**: Automatically check weather for your travel dates
4. **Create detailed plans**: Generate comprehensive itineraries using the reasoning model

### CLI Interface
```bash
# Start with conversation tracking (requires API keys)
python cli_run.py

# Start without tracking
python cli_run.py --no-tracking

# Custom session ID
python cli_run.py --session my_tokyo_trip
```

## 🔧 Configuration

### Response Types
- **chat**: Normal conversational responses (800 tokens)
- **reasoning**: Detailed planning and analysis (4000 tokens)
- **simple**: Quick answers and confirmations (300 tokens)

### Rate Limits
- Free tier: 20 requests per minute
- Automatic retry with exponential backoff
- Graceful fallback to backup models

## 🛠️ Advanced Features

### Context Management
The assistant maintains sophisticated user context through LLM-powered analysis:

```
# Context automatically captures:
- Date and Time
- Travel preferences and constraints
- Communication style and personality
- Trip purpose and priorities
- Budget and timeline considerations
```

### Tool Integration

**Weather Tool:**
```
$!$TOOL_USE_START$!$
Tool: Weather
Location: Barcelona, Spain
Start_Date: 2025-08-23
End_Date: 2025-08-30
$!$TOOL_USE_END$!$
```

**Deep Planning Tool:**
```
$!$TOOL_USE_START$!$
Tool: Deep_Planning
Prompt: Create a 5-day Tokyo itinerary for a vegetarian traveler on a $1500 budget
$!$TOOL_USE_END$!$
```
## ✨ Key Features

### 🎯 **Conversation-First Design**
- **Natural Dialogue Flow**: Implements advanced conversation patterns that feel human and helpful
- **Context Awareness**: Maintains user preferences and trip details across the entire conversation
- **Progressive Engagement**: Guides users from uncertainty to concrete plans through intelligent questioning

### 🛠️ **Advanced Tool Integration**
- **Weather Integration**: Real-time weather forecasts via OpenWeatherMap API
- **Deep Planning Tool**: Uses reasoning models for comprehensive itinerary generation
- **Smart Tool Selection**: Automatically determines when to use external data vs. LLM knowledge

### 🧠 **Sophisticated Prompt Engineering**
- **Chain of Thought Planning**: Multi-step reasoning process for complex travel plans
- **Dynamic System Prompts**: Context-aware prompts that adapt to user needs
- **Feasibility-First Approach**: Ensures all suggestions are realistic and actionable

### 💬 **Enhanced User Experience**
- **Edit & Retry**: Users can edit messages or regenerate responses
- **Multi-Language Support**: Including Hebrew with RTL text support
- **Real-Time Streaming**: Generator-based responses with status updates
- **Session Tracking**: Comprehensive conversation analytics and transcripts

### Conversation Tracking
Comprehensive session tracking with multiple output formats:

- **transcript.md**: Human-readable conversation log
- **context_evolution.md**: User context progression over time
- **session_data.json**: Performance metrics and metadata
- **Session_Summary.md**: Overview with statistics


### Development Setup
```bash
# Install development dependencies
pip install pytest

# Run tests
pytest tests/

# Check configuration
python -c "from src.utils.config import Config; Config.display_config()"
```


## 🎨 Prompt Engineering Highlights

### Chain of Thought Planning
```
1. Deconstruct the Request: What is the core goal?
2. Formulate a Plan of Action: Outline the structure
3. Generate the Response Content: Gather and structure information
4. Final Review: Self-correction against original request
```

### Dynamic System Prompts
- Context-aware persona adaptation
- User-specific conversation history integration
- Tool availability and usage guidance

### Conversation Patterns
- **Guiding Question Principle**: Help lost users find focus
- **Progressive Engagement**: Build momentum through exploration
- **Feasibility First**: Ensure realistic recommendations

## 🌐 Multi-Language Support

### Hebrew Support
- RTL text detection and rendering
- Unicode character handling
- Streamlit CSS integration for proper display

### Language Detection
- Automatic language identification
- Response generation in user's preferred language
- Cultural context awareness


## 🚧 Known Limitations

1. **Weather Forecasting**: Limited to 5-6 days in advance
2. **Real-time Data**: No access to current prices, availability, or bookings
3. **Model Dependencies**: Performance depends on OpenRouter model availability
4. **Rate Limits**: Free tier constraints may affect response times


