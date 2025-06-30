# Intelligent Document Query System - AI RAG Web Application

## Project Overview

This is an intelligent document query system based on RAG (Retrieval-Augmented Generation) technology. The system combines document retrieval, intelligent filtering, and automated answer generation to quickly find relevant information from large document collections and provide accurate answers. It's suitable for various scenarios including enterprise knowledge base management, technical documentation queries, and customer support.

## Core Features

### 🔍 Intelligent Document Retrieval
- Support for multiple document formats: TXT, PDF, MD, JSON, DOCX, DOC, XLSX, XLS
- Vector search based on semantic similarity
- Support for time range filtering
- Automatic document timestamp extraction

### 🤖 AI Agent System
- Multi-agent collaboration system built with AutoGen framework
- Document filtering agent: Intelligently determines document relevance to queries
- Answer synthesis agent: Integrates relevant documents to generate comprehensive answers
- Support for Ollama local LLM models

### 🌐 Multi-User Independence
- IP-based user isolation mechanism
- Each IP user has an independent agent execution environment
- Support for concurrent multi-user access without interference
- Automatic task termination for current IP when page is refreshed

### 📊 Real-time Processing Feedback
- Server-Sent Events (SSE) real-time streaming responses
- Detailed processing step display: Search → Filter → Answer Generation
- Task progress tracking and status management
- Detailed interaction records of the filtering process

### 📁 Document Management
- Web interface document upload
- Batch document processing
- Document list viewing and management
- Document content preview
- Support for document deletion and batch deletion

### 📝 Query History
- Complete query history records
- Historical query result viewing
- Support for history record deletion
- Filtering interaction process replay

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   Flask Backend │    │   Ollama LLM    │
│   (HTML/JS/CSS) │◄──►│   (Python)      │◄──►│   (Local)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Vector DB     │
                       │   (JSON-based)  │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   AutoGen       │
                       │   Multi-Agent   │
                       └─────────────────┘
```

## Technology Stack

### Backend Technologies
- **Python 3.x**: Primary development language
- **Flask**: Web framework
- **AutoGen**: Multi-agent collaboration framework
- **Ollama**: Local LLM service
- **LangChain**: Document processing and splitting
- **Scikit-learn**: Vector similarity computation
- **OpenCC**: Simplified/Traditional Chinese conversion

### Frontend Technologies
- **HTML5/CSS3**: Page structure and styling
- **JavaScript (ES6+)**: Interactive logic
- **Server-Sent Events**: Real-time data streaming
- **Bootstrap**: UI framework

### Data Storage
- **JSONVectorDB**: Custom vector database
- **JSON**: Document and metadata storage
- **File System**: Uploaded document management

## Installation and Deployment

### System Requirements
- Python 3.8+
- Ollama service
- 8GB+ RAM (recommended)
- 10GB+ disk space

### 1. Clone the Project
```bash
git clone <repository-url>
cd agentic_rag_web_0627
```

### 2. Install Dependencies
```bash
pip install flask ollama autogen langchain pandas python-docx numpy scikit-learn opencc-python-reimplemented
```

### 3. Configure Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download required models (choose other models as needed)
ollama pull llama2:7b
ollama pull nomic-embed-text
```

### 4. Configure Models
Edit the `agent_rag_0609.py` file and configure according to your model selection:
```python
# Modify to use your chosen models
self.embedding_model = "nomic-embed-text"
self.llm_model = "llama2:7b"
```

### 5. Start the Service
```bash
# Use the startup script
python start_server.py

# Or start directly
python app.py
```

### 6. Access the System
Open your browser and visit: http://localhost:5000

## Usage Guide

### Document Upload
1. Go to the management page: http://localhost:5000/manage
2. Click "Choose File" to upload supported format documents
3. The system automatically processes and builds vector indexes

### Intelligent Query
1. Enter your query on the main page
2. Select time range (optional)
3. Click "Query" to start processing
4. Watch the real-time processing and results

### Query History
1. Visit the history page: http://localhost:5000/history
2. View all historical query records
3. Click on queries to view detailed results

## Configuration

### Model Configuration (`agent_rag_0609.py`)
```python
# Ollama configuration
self.base_url = "http://localhost:11434/v1"
self.embedding_model = "nomic-embed-text"  # Embedding model
self.llm_model = "llama2:7b"  # Language model
```

## Testing Guide

### Automated Testing
```bash
# Multi-IP user independence test
python test_multi_ip.py
```

### Manual Testing
1. Open multiple browser windows
2. Send concurrent query requests
3. Verify independent processing for each

### Performance Testing
```bash
# Using Apache Bench
ab -n 100 -c 10 http://localhost:5000/

# Using wrk
wrk -t12 -c400 -d30s http://localhost:5000/
```

## Troubleshooting

### Common Issues

#### 1. Ollama Connection Failure
```bash
# Check Ollama service status
ollama list
systemctl status ollama  # Linux
```

#### 2. Model Download Issues
```bash
# Manually download models
ollama pull <model-name>
```

#### 3. Insufficient Memory
- Adjust model size
- Increase system memory
- Optimize batch processing size

#### 4. Document Processing Failure
- Check document format
- Verify file permissions
- Review error logs

#### 5. Chinese Processing Issues
- Ensure opencc-python-reimplemented is installed
- Check document encoding format

### Log Viewing
The system outputs detailed logs to the console during runtime, including:
- Query request information
- Document processing status
- Task management status
- Error information

## Development Guide

### Project Structure
```
agentic_rag_web_0627/
├── app.py                 # Main application
├── agent_rag_0609.py      # RAG agent system
├── vector_db.py           # Vector database
├── start_server.py        # Startup script
├── test_multi_ip.py       # Test script
├── templates/             # HTML templates
│   ├── index.html        # Main page
│   ├── manage.html       # Management page
│   ├── history.html      # History page
│   └── history_detail.html # History details
├── static/               # Static resources
├── uploads/              # Uploaded documents
├── custom_json_rag_db/   # Vector database
└── history/              # Query history
```

### Extension Development

#### 1. Adding New Document Format Support
```python
# Add processing function in agent_rag_0609.py
def add_new_format_document(self, file_path: str):
    # Implement new format processing logic
    pass

# Update allowed file extensions
ALLOWED_EXTENSIONS.add('new_format')
```

#### 2. Custom AI Agents
```python
# Modify setup_agents() method
def setup_agents(self):
    self.custom_agent = autogen.AssistantAgent(
        name="CustomAgent",
        llm_config=self.llm_config,
        system_message="Custom agent system prompt"
    )
```

#### 3. Optimize Vector Search
```python
# Improve JSONVectorDB class
class JSONVectorDB:
    def advanced_search(self, query, filters=None):
        # Implement advanced search functionality
        pass
```

## Use Cases

- **Enterprise Knowledge Base**: Quick retrieval of internal company documents and knowledge
- **Technical Support**: Automated answers to technical questions and troubleshooting
- **Customer Service**: Knowledge backend for intelligent customer service bots
- **Research Assistant**: Intelligent retrieval of academic literature and research materials
- **Legal Consultation**: Quick query of legal provisions and case studies
- **Medical Information**: Retrieval of medical literature and clinical guidelines

## Contributing

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Create a Pull Request

## Acknowledgments

Thanks to the following open-source projects for their support:
- [AutoGen](https://github.com/microsoft/autogen)
- [Ollama](https://ollama.ai/)
- [LangChain](https://langchain.com/)
- [Flask](https://flask.palletsprojects.com/)

---

**Version**: 1.0.0  
**Last Updated**: June 2025  
**Maintainer**: CHAO YU CHEN 