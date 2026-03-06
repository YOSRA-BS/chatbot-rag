import os, re, time
from groq import Groq
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                PageBreak, HRFlowable)
from dotenv import load_dotenv  # <-- ajout

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration Groq API
API_KEY = os.environ.get("GROQ_API_KEY")
OUTPUT_FOLDER = "generated_pdfs"
MODEL         = "llama-3.3-70b-versatile"  # Modèle Llama 3 70B disponible sur Groq
MAX_TOKENS    = 4000
PAUSE_SECS    = 1

DOCUMENTS = [
  ("01_transformer_architecture.pdf", """
You are a senior ML engineer writing a comprehensive technical reference document.
Write a LONG, DETAILED document titled "The Transformer Architecture: A Deep Dive".

Cover ALL sections below with full paragraphs, formulas, and examples:
# The Transformer Architecture: A Deep Dive

## 1. Introduction and Historical Context
Explain RNN/LSTM limitations (sequential processing, vanishing gradients).
Describe the 2017 Vaswani et al. paper and its central claim.

## 2. Self-Attention Mechanism
- Query, Key, Value projections: shapes, purpose, intuition
- Scaled dot-product attention formula: Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) * V
- Why scale by sqrt(d_k)? What happens without it?
- Step-by-step example with small numbers

## 3. Multi-Head Attention
- Why multiple heads instead of one large head?
- Concatenation and output projection
- What different heads specialize in (syntactic, semantic, positional)

## 4. Positional Encoding
- Why Transformers need positional information
- Sinusoidal encoding formula and intuition per dimension
- Learned positional embeddings (BERT, GPT)
- RoPE (Rotary Position Embeddings) used in LLaMA
- ALiBi (Attention with Linear Biases) for length generalization

## 5. Encoder Architecture
- Full layer structure: self-attention + residual + LayerNorm + FFN + residual + LayerNorm
- Pre-LN vs Post-LN: training stability differences
- What each of the 12/24 layers learns progressively

## 6. Decoder Architecture
- Masked self-attention: why masking is critical, how -inf masking works
- Cross-attention over encoder output: Q from decoder, K/V from encoder
- Teacher forcing during training

## 7. Feed-Forward Networks
- Why d_ff = 4 * d_model (e.g., 2048 for d_model=512)
- ReLU vs GELU activation: differences in practice

## 8. Training Details
- Adam optimizer with warmup: lr = d_model^-0.5 * min(step^-0.5, step * warmup^-1.5)
- Label smoothing (epsilon=0.1): why it helps
- Dropout placement, gradient clipping

## 9. Major Variants
- BERT: encoder-only, Masked Language Modeling pre-training
- GPT family: decoder-only, autoregressive, scaling from GPT-1 to GPT-4
- T5: encoder-decoder, text-to-text framing
- Vision Transformer (ViT): patches as tokens

## 10. Scaling and Complexity
- Quadratic O(n^2*d) attention complexity: why it matters at 128K context
- Flash Attention: IO-aware kernel, avoids materializing attention matrix
- Sparse attention, sliding window (Mistral), GQA (Grouped Query Attention)

## 11. Practical Implementation Tips
- KV-cache: what it caches, how much memory it saves
- Mixed precision (BF16): stability advantages over FP16
- Gradient checkpointing: trade compute for memory
- Common bugs: forgetting causal mask, wrong positional encoding application

FORMATTING: Use # ## ### for headings, **bold** for terms, - for bullets,
triple backticks for formulas and code. Write long detailed paragraphs.
Do NOT write a preamble — start directly with # The Transformer Architecture.
"""),

  ("02_rag_complete_guide.pdf", """
You are a senior AI engineer writing a complete technical reference document.
Write a LONG, DETAILED document titled "RAG Systems: Complete Technical Guide".

# RAG Systems: Complete Technical Guide

## 1. What is RAG and Why It Exists
- The 3 core LLM failure modes: hallucination, knowledge cutoff, context limits
- The 2020 Lewis et al. (Facebook AI) paper: architecture and contributions
- When RAG is the right tool vs fine-tuning vs prompting

## 2. RAG System Architecture
Offline Indexing Pipeline (step by step with detail):
- Document collection, text extraction, cleaning
- Chunking strategy selection
- Embedding generation
- Vector database indexing

Online Query Pipeline (step by step with detail):
- Query encoding with same embedding model
- Similarity search (top-K retrieval)
- Optional reranking
- Prompt construction with context
- LLM generation with source grounding

## 3. Chunking Strategies (cover each with pros, cons, when to use)
- Fixed-size character chunking
- RecursiveCharacterTextSplitter: separator hierarchy, how it picks boundaries
- Sentence-based splitting
- Semantic chunking: embedding consecutive sentences, detecting topic shifts
- Parent-child chunking: small child for retrieval, large parent for context
- How to choose chunk_size (200-2000) and chunk_overlap (10-20% of size)

## 4. Embedding Models Comparison
- all-MiniLM-L6-v2: 22MB, 384-dim, best for local/fast
- BGE-M3: multilingual, multi-vector (dense + sparse + colbert)
- text-embedding-3-large: OpenAI, 3072-dim, best quality API
- E5-large-v2: requires query:/passage: prefixes
- Critical rule: same model at index time AND query time

## 5. Vector Databases Deep Comparison
For each: FAISS, ChromaDB, Qdrant, Weaviate, Pinecone
- Architecture, storage, ANN algorithm used
- Metadata filtering capabilities
- Local vs cloud, scaling limits
- When to choose each

## 6. Retrieval Strategies
- Dense vector search: cosine similarity intuition and formula
- Sparse BM25: term frequency, inverse document frequency, why keywords still matter
- Hybrid search: Reciprocal Rank Fusion formula: RRF(d) = sum(1/(k + rank_i(d)))
- Reranking with cross-encoders: why they are more accurate than bi-encoders

## 7. Prompt Engineering for RAG
- Basic context injection template
- Strict vs. hybrid mode (documents-only vs documents + own knowledge)
- Source citation instructions
- Chain-of-thought RAG for complex questions
- Preventing hallucinations: instruction design

## 8. Advanced RAG Techniques
- HyDE: generate a hypothetical answer, embed it, retrieve similar real docs
- Multi-query retrieval: generate 3-5 query variants, union the results
- Contextual compression: LLM extracts only relevant sentences from each chunk
- Self-RAG: model decides when retrieval is needed

## 9. Evaluation with RAGAS
- Faithfulness: answer grounded in retrieved context?
- Answer Relevancy: answer addresses the question?
- Context Precision: retrieved chunks actually useful?
- Context Recall: all necessary info retrieved?
- How to run RAGAS automatically (LLM-as-judge)

## 10. Common Failure Modes and Fixes
- Chatbot says "I don't know" on answerable questions → fix retrieval
- Hallucination despite context → fix prompt, lower temperature
- Wrong chunks retrieved → improve chunking, try hybrid search
- Slow responses → caching, smaller reranker, HNSW index

## 11. RAG vs Fine-Tuning Decision Table
Create a detailed comparison table covering: knowledge updates, cost, latency,
source citation, factual grounding, style control, domain terminology.

FORMATTING: # ## ### headings, **bold** terms, - bullets, ``` for code/formulas.
Long paragraphs. Start directly with # RAG Systems — no preamble.
"""),

  ("03_llm_finetuning_guide.pdf", """
You are a senior ML researcher writing a masterclass-level reference document.
Write a LONG, DETAILED document titled "LLM Fine-Tuning: Practitioner's Complete Guide".

# LLM Fine-Tuning: Practitioner's Complete Guide

## 1. When to Fine-Tune
- Prompt engineering: when it is enough (style, format, few examples)
- RAG: when new knowledge is the goal
- Fine-tuning: the 5 clear winning cases (behavior, jargon, consistent format,
  latency reduction, smaller+specialized model)
- The cost of fine-tuning vs. alternatives

## 2. Supervised Fine-Tuning (SFT)
- Dataset format: instruction/input/output JSON structure
- Chat template formats: Llama-3, Mistral, Phi-3 — why they differ
- Cross-entropy loss on completion tokens only (not on prompt)
- Training loop details

## 3. RLHF (Reinforcement Learning from Human Feedback)
- Phase 1 SFT: high-quality demonstration data
- Phase 2 Reward Model: preference pairs, Bradley-Terry model, sigmoid output
- Phase 3 PPO: policy gradient, KL penalty to prevent reward hacking
- Why RLHF is expensive and complex

## 4. DPO (Direct Preference Optimization)
- How DPO eliminates the reward model
- DPO loss formula: -log(sigmoid(beta*(log_pi_theta(y_w|x) - log_pi_theta(y_l|x) - log_pi_ref(y_w|x) + log_pi_ref(y_l|x))))
- DPO dataset format: (prompt, chosen, rejected) triples
- SimPO, ORPO: simplifications of DPO

## 5. LoRA In Depth
- Core idea: W + delta_W where delta_W = B*A, rank r << d
- Why low-rank works: gradient updates are empirically low-rank
- Hyperparameters: r (4-64), lora_alpha (=2r), target_modules, lora_dropout
- Which modules to target: q_proj, k_proj, v_proj, o_proj, gate, up, down
- Parameter count: full FT 7B = 7B params; LoRA r=16 = ~20M params (0.3%)

## 6. QLoRA
- 4-bit NormalFloat (NF4): why it is better than int4 for weights
- Double quantization: quantize the quantization constants
- Paged optimizers: unified memory for gradient checkpointing spikes
- GPU memory table: 7B, 13B, 70B models with full FT vs LoRA vs QLoRA

## 7. Dataset Preparation
- Quality over quantity: 1000 good examples > 100K bad ones
- Deduplication: exact and near-duplicate removal
- Length distribution: filter too-short and too-long responses
- Task balance: avoid 80% of same task type
- Data augmentation: instruction rewriting, teacher model generation

## 8. Training Hyperparameters Guide
Write a complete table:
| Hyperparameter | LoRA Range | Full FT Range | Notes |
Include: learning rate, batch size, gradient accumulation, epochs,
warmup ratio, LR scheduler, weight decay, gradient clipping, LoRA r, LoRA alpha

## 9. Evaluation
- Training vs validation loss curves: what to look for
- Perplexity: formula and interpretation
- Task-specific: ROUGE-L for summarization, pass@k for code, win rate for chat
- Red-teaming: adversarial evaluation before deployment

## 10. Serving the Fine-Tuned Model
Step-by-step for each method:
- Merge LoRA into base model: W_merged = W + B*A*(alpha/r)
- Convert to GGUF for Ollama: llama.cpp convert script commands
- Create Modelfile for Ollama and register model
- vLLM for high-throughput serving: launch command, batch size config

FORMATTING: # ## ### headings, **bold** for terms, - bullets, ``` for code/formulas.
Tables where specified. Long paragraphs. Start directly with # LLM Fine-Tuning.
"""),

  ("04_langchain_developer_reference.pdf", """
You are a senior software engineer writing a complete developer reference.
Write a LONG, DETAILED document titled "LangChain: Complete Developer Reference".

# LangChain: Complete Developer Reference

## 1. Ecosystem Overview
- Package structure: langchain-core, langchain, langchain-community, langchain-[provider]
- The Runnable interface: invoke(), batch(), stream(), astream()
- LCEL (LangChain Expression Language): the pipe operator |
- Why LCEL: automatic streaming, async, parallel, LangSmith tracing

## 2. Prompt Templates
With full code examples for each:
- PromptTemplate: variables, partial(), from_template()
- ChatPromptTemplate: system/human/ai messages, from_messages()
- MessagesPlaceholder: injecting conversation history
- FewShotPromptTemplate: examples, example_prompt, prefix/suffix

## 3. LLM Integrations
With code examples and key parameters:
- ChatOllama: model, temperature, keep_alive, num_ctx
- ChatOpenAI: model, max_tokens, streaming, timeout
- ChatAnthropic: model, max_tokens, system prompt
- HuggingFacePipeline: model_id, task, pipeline_kwargs
- AIMessage structure: content, response_metadata, usage_metadata

## 4. Document Loaders
With code examples:
- PyPDFLoader: page-by-page, metadata.page
- Docx2txtLoader, TextLoader
- WebBaseLoader: BeautifulSoup parsing
- CSVLoader, JSONLoader (jq path)
- Document object anatomy: page_content, metadata dict

## 5. Text Splitters
- RecursiveCharacterTextSplitter: separator hierarchy ["\n\n","\n",". "," ",""]
- TokenTextSplitter: when to prefer tokens over characters
- Choosing chunk_size and chunk_overlap in practice
- split_documents() vs split_text() difference

## 6. Vector Stores in LangChain
With full code examples:
- FAISS: from_documents(), save_local(), load_local(allow_dangerous=True)
- ChromaDB: PersistentClient, collection, metadata filtering
- as_retriever(): search_type (similarity, mmr, threshold), search_kwargs

## 7. Memory Systems
With code examples:
- ConversationBufferMemory: memory_key, return_messages, output_key
- ConversationSummaryMemory: llm parameter, how summarization triggers
- ConversationBufferWindowMemory: k parameter
- How memory plugs into ConversationalRetrievalChain

## 8. ConversationalRetrievalChain Deep Dive
- from_llm() all parameters explained: llm, retriever, memory, combine_docs_chain_kwargs
- The condense_question step: how follow-ups are handled
- return_source_documents: what it returns
- Custom prompt via combine_docs_chain_kwargs={"prompt": prompt}
- result keys: "answer", "source_documents", "chat_history"

## 9. Agents and Tools
With full code examples:
- @tool decorator: docstring as tool description for the LLM
- create_react_agent() + AgentExecutor
- ReAct loop: Thought → Action → Observation → ...
- Built-in tools: DuckDuckGoSearchRun, WikipediaQueryRun, PythonREPLTool
- max_iterations and early_stopping_method

## 10. LangGraph Basics
- StateGraph, TypedDict state, add_node, add_edge, add_conditional_edges
- Entry point, END node
- Building a RAG retry loop: retrieve → generate → grade → retry if low quality
- Compiling and invoking a graph

## 11. LangSmith
- Environment variables for automatic tracing
- What gets logged: every invoke, retrieval, LLM call, tool call
- Reading a trace: latency breakdown, token counts
- Creating evaluation datasets and running evals

## 12. Production Patterns
- Async with ainvoke() for FastAPI integration
- InMemoryCache and RedisCache for LLM call caching
- Streaming to frontend with stream()
- Request-level logging from day one

FORMATTING: # ## ### headings, **bold** for class/function names,
```python code blocks for all examples. Start directly with # LangChain.
"""),

  ("05_genai_business_guide.pdf", """
You are a strategy consultant and AI expert writing a comprehensive business guide.
Write a LONG, DETAILED document titled "Generative AI in Business: Applications, ROI, and Implementation".

# Generative AI in Business: Applications, ROI, and Implementation

## 1. The Business Case
- McKinsey estimate: 2.6-4.4 trillion USD annual value across use cases
- Why this differs from previous automation waves (open-ended vs. rule-based)
- The three value sources: productivity, quality, revenue

## 2. Software Development
- Code generation ROI: Peng et al. MIT study (55% faster task completion)
- GitHub Copilot: 46% of new code AI-generated at scale
- Google internal: 25% of new code AI-generated (Q2 2024)
- Beyond autocomplete: architecture review, documentation, security scanning,
  legacy code modernization (COBOL→Python), IaC generation
- Metrics to track: velocity, defect rate, time-to-ship

## 3. Customer Service
- Tier-1 deflection rates: 60-80% benchmark for well-deployed LLM chatbots
- Agent assistance: handle time reduction, CSAT improvement
- 100% QA coverage vs traditional 2-5% manual sampling
- Real examples: Bank of America Erica (1.5B interactions/year),
  Salesforce Einstein (30% handle time reduction)
- Implementation sequence: start with agent assist, then chatbot

## 4. Healthcare and Life Sciences
- Clinical documentation: physicians spend 34-55% of time on admin
- AI scribes: Nuance DAX at Mayo Clinic (3 min/patient saved, 50% doc time reduction)
- Drug discovery: AlphaFold 2/3 protein structure prediction breakthrough
- Insilico Medicine: AI-designed drug to Phase 2 in 4 years vs typical 10-15
- Medical imaging: FDA-cleared tools, 20-40% radiologist throughput increase

## 5. Financial Services
- JPMorgan COIN: 360,000 lawyer-hours of contract review automated
- JPMorgan LOXM: equity trade execution learned from billions of scenarios
- Morgan Stanley: GPT-4 assistant for 16,000 advisors, 60% less research time
- Fraud detection: synthetic fraud scenario generation, novel pattern detection
- BloombergGPT: 50B parameter financial domain model

## 6. Legal Industry
- Contract review accuracy: AI 90%+ vs junior associates 85% on standard clauses
- Time: 4-6 hours per contract → 60 seconds with AI
- Harvey, Ironclad, ContractPodAi: feature comparison
- Legal research: Westlaw AI, LexisNexis natural language queries
- M&A due diligence: entire data rooms processed in hours

## 7. Education and Training
- Khan Academy Khanmigo: 47% faster concept mastery in pilots
- Socratic method: why guiding questions outperform direct answers
- Corporate training: 6-week instructional design → 1 week with AI assistance
- Duolingo AI features: roleplay, grammar explanation
- Personalization at scale: adaptive learning paths

## 8. Manufacturing and Supply Chain
- Predictive maintenance: LLM-powered anomaly explanation (not just detection)
- Quality control: vision AI + LLM root cause analysis
- Demand forecasting with unstructured data (news, social, weather)
- Technical documentation: maintenance manual generation from CAD + sensor data

## 9. Implementation Framework
Phase 1 - Opportunity Assessment (4-6 weeks):
- Scoring matrix: frequency × volume × quality-issues × automation-readiness
- Prioritization criteria: high volume, repetitive, measurable, low error cost

Phase 2 - Pilot Design (6-8 weeks):
- Control group methodology
- Success metrics defined BEFORE starting (not after)
- User involvement in design: why resistance kills AI projects

Phase 3 - Evaluation (4 weeks):
- Productivity measurement: time-per-task with/without AI
- Quality measurement: error rate, consistency, user satisfaction
- ROI calculation: (time_saved * hourly_rate + error_cost_reduction) / (tool_cost + implementation)

Phase 4 - Scaled Deployment:
- Prompt version control
- Monitoring: latency, accuracy drift, user adoption rate
- Feedback loops for continuous improvement

## 10. Risk Management
- Hallucination severity matrix by domain (low: content generation; high: medical/legal)
- Data privacy: opt-out from training data, local models for sensitive data
- Bias audits: demographic parity, counterfactual fairness testing
- IP ownership: current legal landscape, disclosure requirements
- Why human-in-the-loop is non-negotiable for high-stakes decisions

## 11. Future Outlook (Next 3-5 Years)
- Agentic AI: autonomous multi-step task execution without human approval
- Multimodal enterprise workflows: video, audio, images + text
- Inference cost curves: 10x cost reduction every 12-18 months historically
- Competitive dynamics: the window for differentiation via AI is narrowing

FORMATTING: # ## ### headings, **bold** for stats and company names,
- bullets, numbered steps. Include specific numbers throughout.
Start directly with # Generative AI in Business — no preamble.
"""),
]
def get_styles():
    base = getSampleStyleSheet()
    return {
        "title":    ParagraphStyle("T",  parent=base["Title"],   fontSize=22, textColor=colors.HexColor("#1B2A4A"), spaceAfter=14, alignment=TA_CENTER, fontName="Helvetica-Bold"),
        "subtitle": ParagraphStyle("ST", parent=base["Normal"],  fontSize=11, textColor=colors.HexColor("#2E75B6"), spaceAfter=28, alignment=TA_CENTER, fontName="Helvetica-Oblique"),
        "h1":       ParagraphStyle("H1", parent=base["Heading1"],fontSize=15, textColor=colors.HexColor("#1B2A4A"), spaceBefore=22, spaceAfter=9,  fontName="Helvetica-Bold"),
        "h2":       ParagraphStyle("H2", parent=base["Heading2"],fontSize=12, textColor=colors.HexColor("#2E75B6"), spaceBefore=15, spaceAfter=7,  fontName="Helvetica-Bold"),
        "h3":       ParagraphStyle("H3", parent=base["Heading3"],fontSize=10.5,textColor=colors.HexColor("#1F5C8B"),spaceBefore=11, spaceAfter=5,  fontName="Helvetica-Bold"),
        "body":     ParagraphStyle("B",  parent=base["Normal"],  fontSize=10, textColor=colors.HexColor("#333333"), spaceAfter=7,  leading=15, alignment=TA_JUSTIFY, fontName="Helvetica"),
        "bullet":   ParagraphStyle("BU", parent=base["Normal"],  fontSize=10, textColor=colors.HexColor("#333333"), spaceAfter=5,  leading=14, leftIndent=18, fontName="Helvetica"),
        "code":     ParagraphStyle("C",  parent=base["Code"],    fontSize=8.5,textColor=colors.HexColor("#1A1A2E"), backColor=colors.HexColor("#F4F6F9"), spaceAfter=9, spaceBefore=5, leftIndent=10, rightIndent=10, leading=13, fontName="Courier"),
        "note":     ParagraphStyle("N",  parent=base["Normal"],  fontSize=9.5,textColor=colors.HexColor("#444444"), backColor=colors.HexColor("#EBF3FB"), spaceAfter=9, spaceBefore=5, leftIndent=10, rightIndent=10, leading=14, fontName="Helvetica-Oblique"),
    }

def _esc(t):
    t = t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", t)
    t = re.sub(r"`(.+?)`", r'<font name="Courier" color="#C7254E">\1</font>', t)
    return t

def parse_md(text, S):
    out, lines = [], text.split("\n")
    i, in_code, cbuf = 0, False, []
    while i < len(lines):
        ln = lines[i]; s = ln.strip()
        if s.startswith("```"):
            if not in_code: in_code, cbuf = True, []
            else:
                in_code = False
                ct = "\n".join(cbuf).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                out.append(Paragraph(ct.replace("\n","<br/>"), S["code"]))
            i+=1; continue
        if in_code: cbuf.append(ln); i+=1; continue
        if not s:   out.append(Spacer(1,5)); i+=1; continue
        if s.startswith("### "):
            out.append(Paragraph(_esc(s[4:]), S["h3"]))
        elif s.startswith("## "):
            out.append(HRFlowable(width="100%",thickness=0.4,color=colors.HexColor("#DDDDDD"),spaceAfter=3))
            out.append(Paragraph(_esc(s[3:]), S["h2"]))
        elif s.startswith("# "):
            out.append(Spacer(1,10))
            out.append(HRFlowable(width="100%",thickness=2,color=colors.HexColor("#2E75B6"),spaceAfter=5))
            out.append(Paragraph(_esc(s[2:]), S["h1"]))
        elif s.startswith(("- ","* ","• ")):
            out.append(Paragraph(f"&bull; &nbsp; {_esc(s[2:])}", S["bullet"]))
        elif re.match(r"^\d+\.\s",s) and len(s)<300:
            out.append(Paragraph(_esc(s), S["bullet"]))
        elif s.lower().startswith(("note:","tip:","important:","warning:")):
            out.append(Paragraph(_esc(s), S["note"]))
        else:
            out.append(Paragraph(_esc(s), S["body"]))
        i+=1
    return out

def build_pdf(path, title, content):
    S = get_styles()
    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            leftMargin=2.5*cm, rightMargin=2.5*cm,
                            topMargin=2.5*cm,  bottomMargin=2.5*cm, title=title)
    story = [
        Spacer(1,1.5*cm),
        Paragraph(title, S["title"]),
        Paragraph("Technical Reference — Generated for RAG Chatbot", S["subtitle"]),
        HRFlowable(width="70%",thickness=2,color=colors.HexColor("#2E75B6"),hAlign="CENTER"),
        Spacer(1,0.8*cm), PageBreak(),
    ]
    story.extend(parse_md(content, S))
    doc.build(story)


# =============================================================================
# MAIN
# =============================================================================
def main():
    if not API_KEY:
        print("\n❌ ERROR: No Groq API key set!")
        print("\n  Quick setup:")
        print("  1. Go to https://console.groq.com")
        print("  2. Create a FREE account")
        print("  3. Go to API Keys and create a key")
        print("  4. Add it to your .env file as:")
        print("     GROQ_API_KEY=gsk_...")
        return

    client = Groq(api_key=API_KEY)

    out_dir = Path(OUTPUT_FOLDER)
    out_dir.mkdir(exist_ok=True)

    print(f"\nGenerating {len(DOCUMENTS)} PDFs  |  model: {MODEL}  |  output: {out_dir}/")
    print("=" * 60)

    for idx, (filename, prompt) in enumerate(DOCUMENTS, 1):
        title = re.sub(r"^\d+_","", filename.replace(".pdf","")).replace("_"," ").title()
        print(f"\n[{idx}/{len(DOCUMENTS)}] {filename}")
        print(f"  Calling Groq API ({MODEL}) ...", end=" ", flush=True)

        try:
            msg = client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{"role":"user","content": prompt}],
                temperature=0.7
            )
            content = msg.choices[0].message.content
            
            print(f"OK  ({len(content):,} chars, ~{len(content.split()):,} words)")

            print(f"  Building PDF   ...", end=" ", flush=True)
            build_pdf(out_dir / filename, title, content)
            kb = (out_dir / filename).stat().st_size // 1024
            print(f"OK  ({kb} KB)")

        except Exception as e:
            print(f"\n  ERROR: {e}")
            continue

        if idx < len(DOCUMENTS) and PAUSE_SECS > 0:
            print(f"  Pausing {PAUSE_SECS}s ...", end="\r")
            time.sleep(PAUSE_SECS)

    print("\n" + "=" * 60)
    print(f"Done!  PDFs saved to: {out_dir.resolve()}/")
    print("\nNext steps:")
    print(f"  cp {OUTPUT_FOLDER}/*.pdf path/to/rag_chatbot/documents/")
    print("  python ingest.py")
    print("  streamlit run chatbot.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
