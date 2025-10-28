# 🚀 Fine-Tuning Quick Start

## ⚡ The Fastest Way (One Command)

```bash
python scripts/finetune_unified.py auto "C:\Users\ChaitanyaMalle\Downloads\1761296600214-lf-dataset_items-export-cmh4b8o3z002kad07yk8i4b5q.jsonl" --monitor
```

**That's it!** This single command will:
1. ✅ Load & validate your dataset
2. ✅ Show quality metrics
3. ✅ Start fine-tuning
4. ✅ Monitor progress with live updates
5. ✅ Complete and show final model name

**Time:** 20-60 minutes (automatic)  
**Your effort:** Run 1 command

---

## 📊 What You'll See

```
======================================================================
FINE-TUNING FROM AUTO-DETECTED FORMAT
======================================================================

[STEP 1] Converting Langfuse export...
✓ Converted 86 examples

[STEP 2] Analyzing dataset quality...
Quality Score: 70/100 (GOOD)

[STEP 3] Preparing training file...
✓ Saved training file

[STEP 4] Starting OpenAI fine-tuning...
✓ Job created: ftjob-abc123xyz

======================================================================
STARTING AUTOMATIC MONITORING...
======================================================================

┌────────────────────────────────────────────────────────────────────┐
│ ████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ 45%
│            Step 90/200 | Loss: 1.2340 | Elapsed: 0:12:34          │
└────────────────────────────────────────────────────────────────────┘

... (continues until completion) ...

✅ Fine-tuning completed successfully!
   Fine-tuned model: ft:gpt-4o-mini-2024-07-18:cloudfuze::AbCdEfGh
```

---

## 🎯 Next Step After Completion

Update `app/endpoints.py` in 3 places:
```python
model_name="ft:gpt-4o-mini-2024-07-18:cloudfuze::AbCdEfGh"
```

Locations:
- Line ~153 (main chat endpoint)
- Line ~242 (generate_improved_response)
- Line ~1154 (generate_improved_response_with_context)

---

## 🛠️ Other Useful Commands

### **Validate Only (No Training)**
```bash
python scripts/finetune_unified.py validate FILE.jsonl
```

### **Check Status of Running Job**
```bash
python scripts/finetune_unified.py status
```

### **Monitor Existing Job**
```bash
python scripts/finetune_unified.py monitor JOB_ID
```

---

## 💡 Pro Tips

1. **Press Ctrl+C** to stop monitoring (job continues running)
2. **Resume monitoring** with: `python scripts/finetune_unified.py monitor`
3. **Check all jobs** with: `python scripts/finetune_unified.py status`

---

## 📖 Full Documentation

- **AUTO_MONITOR_FEATURE.md** - Complete feature guide
- **UNIFIED_FINE_TUNING_GUIDE.md** - All commands and options
- **AUTO_MONITOR_COMPLETE.md** - Implementation summary

---

## ✅ Ready When You Are!

Just copy and run the command at the top of this file. Walk away and come back to a fine-tuned model! 🎉

