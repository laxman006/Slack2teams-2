# 🔄 Update Production Deployment Guide

**Server:** newcf3.cloudfuze.com (64.227.160.206)  
**Purpose:** Pull new code and redeploy with MongoDB Atlas configuration

---

## 🚀 Quick Update Process

### Step 1: SSH to Your Server

```bash
ssh user@64.227.160.206
# or
ssh user@newcf3.cloudfuze.com
```

---

### Step 2: Navigate to Application Directory

```bash
cd /opt/slack2teams
```

---

### Step 3: Pull Latest Code from Git

```bash
# Check current status
git status

# Fetch latest changes
git fetch origin

# Pull the latest code
git pull origin main
# or if your branch is 'master':
# git pull origin master
```

**Expected Output:**
```
Updating 46e52b8..a3ae671
Fast-forward
 deploy-ubuntu.sh              |   7 +-
 docker-compose.prod.yml       |   6 +-
 MONGODB-ATLAS-SETUP.md        | 450 +++++++++++++++++++++++++++++++++++++++++
 DEPLOYMENT-READY-SUMMARY.md   | 200 ++++++++++++++++++
 4 files changed, 709 insertions(+), 4 deletions(-)
```

---

### Step 4: Update Environment Variables

```bash
# Edit .env.prod file
nano .env.prod
```

**Update or verify these lines:**

```env
# MongoDB Atlas Configuration (UPDATED!)
MONGODB_URL=mongodb+srv://sudityanimmala_db_user:Arss_2025@cluster0.sgqafxp.mongodb.net/slack2teams?retryWrites=true&w=majority&appName=Cluster0
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories
MONGODB_VECTORSTORE_COLLECTION=cloudfuze_vectorstore

# Vectorstore Configuration
VECTORSTORE_BACKEND=mongodb
INITIALIZE_VECTORSTORE=false
```

**Save and exit:** Press `Ctrl+X`, then `Y`, then `Enter`

---

### Step 5: Stop Current Containers

```bash
# Stop and remove current containers
docker-compose -f docker-compose.prod.yml down
```

**Expected Output:**
```
Stopping slack2teams-nginx-prod ... done
Stopping slack2teams-backend-prod ... done
Removing slack2teams-nginx-prod ... done
Removing slack2teams-backend-prod ... done
```

---

### Step 6: Rebuild and Start with New Configuration

```bash
# Rebuild containers with new code and start
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

**Expected Output:**
```
Building backend
[+] Building 45.2s (12/12) FINISHED
...
Creating slack2teams-backend-prod ... done
Creating slack2teams-nginx-prod ... done
```

**The `--build` flag ensures Docker rebuilds images with the latest code!**

---

### Step 7: Verify Deployment

```bash
# Check if containers are running
docker-compose -f docker-compose.prod.yml ps
```

**Expected Output:**
```
Name                          State       Ports
----------------------------------------------------------------
slack2teams-backend-prod     Up          8002/tcp
slack2teams-nginx-prod       Up          0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

---

### Step 8: Check Logs for MongoDB Connection

```bash
# Follow logs in real-time
docker-compose -f docker-compose.prod.yml logs -f backend
```

**Look for these SUCCESS messages:**
```
✅ MongoDB connection successful
✅ Connected to database: slack2teams
✅ Vectorstore backend: mongodb
✅ Vectorstore collection: cloudfuze_vectorstore
✅ Found 1511 documents in vectorstore
✅ Application started successfully on port 8002
```

**Press `Ctrl+C` to exit logs**

---

### Step 9: Test the Application

```bash
# Test health endpoint
curl https://newcf3.cloudfuze.com/health

# Or from your local machine:
curl https://newcf3.cloudfuze.com/health
```

**Expected Response:**
```json
{"status":"healthy"}
```

---

### Step 10: Verify in Browser

1. Visit: **https://newcf3.cloudfuze.com**
2. Login with @cloudfuze.com email
3. Ask: "What is CloudFuze?"
4. Should get response from MongoDB Atlas vectorstore

---

## 🔍 Troubleshooting

### Issue: Git Pull Fails (Local Changes)

```bash
# If you see "error: Your local changes would be overwritten"

# Option 1: Stash local changes
git stash
git pull origin main
git stash pop

# Option 2: Discard local changes (CAREFUL!)
git reset --hard HEAD
git pull origin main
```

---

### Issue: MongoDB Connection Failed

```bash
# Check logs for error details
docker-compose -f docker-compose.prod.yml logs backend | grep -i mongo

# Common errors:
```

**Error:** `MongoServerError: Authentication failed`
- **Fix:** Check MongoDB username/password in `.env.prod`
- Verify: `MONGODB_URL=mongodb+srv://sudityanimmala_db_user:Arss_2025@...`

**Error:** `Connection timeout` or `Network error`
- **Fix:** Whitelist server IP in MongoDB Atlas
- Go to: https://cloud.mongodb.com → Network Access
- Add IP: **64.227.160.206** or **0.0.0.0/0**

**Error:** `Database not found`
- **Fix:** Verify connection string includes database name
- Should be: `.../slack2teams?retryWrites=...`

---

### Issue: Containers Won't Start

```bash
# Check what went wrong
docker-compose -f docker-compose.prod.yml logs

# Check Docker disk space
docker system df

# Clean up if needed
docker system prune -a
```

---

### Issue: Old Code Still Running

```bash
# Force rebuild without cache
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

---

## 📋 Complete Update Script (Copy-Paste)

Save this as a file or run line by line:

```bash
#!/bin/bash
# Quick update script for production deployment

echo "🔄 Updating Slack2Teams Production Deployment..."

# Navigate to app directory
cd /opt/slack2teams

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Stop current containers
echo "🛑 Stopping current containers..."
docker-compose -f docker-compose.prod.yml down

# Rebuild and start
echo "🔨 Rebuilding and starting containers..."
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# Wait for startup
echo "⏳ Waiting for services to start..."
sleep 20

# Check status
echo "✅ Checking service status..."
docker-compose -f docker-compose.prod.yml ps

# Show logs
echo "📋 Recent logs:"
docker-compose -f docker-compose.prod.yml logs --tail=50 backend

echo ""
echo "🎉 Update complete!"
echo "Visit: https://newcf3.cloudfuze.com"
echo ""
echo "To view live logs: docker-compose -f docker-compose.prod.yml logs -f"
```

**To use:**
```bash
# Copy script to server
nano update-deployment.sh
# Paste the script above
# Save: Ctrl+X, Y, Enter

# Make executable
chmod +x update-deployment.sh

# Run it
./update-deployment.sh
```

---

## 🔐 Before You Push (From Your Local Machine)

If you made changes and want to push them:

### From Your Local Development Machine:

```bash
# Navigate to your project
cd c:\Users\LaxmanKadari\Desktop\Slack2teams-2

# Check status
git status

# Add all changes
git add -A

# Commit changes
git commit -m "feat: your change description"

# Push to remote repository
git push origin main
# or if using master branch:
# git push origin master
```

**Then SSH to server and pull the changes as shown above.**

---

## 📊 Deployment Workflow

```
Local Machine (Your Computer)
    ↓
1. Make changes to code
    ↓
2. git add -A
    ↓
3. git commit -m "message"
    ↓
4. git push origin main
    ↓
Server (64.227.160.206)
    ↓
5. SSH to server
    ↓
6. cd /opt/slack2teams
    ↓
7. git pull origin main
    ↓
8. docker-compose down
    ↓
9. docker-compose up -d --build
    ↓
10. Verify deployment ✅
```

---

## ⚙️ Environment File Management

### Option 1: Keep .env.prod on Server (RECOMMENDED)

The `.env.prod` file with your secrets should stay on the server and NOT be committed to git.

```bash
# On server, after git pull:
# .env.prod stays unchanged with your actual credentials
# Just rebuild containers:
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

### Option 2: Update .env.prod After Pull

```bash
# After git pull, update .env.prod if template changed:
nano .env.prod
# Add any new environment variables
# Keep existing credentials
```

---

## 🚀 Zero-Downtime Update (Advanced)

For minimal downtime:

```bash
# Pull new code
git pull origin main

# Build new images (while old containers run)
docker-compose -f docker-compose.prod.yml build

# Quick restart
docker-compose -f docker-compose.prod.yml up -d

# Docker will:
# 1. Create new containers
# 2. Start them
# 3. Stop old containers
# 4. Remove old containers
```

---

## ✅ Post-Update Checklist

After updating:

- [ ] Containers running: `docker-compose ps`
- [ ] No errors in logs: `docker-compose logs backend`
- [ ] MongoDB connected: Check for "MongoDB connection successful"
- [ ] Vectorstore loaded: "Found 1511 documents"
- [ ] Application accessible: https://newcf3.cloudfuze.com
- [ ] Login works (Microsoft OAuth)
- [ ] Chatbot responds correctly
- [ ] New system prompt active (rejects general questions)

---

## 🎯 Current Changes to Deploy

The latest code includes:

1. ✅ MongoDB Atlas cloud storage configuration
2. ✅ Updated system prompt (CloudFuze-only, dynamic rejections)
3. ✅ Langfuse host fixed (cloud.langfuse.com)
4. ✅ Production deployment optimizations

**After pulling and redeploying:**
- ✅ Application uses MongoDB Atlas (1,511 documents)
- ✅ Chatbot rejects general questions gracefully
- ✅ All data persists in cloud
- ✅ Production-ready configuration

---

## 📞 Quick Commands Reference

```bash
# SSH to server
ssh user@64.227.160.206

# Navigate to app
cd /opt/slack2teams

# Pull latest code
git pull origin main

# Quick restart
docker-compose -f docker-compose.prod.yml restart

# Full rebuild
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check status
docker-compose -f docker-compose.prod.yml ps

# Test application
curl https://newcf3.cloudfuze.com/health
```

---

## 🎉 Success!

When you see this, you're done:

✅ Latest code pulled from git  
✅ Containers rebuilt with new code  
✅ MongoDB Atlas connected (1,511 documents)  
✅ Application running on https://newcf3.cloudfuze.com  
✅ ChatBot using CloudFuze-only prompt  
✅ Dynamic rejection messages working  

**Your deployment is updated and running! 🚀**

---

**Last Updated:** 2025-01-29  
**Server:** newcf3.cloudfuze.com (64.227.160.206)  
**Latest Commit:** a3ae671 (MongoDB Atlas cloud storage)

