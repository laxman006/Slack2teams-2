# 🌐 MongoDB Atlas Cloud Setup for Production

**Required for Deployment to:** newcf3.cloudfuze.com  
**Status:** ✅ **CONFIGURED** - MongoDB Atlas connection string is set  
**Purpose:** Connect production server to your MongoDB Atlas cloud database

---

## ✅ **Connection Already Configured!**

Your MongoDB Atlas connection is pre-configured in the deployment script:

```
Cluster: cluster0.sgqafxp.mongodb.net
Database: slack2teams
User: sudityanimmala_db_user
Status: ✅ Ready for deployment
```

**What you need to verify:**
1. ✅ Server IP **64.227.160.206** is whitelisted in MongoDB Atlas Network Access
2. ✅ Database user has read/write permissions on `slack2teams` database
3. ✅ Your 1,511 vectorstore documents exist in this cluster

---

## ✅ Why MongoDB Atlas (Cloud)?

Your application **already has 1,511 documents** in MongoDB Atlas:
- ✅ `cloudfuze_vectorstore` - 1,511 vector embeddings
- ✅ `chat_histories` - User conversations
- ✅ `feedback_history` - User feedback
- ✅ `fine_tuning_data` - Training data

**Using Atlas in production means:**
- ✅ No need to migrate data to the server
- ✅ Automatic backups and scaling
- ✅ Accessible from anywhere
- ✅ No MongoDB installation on server required

---

## 🔑 Get Your MongoDB Atlas Connection String

### Step 1: Login to MongoDB Atlas
1. Go to https://cloud.mongodb.com
2. Login with your account
3. Select your project/cluster

### Step 2: Get Connection String
1. Click **"Connect"** on your cluster
2. Choose **"Connect your application"**
3. Select **Driver:** Python, **Version:** 3.12 or later
4. Copy the connection string:

```
mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority
```

### Step 3: Replace Placeholders
Replace these in your connection string:
- `<username>` → Your MongoDB username
- `<password>` → Your MongoDB password (URL encoded if it has special characters)
- `<database>` → `slack2teams` (your database name)

**Example:**
```
mongodb+srv://myuser:mypassword123@cluster0.abcde.mongodb.net/slack2teams?retryWrites=true&w=majority
```

---

## 🔐 Network Access Configuration

### Allow Server IP Access

1. In MongoDB Atlas, go to **Network Access**
2. Click **"Add IP Address"**
3. Add your server IP: **64.227.160.206**
4. Or add **0.0.0.0/0** for "Allow from anywhere" (less secure but simpler)
5. Click **"Confirm"**

**Important:** Your server must be whitelisted, or the connection will fail!

---

## 📝 Update Production Environment File

### On Your Server (64.227.160.206):

```bash
# SSH to server
ssh user@64.227.160.206

# Edit environment file
cd /opt/slack2teams
nano .env.prod
```

### Update This Line:

**Before (WRONG - uses localhost):**
```env
MONGODB_URL=mongodb://localhost:27017
```

**After (CORRECT - uses Atlas cloud):**
```env
MONGODB_URL=mongodb+srv://myuser:mypassword123@cluster0.abcde.mongodb.net/slack2teams?retryWrites=true&w=majority
```

### Full `.env.prod` Example:

```env
# Production Environment Variables

# OpenAI API Key
OPENAI_API_KEY=sk-proj-...

# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT=cloudfuze.com

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# MongoDB Atlas Configuration (Cloud Storage)
MONGODB_URL=mongodb+srv://myuser:mypassword@cluster0.abcde.mongodb.net/slack2teams?retryWrites=true&w=majority
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories
MONGODB_VECTORSTORE_COLLECTION=cloudfuze_vectorstore

# Vectorstore Configuration
VECTORSTORE_BACKEND=mongodb
INITIALIZE_VECTORSTORE=false
```

---

## 🧪 Test MongoDB Connection

### Before Starting Application:

```bash
# Install MongoDB shell (mongosh) on server
sudo apt-get install -y mongodb-mongosh

# Test connection
mongosh "mongodb+srv://myuser:mypassword@cluster0.abcde.mongodb.net/slack2teams"

# If successful, you'll see:
# Current Mongosh Log ID: ...
# Connecting to: mongodb+srv://...
# Using MongoDB: 7.x.x
```

### Verify Your Data:

```bash
# Count vectorstore documents (should be 1511)
mongosh "mongodb+srv://..." --eval "db.cloudfuze_vectorstore.countDocuments()"

# List collections
mongosh "mongodb+srv://..." --eval "db.getCollectionNames()"
```

**Expected Output:**
```json
[
  "cloudfuze_vectorstore",    // 1511 documents
  "chat_histories",
  "feedback_history",
  "fine_tuning_data",
  "corrected_responses",
  "bad_responses",
  "fine_tuning_status",
  "vectorstore_metadata"
]
```

---

## 🚀 Start Application with MongoDB Atlas

### Restart Docker Containers:

```bash
cd /opt/slack2teams

# Stop existing containers
docker-compose -f docker-compose.prod.yml down

# Start with updated environment
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Look for Success Messages:

```
✅ MongoDB connection successful
✅ Connected to database: slack2teams
✅ Vectorstore loaded: 1511 documents
✅ Application started successfully
```

### If You See Errors:

❌ `Authentication failed`
- Check username/password in connection string
- Verify database user has read/write permissions

❌ `Connection timeout`
- Check IP whitelist in MongoDB Atlas Network Access
- Verify server IP: 64.227.160.206 is allowed

❌ `Database not found`
- Ensure connection string uses `slack2teams` database
- Verify database exists in Atlas

---

## 🔍 Verify Production Storage

### Test Application:

1. **Visit:** https://newcf3.cloudfuze.com
2. **Login** with @cloudfuze.com email
3. **Ask question:** "What is CloudFuze?"
4. **Check response** - should use vectorstore data

### Check MongoDB Atlas:

1. Go to MongoDB Atlas dashboard
2. Browse Collections → `chat_histories`
3. You should see **new conversation** just created
4. Browse `cloudfuze_vectorstore` → Should have 1,511 documents

### Monitor Logs:

```bash
# Application logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Should see:
# Vector search query: ...
# Found 4 relevant documents
# Response generated successfully
# Chat saved to MongoDB
```

---

## 📊 Data Flow in Production

### User Interaction → MongoDB Atlas:

```
1. User asks: "What is CloudFuze?"
   ↓
2. App queries MongoDB Atlas vectorstore (1,511 docs)
   ↓
3. Retrieves relevant documents from cloud
   ↓
4. Generates response using GPT-4o-mini
   ↓
5. Saves conversation to MongoDB Atlas chat_histories
   ↓
6. User sees response (data persists in cloud)
```

### All Storage Operations:

| Operation | Storage Location | Happens Where |
|-----------|------------------|---------------|
| Search vectors | MongoDB Atlas | Cloud |
| Load chat history | MongoDB Atlas | Cloud |
| Save new message | MongoDB Atlas | Cloud |
| User feedback | MongoDB Atlas | Cloud |
| Corrections | MongoDB Atlas | Cloud |
| Fine-tuning data | MongoDB Atlas | Cloud |

**Everything is in the cloud!** ☁️

---

## 🔐 Security Best Practices

### 1. **Secure Connection String**
- ✅ Use strong password
- ✅ URL encode special characters in password
- ✅ Never commit `.env.prod` to git

### 2. **Network Access**
- ✅ Whitelist only server IP (64.227.160.206)
- ❌ Avoid 0.0.0.0/0 (allow from anywhere) if possible

### 3. **Database User Permissions**
- ✅ Create dedicated user for production
- ✅ Grant only required permissions:
  - Read/write on `slack2teams` database
  - No admin permissions needed

### 4. **Backup Strategy**
- ✅ Enable Atlas automatic backups
- ✅ Configure backup retention period
- ✅ Test restore process periodically

---

## 🆘 Troubleshooting

### Issue: "MongoServerError: Authentication failed"

**Solution:**
```bash
# Check if password has special characters that need URL encoding
# Example: p@ssw0rd! → p%40ssw0rd%21

# Use Python to encode:
python3 -c "import urllib.parse; print(urllib.parse.quote_plus('p@ssw0rd!'))"
```

### Issue: "Connection timeout"

**Solution:**
```bash
# 1. Check Network Access in MongoDB Atlas
# 2. Verify server can reach Atlas:
ping cluster0.abcde.mongodb.net

# 3. Test connection from server:
mongosh "your_connection_string" --eval "db.runCommand({ping: 1})"
```

### Issue: "Database not found"

**Solution:**
```bash
# List available databases
mongosh "your_connection_string" --eval "show dbs"

# Create database if needed (automatically created on first write)
mongosh "your_connection_string" --eval "use slack2teams; db.test.insertOne({test: 1})"
```

### Issue: "No documents in vectorstore"

**Solution:**
```bash
# Verify data exists in Atlas
mongosh "your_connection_string" --eval "db.cloudfuze_vectorstore.countDocuments()"

# If count is 0, you need to migrate data:
# See MONGODB-MIGRATION-GUIDE.md
```

---

## ✅ Production Storage Checklist

Before going live:

- [ ] MongoDB Atlas connection string obtained
- [ ] Server IP (64.227.160.206) whitelisted in Atlas
- [ ] `.env.prod` updated with Atlas connection string
- [ ] Connection tested successfully
- [ ] Vectorstore documents verified (1,511 count)
- [ ] Collections visible in Atlas dashboard
- [ ] Application starts without MongoDB errors
- [ ] Chat saves to Atlas (test with new conversation)
- [ ] Backup strategy configured in Atlas

---

## 🎉 Success!

**When properly configured:**
- ✅ Application connects to MongoDB Atlas cloud
- ✅ All 1,511 vectorstore documents accessible
- ✅ New data automatically saved to cloud
- ✅ No local MongoDB installation needed
- ✅ Data persists across server restarts
- ✅ Accessible from anywhere

**Your production deployment is now using cloud storage!** ☁️

---

## 📞 Support Resources

- **MongoDB Atlas Docs:** https://www.mongodb.com/docs/atlas/
- **Connection String Format:** https://www.mongodb.com/docs/manual/reference/connection-string/
- **Network Access Setup:** https://www.mongodb.com/docs/atlas/security/ip-access-list/
- **Troubleshooting:** https://www.mongodb.com/docs/atlas/troubleshoot-connection/

---

**Last Updated:** 2025-01-29  
**Target Server:** newcf3.cloudfuze.com (64.227.160.206)

