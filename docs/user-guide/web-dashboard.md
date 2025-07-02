# Web Dashboard User Guide

The AI Orchestration System includes a comprehensive web dashboard for managing projects, monitoring system health, and configuring settings through an intuitive interface.

## 🌐 Accessing the Dashboard

### Starting the Web Service

```bash
# Method 1: Using main.py
python main.py serve --port 8000

# Method 2: Direct uvicorn
uvicorn ai_orchestrator.web.app:create_app --factory --host 0.0.0.0 --port 8000

# Method 3: Docker
docker-compose up -d
```

**Access URLs:**
- **Main Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/api/health

## 🏠 Dashboard Overview

### Main Dashboard Features

The dashboard provides a comprehensive view of your AI orchestration system:

#### **Quick Stats Cards**
- 📊 **Active Projects** - Currently running workflows
- ✅ **Completed Today** - Successfully finished projects
- ⏱️ **Average Duration** - Typical workflow completion time
- 🤖 **API Calls** - Total AI service interactions

#### **System Health Indicator**
Real-time status showing:
- 🟢 **Healthy** - All systems operational
- 🟡 **Warning** - Minor issues detected  
- 🔴 **Unhealthy** - Critical problems require attention

#### **Quick Project Creation**
Streamlined form to start new AI projects:
```
Project Description: [Text area for project requirements]
☑️ Initialize Git repository
☐ Push to GitHub
[Start AI Orchestration Button]
```

## 🚀 Creating Projects

### Step-by-Step Project Creation

1. **Navigate to Dashboard** - Open http://localhost:8000
2. **Enter Description** - Describe what you want to build
3. **Configure Options**:
   - ✅ **Git Integration** - Automatically create repository
   - ☐ **GitHub Publishing** - Push to GitHub (requires token)
4. **Start Orchestration** - Click the "Start AI Orchestration" button
5. **Monitor Progress** - Watch real-time updates

### Project Description Examples

**Good Descriptions:**
```
✅ "Create a todo application with user authentication, CRUD operations, 
   and responsive design using React and Node.js"

✅ "Build an e-commerce platform with product catalog, shopping cart, 
   payment integration, and admin dashboard"

✅ "Develop a blog platform with user management, content creation, 
   comments, and SEO optimization"
```

**Poor Descriptions:**
```
❌ "Make an app" (too vague)
❌ "Website" (lacks specificity)
❌ "Something with AI" (no clear requirements)
```

### Real-Time Progress Monitoring

Once started, you'll see:

#### **Progress Bar**
Visual indicator showing completion percentage (0-100%)

#### **Phase Updates**
Current workflow phase with descriptions:
- 🔄 **Requirements Refinement** - GPT analyzing and clarifying needs
- 🏗️ **Technical Planning** - Claude & Gemini creating architectures
- ⚖️ **Plan Comparison** - Identifying conflicts and agreements
- 🗳️ **Voting** - Democratic decision making process
- 💻 **Implementation** - Code generation in progress
- 🧪 **Testing** - Test suite creation
- 📁 **Finalization** - Project files being organized

#### **Execution Time**
Live timer showing how long the workflow has been running

#### **Agent Activity**
Visual indicators showing which AI agents are currently active

## 📊 Projects Page

### Project Management Interface

Access via sidebar: **Projects** → Comprehensive project listing

#### **Project List View**
```
┌─────────────────────────────────────────────────────────┐
│ Project: Todo Application with Auth                     │
│ Status: [●●●●●●●●○○] 80% Complete                       │
│ Phase: Implementation                                   │
│ Started: 2024-01-01 14:30:22                          │
│ Duration: 12m 34s                                      │
│ [View Details] [Download] [Stop]                       │
└─────────────────────────────────────────────────────────┘
```

#### **Project Details Modal**
Click "View Details" for comprehensive information:

**Workflow Timeline:**
- ✅ Requirements Refinement (45s)
- ✅ Technical Planning (2m 34s)
- ✅ Plan Comparison (1m 12s)
- ✅ Voting (30s)
- 🔄 Implementation (ongoing)
- ⏳ Testing (pending)
- ⏳ Finalization (pending)

**Generated Artifacts:**
- 📝 Refined Requirements Document
- 🏗️ Backend Architecture Plan (Claude)
- 🎨 Frontend Design Plan (Gemini)
- ⚖️ Technical Decisions Log

#### **Project Actions**

**Download Project:**
- ZIP file containing all generated code
- Organized folder structure
- Documentation and setup instructions
- Git repository (if enabled)

**Stop Project:**
- Gracefully halt execution
- Save partial progress
- Generate summary report

**Share Project:**
- GitHub repository link (if published)
- Public project showcase
- Collaboration features

## 📈 Monitoring Page

### System Performance Dashboard

Access via sidebar: **Monitoring** → Real-time system metrics

#### **Performance Metrics Chart**
Interactive doughnut chart showing:
- 🟢 **Successful Workflows** - Completed without errors
- 🔴 **Failed Workflows** - Encountered critical issues
- 🔵 **In Progress** - Currently executing

#### **API Performance Tracking**
Real-time metrics for each AI service:

```
OpenAI GPT-4:
├── Response Time: 2.3s avg
├── Success Rate: 98.5%
├── Requests/Hour: 45
└── Status: 🟢 Healthy

Anthropic Claude:
├── Response Time: 3.1s avg  
├── Success Rate: 96.2%
├── Requests/Hour: 38
└── Status: 🟢 Healthy

Google Gemini:
├── Response Time: 2.8s avg
├── Success Rate: 94.7%
├── Requests/Hour: 42
└── Status: 🟡 Warning
```

#### **System Resource Monitoring**
- **Memory Usage** - Current RAM utilization
- **CPU Usage** - Processing load
- **Disk Space** - Storage consumption
- **Network Activity** - API communication volume

#### **Alert History**
Recent system alerts and warnings:
```
🟡 2024-01-01 14:45:23 - High API response time: Claude (4.2s)
🔴 2024-01-01 14:30:15 - Gemini API rate limit exceeded
🟢 2024-01-01 14:15:08 - All systems operational
```

#### **Health Check Results**
Detailed system validation:

**API Keys Status:**
- ✅ OpenAI: Valid and active
- ✅ Anthropic: Valid and active  
- ❌ Google: Invalid or expired

**Dependencies:**
- ✅ GitPython: Available
- ✅ PyGithub: Available
- ⚠️ FastAPI: Available (outdated version)

**Configuration:**
- ✅ Output directory: Writable
- ✅ Workflow config: Valid YAML
- ✅ Environment: Properly configured

## ⚙️ Settings Page

### System Configuration Management

Access via sidebar: **Settings** → Configuration interface

#### **API Configuration**
Secure management of AI service credentials:

```
OpenAI Configuration:
├── API Key: [●●●●●●●●●●] (Hidden)
├── Model: gpt-4
├── Max Tokens: 4000
├── Temperature: 0.7
└── [Test Connection] [Update]

Anthropic Configuration:
├── API Key: [●●●●●●●●●●] (Hidden)
├── Model: claude-3-sonnet
├── Max Tokens: 4000
└── [Test Connection] [Update]
```

#### **Workflow Settings**
Customize orchestration behavior:

**Voting & Consensus:**
- ☑️ Enable voting when agents disagree
- ☑️ Require consensus for major decisions
- ☑️ Allow GPT tie-breaking votes
- Max voting rounds: [3]

**Performance Settings:**
- Max concurrent agents: [3]
- Session timeout: [3600] seconds
- API retry attempts: [3]
- Rate limit buffer: [10%]

#### **Git Integration**
Repository and version control settings:

**Local Git:**
- ☑️ Initialize Git repositories
- ☑️ Auto-commit generated code
- Commit message template: `AI Generated: {project_name}`

**GitHub Integration:**
- GitHub Token: [●●●●●●●●●●] (Hidden)
- ☐ Auto-push to GitHub
- ☑️ Create public repositories
- ☐ Add repository topics

#### **Output Configuration**
Control how projects are generated:

**File Organization:**
- Output directory: `/app/output`
- Template directory: `/app/templates`
- Archive completed projects: ☑️

**Code Generation:**
- Include documentation: ☑️
- Generate Docker configs: ☑️
- Create CI/CD workflows: ☐
- Add security scanning: ☐

#### **Notification Settings**
Configure alerts and updates:

**Email Notifications:**
- Project completion: ☐
- System alerts: ☐
- Weekly reports: ☐

**In-App Notifications:**
- Workflow updates: ☑️
- System health alerts: ☑️
- Performance warnings: ☑️

## 🔄 Real-Time Features

### WebSocket Live Updates

The dashboard uses WebSocket connections for real-time updates:

#### **Live Progress Tracking**
- Progress bars update every 2 seconds
- Phase transitions shown immediately
- Agent status changes in real-time

#### **System Health Monitoring** 
- Health indicator updates every 30 seconds
- Metric charts refresh automatically
- Alert notifications appear instantly

#### **Multi-Tab Synchronization**
- Changes made in one tab reflect in others
- Consistent state across browser windows
- Automatic reconnection on network issues

### Browser Notifications

Enable browser notifications for:
- ✅ Project completion alerts
- ⚠️ System health warnings  
- 📊 Performance threshold breaches
- 🔔 Custom notification preferences

## 🎨 Interface Customization

### Theme Options
- 🌞 **Light Mode** - Default bright interface
- 🌙 **Dark Mode** - Easy on the eyes
- 🎨 **Auto Mode** - Follows system preference

### Dashboard Layout
- 📊 **Compact View** - More information per screen
- 📱 **Mobile Responsive** - Optimized for tablets/phones
- 🖥️ **Desktop Optimized** - Multi-column layouts

### Accessibility Features
- ♿ **Screen Reader Support** - ARIA labels and descriptions
- ⌨️ **Keyboard Navigation** - Full keyboard accessibility
- 🔍 **High Contrast Mode** - Enhanced visibility
- 📏 **Scalable Text** - Adjustable font sizes

## 💡 Pro Tips

### Efficient Project Management
1. **Use Descriptive Names** - Include technology preferences
2. **Monitor Early Phases** - Catch issues during planning
3. **Save Templates** - Reuse successful project patterns
4. **Regular Health Checks** - Maintain system performance

### Performance Optimization
1. **API Key Rotation** - Prevent rate limiting
2. **Batch Operations** - Group similar projects
3. **Resource Monitoring** - Watch system limits
4. **Clean Output Directory** - Remove old projects

### Troubleshooting
1. **Check Logs** - View detailed execution information
2. **Verify API Keys** - Test connections regularly
3. **Monitor Metrics** - Identify performance trends
4. **Update Dependencies** - Keep system current

The web dashboard provides a complete interface for managing your AI orchestration workflows with real-time monitoring, comprehensive configuration, and intuitive project management capabilities.