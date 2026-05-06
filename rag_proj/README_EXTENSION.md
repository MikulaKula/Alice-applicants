# RAG Experiments Extension

This extension adds experiments required for the chatbot coursework:

- preprocessing experiment
- chunking experiment
- reranker experiment
- generation evaluation template
- AgenticRAG proof-of-concept

## Commands

Build the main Chroma index:

```bash
python load_documents_chroma.py
```

Evaluate baseline retrieval:

```bash
python evaluate_chroma.py
```

Run preprocessing experiment:

```bash
python experiments/preprocessing_experiment.py
```

Run chunking experiment:

```bash
python experiments/chunking_experiment.py
```

Run reranker experiment:

```bash
python experiments/reranker_experiment.py
```

Prepare generation manual evaluation:

```bash
python experiments/generation_experiment.py
```

Run AgenticRAG demo:

```bash
python experiments/agentic_rag_demo.py
```

## Notes

Generation evaluation is semi-manual. The script creates `results/generation_eval_template.json`; after that, manually fill scores:
- factual correctness
- completeness
- groundedness
- hallucination
