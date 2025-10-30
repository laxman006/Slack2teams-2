# Quick Start: MongoDB Vector Store

**Migrate your vector database from ChromaDB to MongoDB in 5 minutes!**

---

## 🎯 Why MongoDB?

- ✅ No more Git conflicts with binary SQLite files
- ✅ Scalable to millions of documents
- ✅ Cloud-ready with MongoDB Atlas
- ✅ Team-friendly (shared database)
- ✅ Your data: **1,510 embeddings** ready to migrate!

---

## 📋 Quick Setup

### 1. Start MongoDB (Choose One)

**Docker (Recommended):**
```bash
docker run -d --name mongodb -p 27017:27017 mongo:latest
```

**Windows:**
```bash
net start MongoDB
```

**macOS:**
```bash
brew services start mongodb-community
```

**Linux:**
```bash
sudo systemctl start mongod
```

### 2. Test Connection

```bash
python test_mongodb_vectorstore.py
```

### 3. Migrate Your Data

```bash
python migrate_vectorstore_to_mongodb.py
```

Select option **2** (clear and migrate)

### 4. Update Configuration

Edit your `.env` file:
```env
VECTORSTORE_BACKEND=mongodb
```

### 5. Restart Application

```bash
python server.py
```

---

## ✅ Done!

Your vector store is now running on MongoDB!

**See full guide:** [MONGODB-VECTORSTORE-GUIDE.md](MONGODB-VECTORSTORE-GUIDE.md)

---

## 🔄 Rollback (if needed)

Change `.env`:
```env
VECTORSTORE_BACKEND=chromadb
```

Restart application. Done!

---

## 📊 What You Get

| Before (ChromaDB) | After (MongoDB) |
|------------------|-----------------|
| SQLite file (273,463 lines) | MongoDB collection |
| Git conflicts 😢 | No conflicts 🎉 |
| Local only | Cloud-ready ☁️ |
| 1,510 embeddings | 1,510 embeddings |

---

## 🆘 Issues?

```bash
# Test MongoDB
python test_mongodb_vectorstore.py

# Check if MongoDB is running
docker ps | grep mongo

# View logs
docker logs mongodb
```

**Full troubleshooting:** [MONGODB-VECTORSTORE-GUIDE.md](MONGODB-VECTORSTORE-GUIDE.md)




