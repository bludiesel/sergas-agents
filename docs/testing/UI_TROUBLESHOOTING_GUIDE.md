# 🔧 Sergas Account Manager - UI Troubleshooting Guide

**System Configuration:**
- **Frontend**: Next.js 15.5.6 on http://localhost:7008
- **Backend**: FastAPI with GLM-4.6 on http://localhost:8008
- **AI Model**: GLM-4.6 via Z.ai (94% cost savings)

## 📋 Table of Contents

1. [Quick Diagnostics](#-quick-diagnostics)
2. [Common Issues & Solutions](#-common-issues--solutions)
3. [Service Recovery Procedures](#-service-recovery-procedures)
4. [Advanced Troubleshooting](#-advanced-troubleshooting)
5. [Performance Issues](#-performance-issues)
6. [Network & Connectivity](#-network--connectivity)
7. [GLM-4.6 Specific Issues](#-glm-46-specific-issues)
8. [Emergency Procedures](#-emergency-procedures)

---

## 🚀 Quick Diagnostics (First Steps)

### 1-Minute Health Check

```bash
# Check if services are running
curl -s http://localhost:7008 > /dev/null && echo "✅ Frontend OK" || echo "❌ Frontend DOWN"
curl -s http://localhost:8008/health > /dev/null && echo "✅ Backend OK" || echo "❌ Backend DOWN"

# Check processes
ps aux | grep -E "(next|node.*7008)" | grep -v grep > /dev/null && echo "✅ Next.js running" || echo "❌ Next.js not running"
```

### Browser Console Check

Open http://localhost:7008 and press F12:

```javascript
// Run in browser console
Promise.all([
  fetch('http://localhost:7008').then(r => r.ok),
  fetch('http://localhost:8008/health').then(r => r.ok)
]).then(([frontend, backend]) => {
  console.log(`Frontend: ${frontend ? '✅' : '❌'}`);
  console.log(`Backend: ${backend ? '✅' : '❌'}`);
});
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: Frontend Not Loading

**Symptoms:**
- Blank white page
- "Connection refused" error
- Page loads but shows error

**Solutions (in order):**

#### Solution A: Check if Next.js is Running
```bash
# Check process
ps aux | grep -E "next.*7008" | grep -v grep

# If not running, start it:
npm run dev -- --port 7008
```

#### Solution B: Port Conflict
```bash
# Check what's using port 7008
lsof -i :7008

# Kill process if needed
kill -9 <PID>

# Restart on different port
npm run dev -- --port 7009
# Then access http://localhost:7009
```

#### Solution C: Clear Browser Cache
1. Open Developer Tools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"
4. Or use incognito/private mode

#### Solution D: Check Node.js Version
```bash
# Verify Node.js 18+ is installed
node --version  # Should be 18.x or higher

# If outdated, update Node.js or use nvm
nvm use 18
npm run dev -- --port 7008
```

### Issue 2: Backend Not Responding

**Symptoms:**
- API calls fail
- "Connection refused" from frontend
- Health check returns error

**Solutions:**

#### Solution A: Check Backend Process
```bash
# Check if FastAPI is running
ps aux | grep -E "(uvicorn|fastapi|python.*main)" | grep -v grep

# If not running, start backend:
python src/main.py
# or
uvicorn src.main:app --host 0.0.0.0 --port 8008 --reload
```

#### Solution B: Check Dependencies
```bash
# Check if required packages are installed
pip list | grep -E "(fastapi|uvicorn|anthropic)"

# Install missing dependencies
pip install fastapi uvicorn python-multipart
```

#### Solution C: Environment Variables
```bash
# Check if .env.local exists and has required variables
cat .env.local

# Should contain:
# ANTHROPIC_API_KEY=...
# ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
# CLAUDE_MODEL=glm-4.6

# If missing, create it:
cat > .env.local << 'EOF'
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_API_KEY=your_api_key_here
CLAUDE_MODEL=glm-4.6
EOF
```

### Issue 3: CopilotKit Runtime Errors

**Symptoms:**
- Console shows TypeError: copilotRuntimeNextJSAppRouterEndpoint
- Sidebar doesn't load properly
- CopilotKit components show errors

**Current Status: Known Issue - Non-Critical**

**Workarounds:**

#### Option 1: Ignore and Continue
- The main application works despite CopilotKit errors
- Use the main interface without the AI sidebar
- Monitor for any fixes in future updates

#### Option 2: Disable CopilotKit (Temporary)
```typescript
// In app/layout.tsx, comment out CopilotProvider:
// <CopilotProvider agent="orchestrator">
//   {children}
// </CopilotProvider>

// Replace with:
{children}
```

#### Option 3: Check CopilotKit Version
```bash
# Check current version
npm list @copilotkit/react-core

# Update to latest (if available)
npm update @copilotkit/react-core @copilotkit/react-ui @copilotkit/runtime
```

### Issue 4: GLM-4.6 Connection Problems

**Symptoms:**
- Backend API returns model errors
- AI responses are slow or fail
- Cost reduction not working

**Solutions:**

#### Solution A: Verify API Configuration
```bash
# Test API directly
curl -X POST https://api.z.ai/api/anthropic/v1/messages \
  -H "Authorization: Bearer $(cat .env.local | grep ANTHROPIC_API_KEY | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.6",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
  }'
```

#### Solution B: Check Environment Variables
```bash
# Verify all variables are set
grep -E "(ANTHROPIC|CLAUDE_MODEL)" .env.local

# Should output:
# ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
# ANTHROPIC_API_KEY=your_key_here
# CLAUDE_MODEL=glm-4.6
```

#### Solution C: Test Backend GLM Integration
```bash
# Test backend GLM endpoint
curl -X POST http://localhost:8008/test-llm \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Respond with SUCCESS"}'
```

### Issue 5: Performance & Slow Loading

**Symptoms:**
- Page takes >10 seconds to load
- UI is sluggish or unresponsive
- High memory usage

**Solutions:**

#### Solution A: Check System Resources
```bash
# Check CPU and memory usage
top -p $(pgrep -f "next.*7008")

# Check Node.js memory limit
ps aux | grep next | grep -v grep
```

#### Solution B: Optimize Browser
1. Close unnecessary tabs
2. Clear browser cache
3. Disable browser extensions temporarily
4. Try a different browser

#### Solution C: Check Network
```bash
# Test network latency
ping localhost
ping 8.8.8.8

# Check if network issues exist
traceroute google.com
```

---

## 🔄 Service Recovery Procedures

### Complete System Restart

#### Step 1: Stop All Services
```bash
# Stop Next.js (if running)
pkill -f "next.*7008"

# Stop Backend (if running)
pkill -f "uvicorn\|fastapi\|python.*main"

# Verify all stopped
ps aux | grep -E "(next|uvicorn|fastapi)" | grep -v grep
```

#### Step 2: Clear Cache and Temp Files
```bash
# Clear Next.js cache
rm -rf .next

# Clear npm cache (optional)
npm cache clean --force

# Clear browser cache (manual step)
```

#### Step 3: Restart Services
```bash
# Start Backend first
cd /path/to/backend
python src/main.py &
# Wait 5 seconds

# Start Frontend
cd /path/to/frontend
npm run dev -- --port 7008 &
```

#### Step 4: Verify Services
```bash
# Wait 30 seconds, then test
sleep 30

curl -s http://localhost:8008/health && echo "✅ Backend OK"
curl -s http://localhost:7008 && echo "✅ Frontend OK"
```

### Partial Service Recovery

#### Restart Frontend Only
```bash
# Stop frontend
pkill -f "next.*7008"

# Clear cache
rm -rf .next

# Restart
npm run dev -- --port 7008
```

#### Restart Backend Only
```bash
# Stop backend
pkill -f "uvicorn\|fastapi\|python.*main"

# Restart
python src/main.py

# Verify
curl http://localhost:8008/health
```

---

## 🔍 Advanced Troubleshooting

### Debug Mode: Frontend

```bash
# Run Next.js with debug logging
DEBUG=* npm run dev -- --port 7008

# Or with specific debug info
DEBUG=next:* npm run dev -- --port 7008
```

### Debug Mode: Backend

```bash
# Run FastAPI with debug logging
uvicorn src.main:app --host 0.0.0.0 --port 8008 --reload --log-level debug

# Or with Python debugging
python -m debugpy --listen 5678 src/main.py
```

### Check Dependencies

#### Frontend Dependencies
```bash
# Check for missing/corrupt dependencies
npm ls

# Reinstall if needed
rm -rf node_modules package-lock.json
npm install

# Check for security vulnerabilities
npm audit
```

#### Backend Dependencies
```bash
# Check Python environment
pip list | grep -E "(fastapi|uvicorn|anthropic|requests)"

# Reinstall if needed
pip install -r requirements.txt

# Check for conflicts
pip check
```

### Port Analysis

```bash
# Check all ports in use
lsof -i :7000-7010
lsof -i :8000-8010

# Find free ports
netstat -tuln | grep :700
netstat -tuln | grep :800
```

---

## ⚡ Performance Issues

### Memory Usage Optimization

```bash
# Check Node.js memory usage
ps aux | grep next | awk '{print $4, $11}'

# If memory > 1GB, restart with increased limit
export NODE_OPTIONS="--max-old-space-size=4096"
npm run dev -- --port 7008
```

### Database/Cache Issues

```bash
# Clear any local cache
rm -rf .cache
rm -rf node_modules/.cache

# Check for database locks (if using local DB)
# Depends on your database type
```

### Network Optimization

```bash
# Test API response time
time curl http://localhost:8008/health

# Test with different endpoints
time curl -X POST http://localhost:8008/test-llm \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
```

---

## 🌐 Network & Connectivity

### Localhost Issues

```bash
# Test localhost resolution
nslookup localhost
ping -c 3 localhost

# Test 127.0.0.1 as alternative
curl http://127.0.0.1:7008
curl http://127.0.0.1:8008/health
```

### Firewall Issues

```bash
# On macOS, check firewall status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Temporarily disable for testing (use with caution)
# System Preferences → Security & Privacy → Firewall → Turn Off
```

### Proxy Issues

```bash
# Check for proxy environment variables
env | grep -i proxy

# Temporarily disable for testing
unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY
```

---

## 🤖 GLM-4.6 Specific Issues

### API Key Problems

```bash
# Test API key validity
curl -X POST https://api.z.ai/api/anthropic/v1/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "glm-4.6", "messages": [{"role": "user", "content": "test"}], "max_tokens": 5}'

# Expected: {"content": [{"type": "text", "text": "test"}], ...}
# If error: Check API key and account status
```

### Model Configuration

```bash
# Verify model is being used correctly
curl -X POST http://localhost:8008/model-info

# Should return GLM-4.6 configuration
```

### Cost Verification

```bash
# Check cost tracking (if implemented)
curl -X GET http://localhost:8008/api/cost-tracking

# Should show reduced costs vs Claude
```

---

## 🚨 Emergency Procedures

### Complete System Reset

```bash
# 1. Stop everything
pkill -f "next\|uvicorn\|fastapi\|python.*main"

# 2. Clear all caches
rm -rf .next node_modules/.cache
npm cache clean --force

# 3. Reset environment
cp .env.local.example .env.local.backup
# Edit .env.local with fresh credentials

# 4. Reinstall dependencies
npm install
pip install -r requirements.txt

# 5. Restart services
python src/main.py &
sleep 5
npm run dev -- --port 7008 &
```

### Fallback to Minimal Mode

If full system won't work:

```bash
# 1. Run backend only (no AI)
python -c "
from fastapi import FastAPI
app = FastAPI()

@app.get('/health')
def health():
    return {'status': 'minimal', 'model': 'none'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8008)
" &

# 2. Run simple frontend
npx create-next-app@latest temp-app --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm
cd temp-app
npm run dev -- --port 7009
```

### Data Recovery

```bash
# Check for any unsaved data
find . -name "*.log" -mtime -1
find . -name "*.json" -mtime -1

# Backup current state
cp -r . ../sergas-backup-$(date +%Y%m%d-%H%M%S)
```

---

## 📞 Getting Help

### Before Requesting Help:

1. **Run Quick Diagnostics** (see top of this guide)
2. **Check Error Logs**:
   ```bash
   # Frontend logs
   npm run dev 2>&1 | tee frontend.log

   # Backend logs
   python src/main.py 2>&1 | tee backend.log
   ```
3. **Document the Issue**:
   - What were you trying to do?
   - What happened instead?
   - Any error messages?
   - Browser and OS version?

### Information to Provide:

```bash
# Collect system information
echo "=== System Info ==="
uname -a
node --version
npm --version
python --version

echo "=== Service Status ==="
ps aux | grep -E "(next|uvicorn|fastapi)" | grep -v grep

echo "=== Port Usage ==="
lsof -i :7008
lsof -i :8008

echo "=== Environment ==="
env | grep -E "(NODE|PORT|ANTHROPIC)" | head -5
```

### Where to Get Help:

1. **Check this guide first** - solutions to 90% of issues
2. **Review error logs** - often contain the exact solution
3. **Search project issues** - someone may have had the same problem
4. **Contact development team** with the information above

---

## ✅ Troubleshooting Checklist

Print this checklist for systematic troubleshooting:

```
QUICK FIXES (Try these first):
□ Restart browser and clear cache
□ Check http://localhost:7008 loads
□ Check http://localhost:8008/health responds
□ Restart both services
□ Try different browser

ENVIRONMENT CHECKS:
□ Node.js version 18+ installed
□ Python 3.12+ installed
□ .env.local configured correctly
□ Dependencies installed

NETWORK CHECKS:
□ Localhost resolves correctly
□ Ports 7008 and 8008 are free
□ No firewall blocking
□ No proxy interference

SERVICE CHECKS:
□ Next.js process running
□ FastAPI process running
□ GLM-4.6 API accessible
□ CopilotKit errors noted (if present)

ADVANCED (if basic fixes don't work):
□ Clear all caches and restart
□ Check for dependency conflicts
□ Verify environment variables
□ Test API endpoints directly
□ Check system resources

ESCALATION (if nothing works):
□ Collect all error logs
□ Document steps taken
□ Provide system information
□ Contact support with details
```

**Remember**: Most issues are resolved by restarting services and clearing cache. The system is designed to be resilient and recoverable.

---

**Last Updated**: January 20, 2025
**System Version**: Sergas Account Manager v1.0 with GLM-4.6 integration