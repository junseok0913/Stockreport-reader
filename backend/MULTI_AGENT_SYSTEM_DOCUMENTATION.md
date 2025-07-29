# Multi-Agent System Documentation
## ChatClovaX & LangGraph Based Stock Analysis Platform

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagrams](#architecture-diagrams)
3. [Agent System Structure](#agent-system-structure)
4. [Data Flow Analysis](#data-flow-analysis)
5. [API Integration](#api-integration)
6. [State Management](#state-management)
7. [Upload API System Analysis](#upload-api-system-analysis)
8. [Technology Stack](#technology-stack)
9. [Extension Points](#extension-points)

---

## System Overview

This is a comprehensive multi-agent system built with **ChatClovaX (HCX-005)** and **LangGraph** for analyzing stock market data and documents. The system combines PDF document processing with stock chart  analysis through a coordinated agent architecture.

### Core Components
- **Frontend**: React 19 + TypeScript + Tailwind CSS
- **Backend**: FastAPI + LangGraph + ChatClovaX
- **Multi-Agent System**: Supervisor + Worker Agent Pattern
- **Data Sources**: Kiwoom REST API, PDF Documents

---

## Architecture Diagrams

### 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "Frontend (React)"
        UI[Web Interface<br/>React + TypeScript]
        PDF[PDF Viewer<br/>react-pdf]
        Chat[Chat Interface<br/>ChatPane]
        State[State Management<br/>Zustand]
    end
    
    subgraph "Backend Services"
        Upload[Upload API<br/>:9000]
        Supervisor[Supervisor API<br/>:8000]
        
        subgraph "Multi-Agent System"
            SupervisorAgent[Supervisor Agent<br/>ChatClovaX HCX-005]
            StockAgent[Stock Price Agent<br/>ChatClovaX HCX-005]
        end
    end
    
    subgraph "External APIs"
        Kiwoom[Kiwoom REST API<br/>Historical Stock Chart Data]
        Clova[CLOVA Studio API<br/>ChatClovaX Models]
    end
    
    subgraph "Storage"
        PDFs[PDF Files<br/>uploads/]
        Processed[Processed Data<br/>processed/]
        StockData[Stock Chart Data<br/>data/]
    end
    
    UI --> Upload
    UI --> Supervisor
    PDF --> Upload
    Chat --> Supervisor
    
    Upload --> PDFs
    Upload --> Processed
    
    Supervisor --> SupervisorAgent
    SupervisorAgent --> StockAgent
    StockAgent --> Kiwoom
    StockAgent --> StockData
    
    SupervisorAgent --> Clova
    StockAgent --> Clova
    
    style SupervisorAgent fill:#e1f5fe
    style StockAgent fill:#f3e5f5
    style Clova fill:#fff3e0
```

### 2. Multi-Agent System Architecture

```mermaid
graph TB
    subgraph "LangGraph Multi-Agent System"
        subgraph "Supervisor Layer"
            Supervisor[Supervisor Agent<br/>ChatClovaX HCX-005<br/>🎯 Coordinator & Router]
        end
        
        subgraph "Worker Agents"
            StockAgent[Stock Price Agent<br/>ChatClovaX HCX-005<br/>📊 Stock Data Analysis]
            SearchAgent[✅ Search Agent<br/>ChatClovaX HCX-005<br/>🔍 Web Search & News Analysis<br/>Tavily + Naver News]
            DARTAgent[🔜 DART Agent<br/>ChatClovaX HCX-005<br/>📈 Corporate Filings Analysis]
        end
        
        subgraph "Shared Components"
            State[MessagesState<br/>📝 Shared State]
            Graph[LangGraph<br/>🔄 Workflow Engine]
        end
        
        subgraph "Tools & APIs"
            KiwoomTools[Kiwoom API Tools<br/>📡 Chart Data Retrieval]
            SearchTools[✅ Search & News Tools<br/>🌐 Tavily Web Search + 📰 Naver News + 🔗 Content Crawling]
            DARTTools[🔜 DART API Tools<br/>📊 Corporate Filings Retrieval]
        end
    end
    
    User[👤 User Query] --> Supervisor
    Supervisor -->|handoff| StockAgent
    Supervisor -->|handoff| SearchAgent
    Supervisor -.->|future| DARTAgent
    
    StockAgent --> KiwoomTools
    SearchAgent --> SearchTools
    DARTAgent -.-> DARTTools
    
    StockAgent --> State
    SearchAgent --> State
    DARTAgent -.-> State
    
    State --> Graph
    Graph --> Supervisor
    
    style Supervisor fill:#e3f2fd
    style StockAgent fill:#f3e5f5
    style SearchAgent fill:#e8f5e8
    style DARTAgent fill:#fff3e0,stroke-dasharray: 5 5
    style State fill:#fce4ec
```

### 3. Current Agent Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant API as Supervisor API
    participant Supervisor as Supervisor Agent
    participant StockAgent as Stock Price Agent
    participant Kiwoom as Kiwoom API
    participant DataMgr as Data Manager
    
    User->>API: POST /query {"query": "삼성전자 Q1 분석"}
    API->>Supervisor: invoke(initial_state)
    
    Note over Supervisor: ChatClovaX 분석<br/>질문 파싱 & 라우팅
    
    Supervisor->>Supervisor: 종목: 삼성전자(005930)<br/>기간: Q1 (20250101-20250331)<br/>목적: 분석
    
    Supervisor->>StockAgent: call_stock_price_agent(<br/>"삼성전자(005930) Q1 데이터 분석")
    
    Note over StockAgent: ChatClovaX + LangGraph<br/>ReAct Pattern
    
    StockAgent->>StockAgent: Thought: 일봉 데이터 필요
    StockAgent->>Kiwoom: get_day_chart(005930, 20250101, 20250331)
    Kiwoom-->>StockAgent: Raw Chart Data
    
    StockAgent->>DataMgr: process_chart_data(raw_data, "day")
    DataMgr-->>StockAgent: Processed DataFrame + Indicators
    
    StockAgent->>StockAgent: Final Answer: 기술적 분석 보고서
    StockAgent-->>Supervisor: 상세 분석 결과
    
    Supervisor->>Supervisor: 결과 종합 & 최종 답변 작성
    Supervisor-->>API: 최종 답변
    API-->>User: QueryResponse
```

---

## Agent System Structure

### 4. Supervisor Agent Internal Architecture

```mermaid
flowchart TD
    subgraph "Supervisor Agent (ChatClovaX HCX-005)"
        Prompt[System Prompt<br/>📋 Date-aware Instructions]
        LLM[ChatClovaX HCX-005<br/>🧠 Core Intelligence]
        Tools[Handoff Tools<br/>🔧 Worker Agent Connectors]
        
        subgraph "Tool Registry"
            StockTool[call_stock_price_agent<br/>📊 Stock Analysis Tool]
            NewsTool[🔜 call_news_agent<br/>📰 News Analysis Tool]
            DARTTool[🔜 call_dart_agent<br/>📈 Corporate Filings Analysis Tool]
        end
        
        subgraph "Manual Supervisor Implementation"
            ReactAgent[create_react_agent<br/>🔄 LangGraph ReAct Pattern]
            Workflow[StateGraph Workflow<br/>START → supervisor → END]
        end
    end
    
    UserQuery[User Query] --> Prompt
    Prompt --> LLM
    LLM --> Tools
    Tools --> StockTool
    Tools -.-> NewsTool
    Tools -.-> DARTTool
    
    ReactAgent --> LLM
    ReactAgent --> Tools
    Workflow --> ReactAgent
    
    style LLM fill:#e1f5fe
    style StockTool fill:#f3e5f5
    style NewsTool fill:#e8f5e8,stroke-dasharray: 5 5
    style DARTTool fill:#fff3e0,stroke-dasharray: 5 5
```

### 5. Stock Price Agent Internal Architecture

```mermaid
flowchart TD
    subgraph "Stock Price Agent (ChatClovaX HCX-005)"
        StockLLM[ChatClovaX HCX-005<br/>🧠 Stock Analysis Intelligence]
        StockPrompt[Stock Analysis Prompt<br/>📋 Date-formatted Instructions]
        
        subgraph "LangChain Tools"
            MinuteTool[get_minute_chart<br/>⏱️ 1-60분 데이터]
            DayTool[get_day_chart<br/>📅 일봉 데이터]
            WeekTool[get_week_chart<br/>📆 주봉 데이터]
            MonthTool[get_month_chart<br/>🗓️ 월봉 데이터]
            YearTool[get_year_chart<br/>📊 년봉 데이터]
        end
        
        subgraph "React Agent System"
            ReactEngine[create_react_agent<br/>🔄 Tool-calling Engine]
            ThoughtAction[Thought → Action → Observation<br/>🤔 ReAct Loop]
        end
        
        subgraph "Data Processing Layer"
            KiwoomAPI[Kiwoom API Client<br/>📡 Chart Data Access]
            DataManager[Data Manager<br/>📊 Processing & Indicators]
            TechIndicators[Technical Indicators<br/>📈 SMA, EMA, MACD, RSI, etc.]
        end
    end
    
    StockLLM --> StockPrompt
    StockLLM --> ReactEngine
    ReactEngine --> ThoughtAction
    ThoughtAction --> MinuteTool
    ThoughtAction --> DayTool
    ThoughtAction --> WeekTool
    ThoughtAction --> MonthTool
    ThoughtAction --> YearTool
    
    MinuteTool --> KiwoomAPI
    DayTool --> KiwoomAPI
    WeekTool --> KiwoomAPI
    MonthTool --> KiwoomAPI
    YearTool --> KiwoomAPI
    
    KiwoomAPI --> DataManager
    DataManager --> TechIndicators
    
    style StockLLM fill:#f3e5f5
    style ReactEngine fill:#e8f5e8
    style KiwoomAPI fill:#fff3e0
    style DataManager fill:#fce4ec
```

---

## Data Flow Analysis

### 6. Complete Data Flow Pipeline

```mermaid
flowchart LR
    subgraph "Input Layer"
        UserQuery[👤 User Query<br/>삼성전자 Q1 분석]
        PDFUpload[📄 PDF Upload<br/>Research Reports]
    end
    
    subgraph "Processing Layer"
        subgraph "Supervisor Processing"
            Parse[🔍 Query Parsing<br/>Extract: 종목, 기간, 목적]
            Route[🎯 Agent Routing<br/>Determine: Stock/News/DART]
            Coordinate[🤝 Result Coordination<br/>Integrate responses]
        end
        
        subgraph "Stock Agent Processing"
            Analyze[📊 Stock Analysis<br/>Period & Chart Selection]
            Fetch[📡 Data Fetching<br/>Kiwoom API Calls]
            Process[⚙️ Data Processing<br/>Technical Indicators]
            Report[📋 Analysis Report<br/>7-section format]
        end
        
        subgraph "PDF Processing"
            Extract[📄 Text Extraction<br/>PyPDF2]
            Chunk[🧩 Chunking<br/>BBox Creation]
            Store[💾 Storage<br/>processed/]
        end
    end
    
    subgraph "Output Layer"
        Response[📝 Final Response<br/>Structured Analysis]
        PDF_UI[🖥️ PDF Viewer<br/>Chunk Overlays]
        Chat_UI[💬 Chat Interface<br/>Streaming Responses]
    end
    
    UserQuery --> Parse
    Parse --> Route
    Route --> Analyze
    Analyze --> Fetch
    Fetch --> Process
    Process --> Report
    Report --> Coordinate
    Coordinate --> Response
    Response --> Chat_UI
    
    PDFUpload --> Extract
    Extract --> Chunk
    Chunk --> Store
    Store --> PDF_UI
    
    style Parse fill:#e3f2fd
    style Route fill:#e3f2fd
    style Analyze fill:#f3e5f5
    style Process fill:#f3e5f5
    style Extract fill:#e8f5e8
```

### 7. State Management Flow

```mermaid
stateDiagram-v2
    [*] --> UserInput
    
    state "User Input Processing" as UserInput {
        [*] --> QueryReceived
        QueryReceived --> StateCreation
        StateCreation --> InitialState
    }
    
    state "Supervisor Processing" as SupervisorProc {
        [*] --> QuestionAnalysis
        QuestionAnalysis --> AgentSelection
        AgentSelection --> ToolCalling
        ToolCalling --> ResultIntegration
    }
    
    state "Stock Agent Processing" as StockProc {
        [*] --> ChartSelection
        ChartSelection --> APICall
        APICall --> DataProcessing
        DataProcessing --> TechnicalAnalysis
        TechnicalAnalysis --> ReportGeneration
    }
    
    state "Final State" as FinalState {
        [*] --> ResponseExtraction
        ResponseExtraction --> UserResponse
    }
    
    UserInput --> SupervisorProc
    SupervisorProc --> StockProc : handoff_tool
    StockProc --> SupervisorProc : analysis_result
    SupervisorProc --> FinalState
    FinalState --> [*]
    
    note right of SupervisorProc
        MessagesState maintains:
        - messages: List[BaseMessage]
        - user_query: str
        - extracted_info: Dict
        - stock_data: Dict
        - metadata: Dict
    end note
```

---

## API Integration

### 8. API Architecture & Endpoints

```mermaid
graph TB
    subgraph "Frontend (Port 5173)"
        ReactApp[React Application]
        PDFViewer[PDF Viewer Component]
        ChatComponent[Chat Component]
    end
    
    subgraph "Backend APIs"
        subgraph "Upload Service (Port 9000)"
            UploadAPI[Upload API<br/>FastAPI]
            UploadEndpoints["Endpoints:<br/>POST /upload<br/>GET /chunks/{fileId}<br/>GET /file/{fileId}/download"]
        end
        
        subgraph "Query Service (Port 8000)"
            SupervisorAPI[Supervisor API<br/>FastAPI]
            QueryEndpoints["Endpoints:<br/>POST /query<br/>GET /health<br/>GET /status"]
        end
    end
    
    subgraph "External Services"
        KiwoomAPI[Kiwoom REST API<br/>Chart Data]
        ClovaAPI[CLOVA Studio API<br/>ChatClovaX Models]
        LangSmith[LangSmith<br/>Observability]
    end
    
    ReactApp -->|PDF Upload| UploadAPI
    PDFViewer -->|Get Chunks| UploadAPI
    ChatComponent -->|Query| SupervisorAPI
    
    UploadAPI --> UploadEndpoints
    SupervisorAPI --> QueryEndpoints
    
    SupervisorAPI --> ClovaAPI
    SupervisorAPI --> KiwoomAPI
    SupervisorAPI --> LangSmith
    
    style UploadAPI fill:#e8f5e8
    style SupervisorAPI fill:#e3f2fd
    style KiwoomAPI fill:#fff3e0
    style ClovaAPI fill:#fce4ec
```

### 9. Request/Response Flow

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant Upload as Upload API<br/>:9000
    participant Query as Query API<br/>:8000
    participant MAS as Multi-Agent<br/>System
    participant Kiwoom as Kiwoom API
    participant Clova as CLOVA Studio
    
    Note over FE,Clova: PDF Upload Flow
    FE->>Upload: POST /upload (PDF file)
    Upload->>Upload: Save to uploads/
    Upload->>Upload: Create processed_states.json
    Upload-->>FE: {fileId, pageCount}
    
    FE->>Upload: GET /chunks/{fileId}
    Upload-->>FE: [] (empty initially)
    
    Note over FE,Clova: Query Processing Flow
    FE->>Query: POST /query {"query": "stock analysis"}
    Query->>MAS: create_supervisor_graph().invoke()
    
    MAS->>Clova: Supervisor analysis request
    Clova-->>MAS: Task routing decision
    
    MAS->>MAS: call_stock_price_agent()
    MAS->>Clova: Stock analysis request
    Clova-->>MAS: Chart type decision
    
    MAS->>Kiwoom: get_day_chart() request
    Kiwoom-->>MAS: Raw chart data
    
    MAS->>MAS: process_chart_data()
    MAS->>Clova: Technical analysis request
    Clova-->>MAS: Analysis report
    
    MAS-->>Query: Final response
    Query-->>FE: Streaming response (SSE)
```

---

## Upload API System Analysis

### 10. Upload API Service Architecture

The Upload API (`backend/upload_api.py`) serves as a critical integration point between frontend PDF handling and backend RAG processing, operating on port 9000.

```mermaid
graph TB
    subgraph "Upload API Service (Port 9000)"
        UploadAPI[Upload API<br/>FastAPI Application]
        
        subgraph "Core Endpoints"
            Upload[POST /upload<br/>PDF Upload & Validation]
            Status[GET /status/{file_id}<br/>Processing Status]
            Download[GET /file/{file_id}/download<br/>PDF Streaming]
            Summaries[GET /summaries/{file_id}<br/>RAG Results]
            Health[GET /health<br/>System Health Check]
        end
        
        subgraph "Background Processing"
            BGTask[Background Tasks<br/>process_pdf_with_rag()]
            RAGCall[RAG Script Executor<br/>subprocess calls]
        end
        
        subgraph "Data Management"
            Metadata[File Metadata<br/>JSON storage]
            FileStorage[PDF Storage<br/>rag/data/pdf/]
        end
    end
    
    subgraph "RAG Integration"
        RAGScript[process_pdfs.py<br/>RAG Pipeline Script]
        RAGResults[RAG Results<br/>JSON output files]
        VectorDB[Vector Database<br/>ChromaDB storage]
    end
    
    subgraph "Frontend Integration"
        PDFDropzone[PdfDropzone Component<br/>File Upload UI]
        PDFViewer[PdfViewer Component<br/>Document Display]
        StatusPolling[Status Polling<br/>Processing Updates]
    end
    
    PDFDropzone -->|POST /upload| Upload
    PDFViewer -->|GET /file/download| Download
    StatusPolling -->|GET /status| Status
    
    Upload --> BGTask
    BGTask --> RAGCall
    RAGCall --> RAGScript
    RAGScript --> RAGResults
    RAGScript --> VectorDB
    
    Upload --> Metadata
    Upload --> FileStorage
    Status --> RAGResults
    
    style UploadAPI fill:#e8f5e8
    style BGTask fill:#fff3e0
    style RAGScript fill:#e1f5fe
    style PDFDropzone fill:#f3e5f5
```

### Key Features:
- **FastAPI-based Service**: Robust web framework with automatic OpenAPI documentation
- **RAG Pipeline Integration**: Automatic background processing with `rag/scripts/process_pdfs.py`
- **File Management**: UUID-based file identification with metadata persistence
- **Background Processing**: Non-blocking uploads with 10-minute processing timeout
- **Status Monitoring**: Real-time processing status with completion detection
- **CORS Support**: Full frontend integration with streaming file downloads
- **✅ Chunk-based Document Analysis**: Bounding box extraction from `processed_states.json`
- **✅ Multi-type Chunk Support**: Text, image, and table chunks with type-specific styling
- **✅ Interactive PDF Overlays**: Visual chunk selection with normalized coordinates
- **✅ Page-level Citation**: Bulk selection of all chunks on a page

### File Processing Flow:
1. **Upload**: PDF validation, unique ID generation, file storage to `backend/rag/data/pdf/`
2. **Metadata**: JSON metadata storage with page count and timestamps
3. **Background Task**: Queued RAG processing via subprocess execution
4. **RAG Processing**: Creation of `processed_states.json` with chunk data and bounding boxes
5. **Status Tracking**: Monitoring through JSON result file detection
6. **✅ Chunk Extraction**: Parse chunks from `processed_states.json` with coordinate normalization
7. **✅ Frontend Display**: Interactive PDF overlays with type-specific chunk visualization
8. **Result Access**: Structured summaries (text/image/table) via API endpoints

### Integration Points:
- **Directory Structure**: Unified with RAG system (`backend/rag/data/pdf/`)
- **Environment Variables**: Shared secrets from `backend/secrets/.env`
- **Multi-Agent Connection**: Processed documents available for agent consumption
- **Vector Database**: ChromaDB integration through RAG pipeline
- **✅ Chunk Data Source**: `backend/rag/data/vectordb/processed_states.json`
- **✅ Frontend Integration**: Real-time chunk polling via `/chunks/{file_id}` endpoint
- **✅ Interactive UI**: PDF viewer with visual chunk selection and page-level citation
- **✅ Query Integration**: Selected chunks passed to chat API for contextual responses

---

## Chunk-based Document Reference System

### Interactive PDF Analysis Flow

```mermaid
sequenceDiagram
    participant User as 사용자
    participant PDF as PDF Viewer
    participant API as Upload API
    participant RAG as RAG System
    participant FS as File System
    participant Chat as Chat System
    
    Note over User,Chat: Document Upload & Processing
    User->>API: POST /upload (PDF)
    API->>RAG: Background processing
    RAG->>FS: Create processed_states.json
    
    Note over User,Chat: Chunk Visualization
    PDF->>API: GET /chunks/{fileId} (every 5s)
    API->>FS: Load processed_states.json
    API->>API: Parse & normalize coordinates
    API-->>PDF: ChunkInfo[] (text/image/table)
    PDF->>PDF: Render interactive overlays
    
    Note over User,Chat: Interactive Selection
    User->>PDF: Click chunk overlay
    PDF->>PDF: Toggle chunk selection
    User->>PDF: Click "페이지 전체 인용"
    PDF->>PDF: Select all page chunks
    
    Note over User,Chat: Query with Context
    User->>Chat: Enter question
    Chat->>API: query + pinChunks[]
    API->>Chat: Context-aware response
    
    style PDF fill:#e8f5e8
    style API fill:#fff3e0
    style RAG fill:#e1f5fe
    style Chat fill:#f3e5f5
```

### Chunk Type Visualization

```mermaid
graph LR
    subgraph "PDF Page"
        TextChunk[📝 Text Chunk<br/>Blue Border<br/>Green when pinned]
        ImageChunk[🖼️ Image Chunk<br/>Purple Border<br/>Purple when pinned]
        TableChunk[📊 Table Chunk<br/>Orange Border<br/>Orange when pinned]
    end
    
    subgraph "Pinned Chips"
        TextChip[📝 텍스트 청크<br/>Green chip]
        ImageChip[🖼️ 이미지 청크<br/>Purple chip]
        TableChip[📊 테이블 청크<br/>Orange chip]
    end
    
    TextChunk -->|User clicks| TextChip
    ImageChunk -->|User clicks| ImageChip
    TableChunk -->|User clicks| TableChip
    
    style TextChunk fill:#dbeafe
    style ImageChunk fill:#ede9fe
    style TableChunk fill:#fed7aa
    style TextChip fill:#dcfce7
    style ImageChip fill:#f3e8ff
    style TableChip fill:#ffedd5
```

---

## Technology Stack

### 11. Technology Stack Overview

```mermaid
graph TB
    subgraph "Frontend Stack"
        React[React 19<br/>🔄 Component Framework]
        TS[TypeScript<br/>🔒 Type Safety]
        Tailwind[Tailwind CSS<br/>🎨 Styling]
        Vite[Vite<br/>⚡ Build Tool]
        Zustand[Zustand<br/>🗃️ State Management]
        ReactPDF[react-pdf<br/>📄 PDF Rendering]
        Vitest[Vitest<br/>🧪 Testing Framework]
    end
    
    subgraph "Backend Stack"
        FastAPI[FastAPI<br/>🚀 Web Framework]
        LangGraph[LangGraph<br/>🕸️ Agent Orchestration]
        LangChain[LangChain<br/>🔗 LLM Integration]
        ChatClovaX[ChatClovaX<br/>🧠 AI Model HCX-005]
        Pydantic[Pydantic<br/>📝 Data Validation]
        Uvicorn[Uvicorn<br/>🏃 ASGI Server]
    end
    
    subgraph "Data Processing"
        Pandas[pandas<br/>📊 Data Analysis]
        PandasTA[pandas-ta<br/>📈 Technical Analysis]
        PyPDF2[PyPDF2<br/>📄 PDF Processing]
        Requests[requests<br/>🌐 HTTP Client]
    end
    
    subgraph "External APIs"
        KiwoomAPI[Kiwoom REST API<br/>📡 Stock Chart Data]
        ClovaStudio[CLOVA Studio API<br/>🤖 AI Services]
        LangSmithAPI[LangSmith API<br/>📊 Observability]
    end
    
    React --> FastAPI
    LangGraph --> ChatClovaX
    FastAPI --> LangChain
    LangChain --> ClovaStudio
    FastAPI --> KiwoomAPI
    LangGraph --> LangSmithAPI
    
    style React fill:#61dafb,color:#000
    style FastAPI fill:#009688,color:#fff
    style LangGraph fill:#ff6b6b,color:#fff
    style ChatClovaX fill:#4caf50,color:#fff
```

---

## Extension Points

### 12. Implemented Search Agent Architecture

```mermaid
graph TB
    subgraph "Active System"
        CurrentSupervisor[Supervisor Agent<br/>✅ Active]
        CurrentStock[Stock Price Agent<br/>✅ Active]
        CurrentSearch[Search Agent<br/>✅ Active & Integrated]
    end
    
    subgraph "Search Agent Capabilities"
        SearchTools[Search & News Tools<br/>🌐 Comprehensive Search Suite]
        SearchPrompt[Search Agent Prompt<br/>📋 Autonomous reasoning instructions]
        
        subgraph "Search Agent Tools"
            TavilyTool[tavily_web_search<br/>🌐 Global Web Search]
            NaverRelevance[search_naver_news_by_relevance<br/>📰 Korean News Relevance]
            NaverDate[search_naver_news_by_date<br/>📅 Korean News Latest]
            ContentCrawl[Content Crawling<br/>🔗 Deep article analysis]
        end
    end
    
    subgraph "Integration Points"
        SupervisorTools[Supervisor Handoff Tools<br/>🔧 call_search_agent]
        SharedState[MessagesState<br/>📝 Shared between agents]
        CommonGraph[LangGraph Workflow<br/>🔄 Agent orchestration]
    end
    
    CurrentSupervisor --> SupervisorTools
    SupervisorTools --> CurrentSearch
    CurrentSearch --> SearchTools
    CurrentSearch --> SearchPrompt
    CurrentSearch --> TavilyTool
    CurrentSearch --> NaverRelevance
    CurrentSearch --> NaverDate
    CurrentSearch --> ContentCrawl
    
    CurrentStock --> SharedState
    CurrentSearch --> SharedState
    SharedState --> CommonGraph
    
    style CurrentSearch fill:#e8f5e8
    style SearchTools fill:#e8f5e8
    style SupervisorTools fill:#fff3e0
```

### 13. Future Multi-Agent Expansion

```mermaid
graph TB
    subgraph "Core Supervisor"
        Supervisor[Supervisor Agent<br/>🎯 Master Coordinator]
    end
    
    subgraph "Current Agents"
        StockAgent[Stock Price Agent<br/>📊 ✅ Active]
    end
    
    subgraph "Implemented Agents"
        SearchAgent[Search Agent<br/>🔍 ✅ Completed]
    end
    
    subgraph "Planned Agents"
        DARTAgent[DART Agent<br/>📈 🔮 Phase 2]
    end
    
    subgraph "Extension Pattern"
        HandoffTools[Handoff Tools Pattern<br/>🔧 call_agent_name]
        ToolRegistry[Tool Registry<br/>📋 Dynamic tool addition]
        StateManagement[Shared State Management<br/>📝 MessagesState extension]
    end
    
    Supervisor --> StockAgent
    Supervisor --> SearchAgent
    Supervisor -.-> DARTAgent
    
    HandoffTools --> Supervisor
    ToolRegistry --> HandoffTools
    StateManagement --> HandoffTools
    
    style StockAgent fill:#f3e5f5
    style SearchAgent fill:#e8f5e8
    style DARTAgent fill:#fff3e0,stroke-dasharray: 10 10

```

---

## Current Implementation Status

### ✅ Completed Components
- **Supervisor Agent**: ChatClovaX-based coordinator with handoff tools for both Stock and Search agents
- **Stock Price Agent**: Full stock analysis with Kiwoom API integration  
- **Search Agent**: Comprehensive search capabilities with Tavily web search and Naver News API
- **PDF Processing**: Upload, chunking, and viewer system
- **Frontend**: React-based UI with chat and PDF viewing
- **APIs**: Upload service (9000) and Query service (8000)
- **State Management**: LangGraph MessagesState and Zustand frontend state

### 🔜 Ready for Extension
- **DART Agent**: Framework ready for corporate filings analysis
- **Additional Tools**: Easy integration pattern established
- **Shared Components**: Reusable state and graph infrastructure
- **API Expansion**: Scalable FastAPI structure

### 🎯 Implementation Status for Search Agent (Evolved from News Agent)

#### ✅ **Production Implementation Completed**
1. **Architecture Evolution**: Refactored from NewsAgent to SearchAgent with expanded capabilities
2. **Comprehensive Tool Suite**: 
   - `tavily_web_search`: Global web search with Tavily API integration and content crawling
   - `search_naver_news_by_relevance`: Korean news search with relevance ranking
   - `search_naver_news_by_date`: Korean news search with latest-first sorting
   - Integrated content crawling for all search results
3. **Pure Autonomous Agent Logic**: True ReAct-style reasoning with NO hard-coded tool selection logic
4. **Supervisor Integration**: `call_search_agent` handoff tool fully integrated
5. **API Integration**: 
   - Tavily Search API for global web search
   - Naver News API for Korean news with enhanced sorting options
   - Content crawling capabilities for deep article analysis
6. **Enhanced Prompts & Tool Descriptions**: Autonomous reasoning guided by detailed system prompts and crystal-clear tool descriptions
7. **Package Structure**: Complete refactored module with expanded capabilities

#### 🚀 **READY FOR PRODUCTION**
- **Full Integration**: NewsAgent is now part of the multi-agent system
- **Supervisor Handoff**: Users can request news analysis through Supervisor
- **Test Coverage**: Test script available at `backend/agents/news_agent/test.py`
- **Documentation**: Complete architecture documentation and implementation guide

This documentation provides a comprehensive view of the current system with the fully implemented SearchAgent, showcasing a production-ready multi-agent architecture with autonomous search capabilities. 