# 🎯 START HERE - Test Microsoft Login in 3 Steps

## 🚀 Quick Start (Less than 2 minutes)

### **Step 1: Start Backend** (Terminal 1)

```powershell
cd C:\Users\LaxmanKadari\Desktop\Slack2teams-2
python server.py
```

**Wait for:** ✅ `Uvicorn running on http://0.0.0.0:8002`

**Keep this terminal running!** 🔴

---

### **Step 2: Open Frontend** (Browser)

Double-click: `login.html`

**OR** use HTTP server (Terminal 2):
```powershell
python -m http.server 8003
# Then go to: http://localhost:8003/login.html
```

---

### **Step 3: Test Login**

1. Click **"Sign in with Microsoft"**
2. Sign in with your CloudFuze email
3. ✅ Should redirect to chat interface

---

## 🔍 What to Watch

### Terminal 1 (Backend):
```
✅ Good: INFO: "POST /auth/microsoft/callback HTTP/1.1" 200 OK
❌ Bad:  INFO: "POST /auth/microsoft/callback HTTP/1.1" 400 Bad Request
```

### Browser Console (F12):
```
✅ Good: OAuth code received, processing...
❌ Bad:  Code verifier not found
```

---

## ❓ Having Issues?

Run diagnostic first:
```bash
python test_auth.py
```

Then check:
- **`READY-TO-TEST.md`** - Quick guide
- **`TEST-INSTRUCTIONS.md`** - Detailed steps
- **`MICROSOFT-LOGIN-TROUBLESHOOTING.md`** - Fix errors

---

## ✅ What Was Fixed

- ✅ Code verifier now uses `localStorage` (was `sessionStorage`)
- ✅ Login redirect should work now
- ✅ Created diagnostic tools
- ✅ Added comprehensive documentation

---

## 📞 Quick Help

**Backend won't start:**
```powershell
# Check if port 8002 is free
netstat -ano | findstr :8002

# Or use different port
uvicorn server:app --port 8005
```

**Login button doesn't work:**
- Open browser DevTools (F12)
- Check Console for errors
- Make sure backend is running

**"Code verifier not found":**
- Already fixed! (Changed to localStorage)
- Clear browser cache and try again

---

That's it! Just run `python server.py` and open `login.html` 🎉



