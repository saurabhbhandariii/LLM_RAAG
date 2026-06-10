# 📋 File Reference Guide - Privacy-First Multi-PDF RAG

## 🎯 Quick Navigation

### 🚀 Getting Started
- **Start here**: [`SETUP_PRIVACY.md`](SETUP_PRIVACY.md) - 5-minute quick start guide
- **Complete guide**: [`PRIVACY.md`](PRIVACY.md) - Full privacy architecture documentation
- **What changed**: [`IMPROVEMENT_SUMMARY.md`](IMPROVEMENT_SUMMARY.md) - Detailed changelog
- **Verify**: [`verify_implementation.sh`](verify_implementation.sh) - Implementation verification

### ⚙️ Core Application
- **Main app**: [`app.py`](app.py) - Streamlit application with privacy integration
- **Guards**: [`guard_utils.py`](guard_utils.py) - LLM Guard + Llama Guard implementation
- **Config**: [`privacy_config.py`](privacy_config.py) - Centralized privacy configuration
- **Setup**: [`.env.example`](.env.example) - Configuration template

### 📊 Output & Formatting
- **Privacy outputs**: [`utils/privacy_output_formatter.py`](utils/privacy_output_formatter.py) - Safe export generation
- **Legacy fallback**: [`utils/artifact_generator.py`](utils/artifact_generator.py) - Original formatters
- **Detection**: [`utils/output_detection.py`](utils/output_detection.py) - Output type detection

### 📚 Documentation
- **README**: [`README.md`](README.md) - Project overview (updated with privacy focus)
- **Privacy guide**: [`PRIVACY.md`](PRIVACY.md) - 500+ lines of privacy documentation
- **Setup guide**: [`SETUP_PRIVACY.md`](SETUP_PRIVACY.md) - Quick start guide
- **What changed**: [`IMPROVEMENT_SUMMARY.md`](IMPROVEMENT_SUMMARY.md) - Complete improvements list
- **Completion**: [`COMPLETION_REPORT.md`](COMPLETION_REPORT.md) - Implementation status
- **This file**: [`FILE_REFERENCE.md`](FILE_REFERENCE.md) - You are here!

### 🛡️ Security & Guards
- **Guard base**: [`guards/base.py`](guards/base.py) - Base guard class
- **Guardrails layer**: [`guards/guardrails_layer.py`](guards/guardrails_layer.py) - Guardrails framework
- **LLM Guard layer**: [`guards/llm_guard_layer.py`](guards/llm_guard_layer.py) - LLM Guard wrapper

### 📦 Dependencies
- **Requirements**: [`requirements.txt`](requirements.txt) - Python dependencies (updated)
- **Project config**: [`pyproject.toml`](pyproject.toml) - Poetry configuration

### 📝 Logs & Data
- **Violations**: [`violations.jsonl`](violations.jsonl) - Audit trail (auto-generated)

---

## 📖 Detailed File Descriptions

### [`app.py`](app.py)
**Purpose**: Main Streamlit application  
**What's New**:
- Privacy-aware imports
- Enhanced guard integration
- Privacy UI elements (privacy level badge, security info)
- Privacy pipeline for prompts/responses
- Better error handling

**Key Features**:
- PDF upload with PII redaction
- Hybrid RAG retrieval (BM25 + FAISS)
- Multi-format output export (PDF, Excel, Word, PowerPoint, Charts)
- Privacy guard checks on all inputs/outputs
- Violation logging

**Configuration**: 
- Set `PRIVACY_LEVEL` in `.env` or environment
- Customize Groq models in code
- Adjust retrieval depth with sidebar slider

---

### [`guard_utils.py`](guard_utils.py) ⭐ NEW
**Purpose**: LLM Guard + Llama Guard implementation  
**Size**: 450+ lines (was 70 lines)  

**Key Classes**:
- `PrivacySanitizer`: PII detection and redaction
- `LLMGuardScanner`: All LLM Guard scanners
- `LlamaGuardScanner`: Meta's Llama Guard integration
- `ViolationCategory`: Enum for violation types

**Main Functions**:
- `check_prompt()`: Checks input with all guards
- `check_response()`: Checks output with all guards
- `log_violation()`: Logs violations with hashing

**Scanner Capabilities**:
- **Input**: Prompt injection, toxicity, secrets, anonymization, language, code
- **Output**: Toxicity, sensitive info, factuality, bias

---

### [`privacy_config.py`](privacy_config.py) ⭐ NEW
**Purpose**: Centralized privacy configuration  
**Size**: 270 lines

**Main Sections**:
- `LLM_GUARD_CONFIG`: Configure all input/output scanners
- `LLAMA_GUARD_CONFIG`: Llama Guard settings
- `PII_PATTERNS`: 10+ PII detection patterns
- `REDACTION_RULES`: How to redact each PII type
- `VIOLATION_CONFIG`: Logging settings
- `PRIVACY_LEVELS`: 3 predefined privacy profiles
- `API_CONFIG`: Groq and Ollama settings

**Functions**:
- `get_privacy_level()`: Get current privacy level
- `get_privacy_config()`: Get config for current level
- `is_strict_mode()`: Check if running in STRICT mode

---

### [`utils/privacy_output_formatter.py`](utils/privacy_output_formatter.py) ⭐ NEW
**Purpose**: Privacy-aware output generation  
**Size**: 400+ lines

**Main Class**: `PrivacyAwareOutputFormatter`

**Supported Formats**:
- `generate_table()`: Sanitized pandas DataFrame
- `generate_excel()`: With metadata sheet
- `generate_chart()`: Line, bar, pie, histogram
- `generate_docx()`: Word document
- `generate_pdf()`: Multi-page PDF
- `generate_pptx()`: PowerPoint slides
- `generate_graph()`: Network visualization

**Features**:
- Automatic PII redaction on all content
- Metadata generation with timestamps
- Professional styling
- Column auto-formatting
- Multi-page support

---

### [`PRIVACY.md`](PRIVACY.md) 📚 COMPREHENSIVE GUIDE
**Purpose**: Complete privacy architecture documentation  
**Size**: 500+ lines

**Sections**:
1. Guard Layers (input/output)
2. Privacy Levels (STRICT/STANDARD/BASIC)
3. PII Detection Patterns (18 types)
4. Violation Logging
5. Privacy Flow Diagram
6. Configuration Guide
7. Monitoring & Compliance
8. Advanced Customization
9. Performance Tuning
10. Troubleshooting

**Use This When**:
- Understanding guard architecture
- Configuring privacy settings
- Monitoring for violations
- Setting up compliance
- Tuning performance

---

### [`SETUP_PRIVACY.md`](SETUP_PRIVACY.md) 🚀 QUICK START
**Purpose**: 5-minute quick start guide  
**Size**: 300+ lines

**Main Sections**:
- Installation (5 steps)
- Privacy level selection guide
- Feature comparison table
- Testing scenarios
- Troubleshooting
- Best practices
- Resource links

**Use This When**:
- Setting up the system
- First-time deployment
- Choosing privacy level
- Testing privacy features

---

### [`.env.example`](.env.example) ⚙️ CONFIGURATION
**Purpose**: Environment variable template  

**Required**:
```bash
GROQ_API_KEY=your_key_here  # Get from https://console.groq.com
```

**Optional**:
```bash
PRIVACY_LEVEL=STANDARD      # STRICT, STANDARD, or BASIC
OLLAMA_BASE_URL=...         # Local LLM (if not using Groq)
VIOLATION_LOG_FILE=...      # Custom log location
```

**How to Use**:
```bash
cp .env.example .env
nano .env  # Edit with your values
```

---

### [`verify_implementation.sh`](verify_implementation.sh) ✅ VERIFICATION
**Purpose**: Verify all improvements are in place  

**Checks**:
- 25 implementation checks
- File existence
- Code integration
- Feature verification

**How to Run**:
```bash
bash verify_implementation.sh
```

**Output**: Pass/fail status for each check

---

### [`IMPROVEMENT_SUMMARY.md`](IMPROVEMENT_SUMMARY.md) 📊 DETAILED CHANGELOG
**Purpose**: Complete list of improvements  

**Covers**:
- All enhancements made
- Before/after comparisons
- Statistics
- Technology used
- Test coverage
- File changes

**Use This When**:
- Understanding what changed
- Documenting improvements
- Reviewing new features

---

### [`COMPLETION_REPORT.md`](COMPLETION_REPORT.md) ✅ FINAL STATUS
**Purpose**: Implementation completion summary  

**Contains**:
- Status: 100% complete
- Verification: 25/25 checks passed
- What was delivered
- Security layers
- Getting started steps
- Final statistics

---

### [`requirements.txt`](requirements.txt) 📦 DEPENDENCIES
**Purpose**: Python package dependencies  

**Key Additions**:
- `llm-guard>=0.3.0` - Input/output scanning
- `transformers>=4.30.0` - Model management
- `torch>=2.0.0` - Deep learning
- `python-docx>=0.8.11` - Word documents
- `python-pptx>=0.6.21` - PowerPoint
- `matplotlib>=3.7.0` - Charting
- `networkx>=3.0.0` - Graph viz

**Install**:
```bash
pip install -r requirements.txt
```

---

## 🔄 Workflow & Integration

### Typical User Flow
```
User Upload PDF
    ↓
app.py: process_pdfs()
    ↓
PDF PII Redaction (security.py)
    ↓
FAISS Vector Storage
    ↓
User Input Question
    ↓
check_prompt() [guard_utils.py]
    ↓
RAG Retrieval (rag_utils.py)
    ↓
LLM Generation (Groq API)
    ↓
check_response() [guard_utils.py]
    ↓
Output Formatting [privacy_output_formatter.py]
    ↓
User Receives Sanitized Response
```

### Guard Integration Points
```
guard_utils.py
├─ LLMGuardScanner (6 input + 4 output scanners)
├─ LlamaGuardScanner (content classification)
├─ PrivacySanitizer (PII redaction)
└─ log_violation() (audit trail)

privacy_config.py
├─ Configures all scanners
├─ Defines PII patterns
├─ Sets privacy levels
└─ Manages thresholds

app.py
├─ Calls check_prompt()
├─ Calls check_response()
└─ Logs violations
```

---

## 🎯 Configuration Quick Reference

### Privacy Levels
```bash
PRIVACY_LEVEL=STRICT      # Max security, slow (~400ms)
PRIVACY_LEVEL=STANDARD    # Balanced (default) (~150ms)
PRIVACY_LEVEL=BASIC       # Fast, minimal guards (~80ms)
```

### Guard Thresholds
Edit in `privacy_config.py`:
```python
"threshold": 0.5  # 0-1, lower = stricter
```

### Add Custom PII
Edit `privacy_config.py`:
```python
PII_PATTERNS["CUSTOM"] = r"pattern_here"
```

---

## 🔍 File Sizes Summary

| File | Size | Purpose |
|------|------|---------|
| app.py | ~800 lines | Main application |
| guard_utils.py | 450 lines | Guard implementation |
| privacy_config.py | 270 lines | Configuration |
| privacy_output_formatter.py | 400 lines | Output formatting |
| PRIVACY.md | 500+ lines | Full documentation |
| SETUP_PRIVACY.md | 300+ lines | Quick start |
| requirements.txt | 40+ lines | Dependencies |

---

## ✅ Implementation Checklist

Use this to verify everything is working:

- [ ] Read SETUP_PRIVACY.md
- [ ] Copy .env.example to .env
- [ ] Add GROQ_API_KEY to .env
- [ ] Run: `pip install -r requirements.txt`
- [ ] Run: `streamlit run app.py`
- [ ] Upload test PDF with PII
- [ ] Ask question with sensitive data
- [ ] Verify email is masked
- [ ] Check violations.jsonl was created
- [ ] Review PRIVACY.md for details
- [ ] Run: `bash verify_implementation.sh`

---

## 🆘 Troubleshooting Quick Links

**Problem**: Imports fail  
**Solution**: Check `requirements.txt` is installed → See SETUP_PRIVACY.md

**Problem**: Guards too strict  
**Solution**: Lower thresholds → See privacy_config.py

**Problem**: Performance slow  
**Solution**: Use BASIC mode → See `.env.example`

**Problem**: PII not redacted  
**Solution**: Check privacy config → See PRIVACY.md

**Problem**: API key error  
**Solution**: Add GROQ_API_KEY to .env → See `.env.example`

---

## 📞 Support Resources

1. **Setup Issues**: Read `SETUP_PRIVACY.md`
2. **Configuration**: Edit `privacy_config.py`
3. **Privacy Questions**: Read `PRIVACY.md`
4. **What Changed**: See `IMPROVEMENT_SUMMARY.md`
5. **Verification**: Run `verify_implementation.sh`

---

## 🎓 Recommended Reading Order

1. **This file** (you are here) - 5 min
2. **README.md** - Understand project - 5 min
3. **SETUP_PRIVACY.md** - Get started - 10 min
4. **PRIVACY.md** - Learn details - 30 min
5. **IMPROVEMENT_SUMMARY.md** - See changes - 15 min

---

**Total Reading Time**: ~65 minutes for complete understanding

---

*Last Updated: June 2024*  
*For latest updates, see COMPLETION_REPORT.md*
