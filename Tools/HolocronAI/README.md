# HolocronAI

A Star Wars character AI chat interface using PyQt and LLMs. This tool allows users to interact with AI-powered versions of characters from Knights of the Old Republic, leveraging game dialog data to maintain authentic character personalities.

## Features

- Modern PyQt-based UI with dark theme
- Real-time character-by-character response generation
- Dialog embedding generation for character personality modeling
- Customizable LLM backend through LiteLLM
- Game installation integration through PyKotor

- Extracts all dialogs from KOTOR installations
- Uses DITTO self-alignment framework for dynamic response generation
- Implements Beyond Dialog concepts for contextual understanding
- No hardcoded patterns or pre-training required
- Maintains character consistency through embedding-based alignment

## Installation

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install in development mode:

```bash
pip install -e .
```

## Usage

Run the application:

```bash
holocron-ai
```

1. Select your KOTOR game installation directory
2. Wait for dialog processing and embedding generation
3. Choose a character to interact with
4. Start chatting!

The system will:

1. Extract all dialogs from the installation
2. Process them through the self-alignment system
3. Start an interactive session where you can chat with the character

## How It Works

HolocronAI uses three main components:

1. **Dialog Processor**: Extracts and processes dialogs from KOTOR installations, converting them into embeddings that capture semantic meaning.

2. **Self-Alignment System**: Implements the DITTO framework to maintain character consistency without relying on hardcoded patterns. This system:
   - Dynamically learns from dialog embeddings
   - Adjusts responses based on conversation context
   - Maintains character consistency through embedding alignment

3. **Character Agent**: Combines the dialog processor and self-alignment system to generate responses that are:
   - Contextually appropriate
   - Character-consistent
   - Based on actual game dialog

## Example Interaction

```
> Hello there!

Character: I see you're not one for subtlety. Very well - I'll be direct as well.

> What do you think about the Jedi?

Character: The Jedi... Their Code is their weakness. The galaxy has far more 
shades of gray than their black and white philosophies would suggest.
```

## Technical Details

- Uses sentence-transformers for generating embeddings
- Implements dynamic context weighting based on semantic similarity
- Maintains conversation history with sliding context window
- Automatically saves processed data for faster subsequent runs

## Requirements

- Python 3.8+
- KOTOR installation
- Dependencies listed in setup.py

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
