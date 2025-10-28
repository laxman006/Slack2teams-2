# 🎯 Unified Fine-Tuning Script - Complete Guide

## ✅ The Hybrid Script is Ready!

**File:** `scripts/finetune_unified.py`

This is the **ultimate fine-tuning script** that combines ALL features from both previous scripts into one powerful tool.

---

## 🌟 What Makes it Special?

### **Auto-Detects Format** 🔍
No need to know if your file is Langfuse or standard format - it figures it out!

### **All Features in One Place** 💪
- ✅ Langfuse format support
- ✅ Standard format support
- ✅ Auto-conversion
- ✅ Data validation
- ✅ Quality scoring (0-100)
- ✅ Automatic deduplication
- ✅ Dry-run mode
- ✅ Validate-only mode
- ✅ Status checking
- ✅ **Real-time progress monitoring with live progress bar** 🎯
- ✅ **End-to-end auto-monitor mode** ⭐ **NEW!**
- ✅ Cleanup commands
- ✅ Merge legacy files

---

## 🚀 Quick Start

### **For Your Langfuse Dataset:**

```bash
# 🌟 BEST: One command does everything (recommended)
python scripts/finetune_unified.py auto "C:\Users\ChaitanyaMalle\Downloads\1761296600214-lf-dataset_items-export-cmh4b8o3z002kad07yk8i4b5q.jsonl" --monitor

# Option 2: Auto-detect without monitoring
python scripts/finetune_unified.py auto "C:\Users\ChaitanyaMalle\Downloads\1761296600214-lf-dataset_items-export-cmh4b8o3z002kad07yk8i4b5q.jsonl"

# Option 3: Validate first
python scripts/finetune_unified.py validate "C:\Users\ChaitanyaMalle\Downloads\1761296600214-lf-dataset_items-export-cmh4b8o3z002kad07yk8i4b5q.jsonl"
```

---

## 📋 All Commands

### **1. Fine-Tune with Langfuse Export**
```bash
python scripts/finetune_unified.py start-langfuse FILE.jsonl
```

### **2. Fine-Tune with Standard Format**
```bash
python scripts/finetune_unified.py start
```

### **3. Auto-Detect Format (Smartest)**
```bash
python scripts/finetune_unified.py auto FILE.jsonl
```

### **4. Validate Only**
```bash
python scripts/finetune_unified.py validate FILE.jsonl
```

### **5. Check Status**
```bash
# All jobs
python scripts/finetune_unified.py status

# Specific job
python scripts/finetune_unified.py status JOB_ID
```

### **6. Monitor Live (Real-Time Progress Bar)**
```bash
# Monitor with live updates and progress bar
python scripts/finetune_unified.py monitor JOB_ID

# Or monitor the last started job (auto-detected)
python scripts/finetune_unified.py monitor
```

**Features:**
- Live progress bar with completion percentage
- Step counter (e.g., Step 90/200)
- Real-time loss metrics
- Elapsed time tracking
- Streaming event logs
- Auto-completes when job finishes
- Press Ctrl+C to stop monitoring (job continues running)

### **7. Cleanup Old Files**
```bash
python scripts/finetune_unified.py cleanup
```

### **8. Merge Legacy Files**
```bash
python scripts/finetune_unified.py merge
```

### **9. End-to-End with Auto-Monitor** ⭐ **NEW!**
```bash
# Single command that does EVERYTHING:
# 1. Loads & validates
# 2. Shows quality metrics
# 3. Starts fine-tuning
# 4. Monitors until completion

python scripts/finetune_unified.py auto FILE.jsonl --monitor
```

**Perfect for:** Quick iterations, one-and-done execution

### **10. Dry-Run (Any Command)**
```bash
python scripts/finetune_unified.py start-langfuse FILE.jsonl --dry-run
python scripts/finetune_unified.py auto FILE.jsonl --dry-run
```

---

## 🎯 Recommended Workflow

### **For Your Current Dataset (86 Examples):**

**Step 1: Validate**
```bash
python scripts/finetune_unified.py validate "C:\Users\ChaitanyaMalle\Downloads\1761296600214-lf-dataset_items-export-cmh4b8o3z002kad07yk8i4b5q.jsonl"
```

**Result:**
```
Dataset Quality Report:
   Total examples: 86
   Quality Score: 70/100 (GOOD)
   Status: Ready for fine-tuning!
```

---

**Step 2: Start Fine-Tuning**
```bash
python scripts/finetune_unified.py start-langfuse "C:\Users\ChaitanyaMalle\Downloads\1761296600214-lf-dataset_items-export-cmh4b8o3z002kad07yk8i4b5q.jsonl"
```

**What Happens:**
1. ✅ Converts Langfuse format to OpenAI format
2. ✅ Validates data (70/100 - GOOD)
3. ✅ Removes duplicates (1 found)
4. ✅ Uploads to OpenAI
5. ✅ Starts fine-tuning
6. 📊 Monitor with real-time progress bar

**Step 3: Monitor Progress**
```bash
# Use the JOB_ID from step 2
python scripts/finetune_unified.py monitor ftjob-xxxxxxxxxxxxx
```

**Live Output:**
```
======================================================================
REAL-TIME FINE-TUNING MONITOR
======================================================================

Job ID: ftjob-xxxxxxxxxxxxx
Press Ctrl+C to stop monitoring

┌────────────────────────────────────────────────────────────────────┐
│ ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ 45%
│            Step 90/200 | Loss: 1.2340 | Elapsed: 0:12:34          │
└────────────────────────────────────────────────────────────────────┘
Status: running | Model: gpt-4o-mini

[14:23:45] Step 90 completed with average loss 1.2340
[14:24:12] Step 91 completed with average loss 1.2298
```

- ⏱️ Updates every 5 seconds
- 📊 Shows real progress bar
- 📉 Live loss metrics
- ⏰ Elapsed time tracking
- ✅ Auto-completes when finished

---

**Step 4: Update Your Code**

When fine-tuning completes, you'll get a model name like:
```
ft:gpt-4o-mini-2024-07-18:cloudfuze::AbCdEfGh
```

Update `app/endpoints.py` in 3 places:
- Line ~153 (main chat)
- Line ~242 (generate_improved_response)  
- Line ~1154 (generate_improved_response_with_context)

Change:
```python
model_name="gpt-4o-mini"
```
To:
```python
model_name="ft:gpt-4o-mini-2024-07-18:cloudfuze::AbCdEfGh"
```

---

## 📊 Comparison with Previous Scripts

| Feature | Old manage_fine_tuning.py | Old finetune_from_langfuse.py | **NEW Unified** |
|---------|---------------------------|-------------------------------|-----------------|
| Langfuse format | ❌ | ✅ | ✅ |
| Standard format | ✅ | ❌ | ✅ |
| Auto-detect | ❌ | ❌ | ✅ **NEW!** |
| Validation | Basic | ✅ | ✅ |
| Quality scoring | ❌ | ✅ | ✅ |
| Deduplication | ❌ | ✅ | ✅ |
| Dry-run | ❌ | ✅ | ✅ |
| Status check | ✅ | ❌ | ✅ |
| Cleanup | ✅ | ❌ | ✅ |
| Merge files | ✅ | ❌ | ✅ |
| **Total** | 3/10 | 5/10 | **10/10** ✅ |

---

## 💡 Smart Features

### **Auto-Detection**
Automatically detects if your file is:
- Langfuse format (`input` + `expectedOutput`)
- Standard format (`input` + `corrected_output`)

No need to remember which command to use!

### **Quality Scoring**
Gives your dataset a score (0-100) with:
- Dataset size check
- Input diversity analysis
- Output length validation
- Recommendations for improvement

### **Deduplication**
Automatically removes duplicate entries based on content hash.

**Your dataset:** 87 lines → 86 unique (1 duplicate removed)

---

## 🎯 Which Command to Use?

### **For Langfuse Exports (Your Case):**
```bash
# Best: Auto-detect
python scripts/finetune_unified.py auto YOUR_FILE.jsonl

# Or explicit:
python scripts/finetune_unified.py start-langfuse YOUR_FILE.jsonl
```

### **For Standard corrections.jsonl:**
```bash
python scripts/finetune_unified.py start
```

### **Not Sure? Use Auto!**
```bash
python scripts/finetune_unified.py auto YOUR_FILE.jsonl
```

---

## 📈 Real Output Example

### **When You Run Validate:**
```
======================================================================
FINE-TUNING FROM LANGFUSE EXPORT
(VALIDATION ONLY)
======================================================================

[STEP 1] Converting Langfuse export to OpenAI format...
[*] Converting Langfuse export: YOUR_FILE.jsonl

[OK] Conversion complete:
   Valid examples: 86
   Duplicates removed: 1
   Invalid entries: 0
   Success rate: 98.9%

[STEP 2] Analyzing dataset quality...

======================================================================
DATASET QUALITY REPORT
======================================================================

Dataset Statistics:
   Total examples: 86
   Unique inputs: 47
   Input diversity: 54.7%

Length Statistics:
   Average input: 54 characters
   Average output: 2968 characters
   Input range: 39 - 68 chars
   Output range: 251 - 4141 chars

Quality Assessment:
   Quality Score: 70/100
   Quality Rating: GOOD

Quality Issues:
   - Low input diversity (54.7%)
   - Many very long outputs (47 > 3000 chars)

Recommendations:
   - Excellent dataset size for high-quality fine-tuning!
   - Consider adding more diverse examples
======================================================================

[SUCCESS] Validation complete!
Dataset is ready with 86 examples.
```

---

## 🔧 Advanced Options

### **Change Model:**
```bash
python scripts/finetune_unified.py start-langfuse FILE.jsonl --model gpt-4o-2024-08-06
```

### **Dry-Run Test:**
```bash
python scripts/finetune_unified.py start-langfuse FILE.jsonl --dry-run
```

### **Check Specific Job:**
```bash
python scripts/finetune_unified.py status ftjob-abc123
```

---

## 🎯 Best Practices

### **1. Always Validate First**
```bash
python scripts/finetune_unified.py validate YOUR_FILE.jsonl
```

### **2. Review Quality Score**
- **90-100:** Excellent - Go ahead!
- **70-89:** Good - Recommended ✅
- **50-69:** Fair - Consider improvements
- **< 50:** Poor - Add more/better data

### **3. Use Auto-Detect for Simplicity**
```bash
python scripts/finetune_unified.py auto YOUR_FILE.jsonl
```

### **4. Monitor with Status**
```bash
python scripts/finetune_unified.py status
```

---

## 🆚 Old Scripts vs Unified

### **You Can Now Delete:**
- ~~`scripts/finetune_from_langfuse.py`~~ (features merged)
- ~~`scripts/manage_fine_tuning.py`~~ (features merged)

### **Keep Only:**
- ✅ `scripts/finetune_unified.py` (has everything!)

### **Or Keep All** (for compatibility):
- All old scripts still work
- New unified script is recommended

---

## 💰 Cost & Time

**For Your 86 Examples:**
- **Cost:** ~$2-5 (one-time)
- **Time:** 20 min - 2 hours
- **Result:** Much better chatbot responses

---

## ✅ Your Next Step

**Run this command when ready:**

```bash
python scripts/finetune_unified.py start-langfuse "C:\Users\ChaitanyaMalle\Downloads\1761296600214-lf-dataset_items-export-cmh4b8o3z002kad07yk8i4b5q.jsonl"
```

**Or play it safe with validate first:**

```bash
# Step 1: Validate (already done ✅)
python scripts/finetune_unified.py validate "C:\Users\ChaitanyaMalle\Downloads\1761296600214-lf-dataset_items-export-cmh4b8o3z002kad07yk8i4b5q.jsonl"

# Step 2: Start fine-tuning
python scripts/finetune_unified.py start-langfuse "C:\Users\ChaitanyaMalle\Downloads\1761296600214-lf-dataset_items-export-cmh4b8o3z002kad07yk8i4b5q.jsonl"

# Step 3: Monitor
python scripts/finetune_unified.py status
```

---

## 🎉 Summary

**What You Get:**
- ✅ One script for everything
- ✅ Auto-detects format
- ✅ Validates quality (70/100 - GOOD)
- ✅ Removes duplicates
- ✅ Handles large datasets
- ✅ Status monitoring
- ✅ Cleanup tools
- ✅ Professional output

**Your Dataset:**
- ✅ 86 examples ready
- ✅ Quality score: 70/100 (GOOD)
- ✅ Validated and tested
- ✅ Ready to fine-tune!

**One command away from better responses!** 🚀

```bash
python scripts/finetune_unified.py start-langfuse "C:\Users\ChaitanyaMalle\Downloads\1761296600214-lf-dataset_items-export-cmh4b8o3z002kad07yk8i4b5q.jsonl"
```

