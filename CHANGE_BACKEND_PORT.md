# How to Change Backend Port

Quick guide to run your backend on a different port.

---

## 📝 Steps to Change Port

### Step 1: Update Backend `.env` File

Edit `backend/.env` and change the `API_PORT` value:

```env
# API Configuration
API_PORT=8080  # Change to your desired port (e.g., 8080, 5000, 3001, etc.)
```

### Step 2: Update Frontend `.env` File

Edit `frontend/.env` and update the `REACT_APP_API_URL` to match:

```env
REACT_APP_API_URL=http://localhost:8080/api/v1  # Match the port from backend
```

### Step 3: Restart Both Servers

```bash
# Stop both servers (Ctrl+C in each terminal)

# Restart backend
cd backend
python start_backend.py

# Restart frontend (in new terminal)
cd frontend
npm start
```

---

## 🎯 Examples

### Example 1: Run Backend on Port 5000

**backend/.env:**
```env
API_PORT=5000
```

**frontend/.env:**
```env
REACT_APP_API_URL=http://localhost:5000/api/v1
```

### Example 2: Run Backend on Port 3001

**backend/.env:**
```env
API_PORT=3001
```

**frontend/.env:**
```env
REACT_APP_API_URL=http://localhost:3001/api/v1
```

### Example 3: Default Port 8000

**backend/.env:**
```env
API_PORT=8000
```

**frontend/.env:**
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

---

## ✅ Verification

After changing the port, verify everything works:

1. **Check Backend Startup Message**
   ```
   🚀 Starting WellnessWay Backend...
   📍 Database: postgresql://***@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres
   🔴 Redis: redis://localhost:6379/0
   🌐 Port: 8080  ← Should show your new port
   ```

2. **Test Backend Health**
   - Open browser: `http://localhost:YOUR_PORT/health`
   - Should return: `{"status":"healthy"}`

3. **Test API Docs**
   - Open browser: `http://localhost:YOUR_PORT/docs`
   - Swagger UI should load

4. **Test Frontend Connection**
   - Open frontend: `http://localhost:3000`
   - Try logging in with Google
   - Check browser console for any connection errors

---

## 🔧 Port Selection Tips

### Good Port Choices:
- **8000** - Default, commonly used for APIs
- **8080** - Alternative HTTP port
- **5000** - Flask/Python convention
- **3001** - If 3000 is taken by frontend
- **4000** - GraphQL convention

### Avoid These Ports:
- **3000** - Usually used by React frontend
- **80** - Requires admin/root privileges
- **443** - Requires admin/root privileges
- **5432** - PostgreSQL default
- **6379** - Redis default

### Port Already in Use?

If you get an error like `Address already in use`:

**Windows:**
```bash
# Find what's using the port
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Mac/Linux:**
```bash
# Find what's using the port
lsof -i :8000

# Kill the process (replace PID with actual process ID)
kill -9 <PID>
```

---

## 🚨 Important Notes

1. **Both files must match**: The port in `backend/.env` must match the port in `frontend/.env`

2. **Restart required**: Changes to `.env` files require restarting the servers

3. **Frontend rebuild**: If frontend doesn't pick up changes, try:
   ```bash
   cd frontend
   rm -rf node_modules/.cache
   npm start
   ```

4. **CORS issues**: If you get CORS errors after changing ports, the backend should automatically allow `localhost` on any port in development mode

5. **Production**: In production, you'll typically use port 80 (HTTP) or 443 (HTTPS) behind a reverse proxy like Nginx

---

## 📚 Related Files

Files that handle port configuration:

- `backend/.env` - Port configuration
- `backend/start_backend.py` - Reads `API_PORT` from `.env`
- `backend/app/core/config.py` - Settings class with `api_port` field
- `frontend/.env` - API URL configuration
- `frontend/src/services/api.ts` - Uses `REACT_APP_API_URL`

---

## 🎉 You're Done!

Your backend is now running on your custom port!

Check the startup message to confirm:
```
🌐 Port: YOUR_PORT
```
