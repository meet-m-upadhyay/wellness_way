# Detailed Flow Diagram: AI Refinement & History Logging

This diagram illustrates the end-to-end flow of a diet plan refinement request, highlighting how the system orchestrates the ML pipeline and automatically persists the interaction in the **Conversation History**.

```mermaid
flowchart TD
    %% Base Start
    Start(("User Refinement Request"))
    
    %% API Endpoints
    subgraph FastAPI ["FastAPI Flow (diet_plans_ml.py)"]
        API_Regen("regenerate_meal/day/plan_ml(plan_id, ...)")
        API_Parse("Parse indices & Verify ownership")
        API_Log["<b>Auto-Log to History:</b><br/>log_regeneration_to_history(db, user_id, scope)"]
    end

    %% Conversation History logic
    subgraph History ["History Component (models/chat.py)"]
        Chat_Lookup{"Find Active Chat?"}
        Chat_Create["Create New Chat Session<br/>'Diet Adjustments'"]
        Msg_User["Add User Message:<br/>'I want to regenerate...'"]
        Msg_Bot["Add Assistant Message:<br/>'Sure! Regenerating...'"]
    end

    %% ML Orchestrator Core 
    subgraph Orch ["ML Orchestrator (orchestrator.py)"]
        Orch_Exec("orchestrator.regenerate_meal/day/plan(...)")
        Orch_HCD["Fetch Active HealthContextDocument"]
        
        %% Step 1: Resampling
        Orch_Step1("STEP 1: Portfolio Resampling<br/>(Discovery Engine)")
        
        %% Step 2: Recalculation
        Orch_Step2("STEP 2: Mass Recalculation<br/>(Daily Assembler)")
        
        %% Step 3: LLM Integration
        Orch_Step3("STEP 3: Creative Regeneration<br/>(GenAI Service)")
    end

    %% Engines & Services
    subgraph Engines ["ML Engines"]
        Disc["Discovery Engine:<br/>Category Sampling<br/>(Protein, Veggie, Starch, Fat)"]
        Assem["Daily Assembler:<br/>Linear Math for precise<br/>ingredient grams"]
        LLM["GenAI Service:<br/>Llama 3.1 via Groq<br/>(Creative Recipes)"]
    end

    %% Final Save
    subgraph EndDB ["Database Sync"]
        DB_Update["Update DietPlan.content"]
        DB_Commit["db.commit() & Refresh"]
        Response["Return Updated DietPlanResponse"]
    end

    %% Flow Mapping 
    Start --> API_Regen
    API_Regen --> API_Parse
    API_Parse --> API_Log
    
    %% Logging Flow
    API_Log --> Chat_Lookup
    Chat_Lookup -->|No| Chat_Create
    Chat_Lookup -->|Yes| Msg_User
    Chat_Create --> Msg_User
    Msg_User --> Msg_Bot
    
    %% Parallel/Sequential ML Flow
    API_Parse --> Orch_Exec
    Orch_Exec --> Orch_HCD
    Orch_HCD --> Orch_Step1
    
    Orch_Step1 --> Disc
    Disc -->|New Portfolio| Orch_Step2
    
    Orch_Step2 --> Assem
    Assem -->|Raw Ingredient Masses| Orch_Step3
    
    Orch_Step3 --> LLM
    LLM -->|Creative JSON| DB_Update
    
    Msg_Bot --> DB_Update
    DB_Update --> DB_Commit
    DB_Commit --> Response

    %% Colors 
    classDef mainFlow fill:#dae8fc,stroke:#6c8ebf,color:#000
    classDef historyFlow fill:#fdf4ff,stroke:#a855f7,color:#000
    classDef mlInternal fill:#fff2cc,stroke:#d6b656,color:#000
    classDef llmFlow fill:#e1d5e7,stroke:#9673a6,color:#000

    class Start,API_Regen,DB_Update,Response mainFlow
    class API_Log,Chat_Lookup,Chat_Create,Msg_User,Msg_Bot historyFlow
    class Orch_Exec,Orch_Step1,Orch_Step2 mlInternal
    class Orch_Step3,LLM llmFlow
```

## Flow Highlights

### 1. Automatic "Shadow" Logging
Unlike standard generation, **Refinement** requests (regenerating a meal or day) trigger an automatic background logging task. The system looks for the user's most recent active chat session. If found, it appends the intent and the bot's acknowledgment; otherwise, it silently creates a new "Diet Adjustments" thread.

### 2. State-Aware ML Pipeline
The `ML Orchestrator` remains the single source of truth for diet logic. When a regeneration is triggered:
- **Scope Isolation**: Only the targeted meal or day is recalculated, preserving the rest of the plan.
- **Dynamic Resampling**: The Discovery Engine provides fresh ingredient candidates while maintaining the user's macronutrient constraints and recently updated preferences (like `cuisine`).

### 3. Contextual Retrieval (Architecture Ready)
While the current implementation focus is on **logging**, the architecture is now "plumbed" to allow the `GenAI Service` to query the `Messages Table` before generation. This will enable future features where the AI can say: *"Since you didn't like the salmon yesterday, I've replaced it with grilled cod."*
