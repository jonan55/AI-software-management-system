# 🚀 NexusAI - AI-Powered Software Management System

A modern, production-grade, full-stack **AI-Powered Software Management System** built with **Python Flask**, **SQLite3**, **Chart.js**, **Lucide Icons**, and custom heuristic machine-assisted intelligence.

---

## 🌟 Key Highlights & Features

### 1. 📊 Executive Dashboard
- **Real-Time Dynamic Metrics directly from SQLite**: Total Projects, Active Projects, Completed Projects, Pending Tasks, Total Team Members, Overall Progress %.
- **Chart.js Visualizations**:
  - Live Doughnut Chart of Project Status distribution (`In Progress`, `Completed`, `Not Started`, `On Hold`).
  - Bar Chart of Task Priority breakdown (`Urgent`, `High`, `Medium`, `Low`).
- **Upcoming Deadlines Tracker**: Ranked by urgency with deadline countdown chips.
- **System Activity Stream**: Live database audit log tracking all CRUD operations.

### 2. 📁 Project Management
- Full CRUD operations with instant SQLite persistence.
- Track project milestones, start/end dates, budget, priority, status, and lead architect.
- Dynamic project progress calculation: derived automatically from child tasks.
- Project Details modal with nested checklist of all subtasks.

### 3. ✅ Task Management & Interactive Kanban
- Switch between interactive **Kanban Board** (`To Do`, `In Progress`, `Review`, `Completed`) and **List Table**.
- Real-time status transitions with one-click selector.
- Filter tasks by project, status, priority, and text search.
- Priority levels: `Low`, `Medium`, `High`, `Urgent`.

### 4. 👥 Team Management
- Roster tracking across Engineering, Design, DevOps, QA, and Product.
- Individual task completion throughput, active backlog count, and workload health indicator (`Overloaded`, `Optimal`, `Available`).
- Department filters, contact info, and profile management.

### 5. 🤖 NexusAI Autonomous Assistant & Chatbot
- **Project Health Diagnostics**: Identifies delayed projects and analyzes velocity slippage.
- **Smart Task Prioritization**: Heuristic multi-factor scoring formula balancing urgency, deadlines, and project risk.
- **Deadline Prediction**: Velocity burn rate analysis estimating exact completion dates and probability of missed delivery.
- **Conversational Chatbot**: Natural language query engine over live SQLite tables. Responds to:
  - *"Which projects are currently delayed?"*
  - *"Which tasks have the highest priority?"*
  - *"What is our overall project completion rate?"*
  - *"Which project needs immediate attention?"*
  - *"Who on the team has the heaviest workload?"*

### 6. 📈 Reports, Analytics & CSV Export
- Date range filtering (`start_date` to `end_date`).
- One-click CSV exports for Projects, Tasks, Team, and Delayed Project Audits.
- Interactive Team Productivity velocity charts.

### 7. 🎨 Modern SaaS UX/UI
- **Dark & Light Mode Toggle**: Seamless, high-contrast, persisted in `localStorage`.
- Navy Blue (`#0B0F19`), Slate (`#131B2E`), Indigo/Purple accents (`#6366F1`, `#8B5CF6`).
- Fully responsive across Desktop, Tablet, and Mobile with collapsible drawer.
- Toast notifications for user feedback and error handling.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.13, Flask 3.1
- **Database**: SQLite3 (`software_management.db`) with `PRAGMA foreign_keys = ON;`
- **Frontend**: HTML5, Modern CSS3 (CSS Custom Properties & Flexbox/Grid), Vanilla JavaScript (ES6+)
- **Charts**: Chart.js
- **Icons**: Lucide Icons
- **Security**: Parameterized SQL queries, password hashing (`werkzeug.security`)

---

## 📂 Project Architecture

```
software-management-system/
│
├── app.py                     # Flask backend & REST API endpoints
├── database.py                # SQLite connection pool & query helpers
├── init_db.py                 # SQLite schema initialization & demo seeder
├── ai_engine.py               # AI heuristic analytics & conversational chatbot
├── requirements.txt           # Python dependencies (Flask, Werkzeug)
├── software_management.db     # SQLite relational database
│
├── static/
│   ├── css/
│   │   └── style.css          # Responsive design system & themes
│   └── js/
│       └── app.js             # Reactive client, charts, modals, chatbot
│
├── frontend/
│   ├── index.html             # Standalone entrypoint
│   ├── style.css              # Frontend styling
│   └── script.js              # Frontend logic
│
├── templates/
│   ├── base.html              # Shell template with sidebar, navbar, modals
│   ├── dashboard.html         # Main dashboard view
│   ├── projects.html          # Project management view
│   ├── tasks.html             # Kanban & task list view
│   ├── team.html              # Team members view
│   ├── ai_assistant.html      # AI diagnostics & chatbot interface
│   └── analytics.html         # Reports, analytics & CSV exports
│
└── README.md                  # System documentation
```

---

## ⚡ Quick Start & Running Locally in VS Code

### Step 1: Open Terminal in VS Code
Open your terminal in the project directory:
```bash
cd /path/to/project
```

### Step 2: Set up Virtual Environment & Dependencies
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Initialize Database & Seed Demo Data
*(Note: `app.py` also runs this automatically on startup)*
```bash
python init_db.py
```

### Step 4: Run the Application
```bash
python app.py
```

### Step 5: Open in Browser
Visit:
👉 **`http://127.0.0.1:5050`** or **`http://localhost:5050`**

Default Administrator Credentials:
- **Username:** `admin`
- **Password:** `admin123`

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard` | Aggregated metrics, charts, upcoming deadlines & recent activities |
| `GET` | `/api/projects` | Fetch all projects with progress % and assignees |
| `POST` | `/api/projects` | Create a new project |
| `GET` | `/api/projects/<id>` | Fetch project details with nested subtasks |
| `PUT` | `/api/projects/<id>` | Update an existing project |
| `DELETE` | `/api/projects/<id>` | Delete project (cascades to child tasks) |
| `GET` | `/api/tasks` | Fetch tasks with filter parameters |
| `POST` | `/api/tasks` | Create a new task |
| `PUT` | `/api/tasks/<id>` | Update task status, priority, or details |
| `DELETE` | `/api/tasks/<id>` | Delete a task |
| `GET` | `/api/team` | Fetch team roster and individual throughput |
| `POST` | `/api/team` | Add a new team member |
| `PUT` | `/api/team/<id>` | Update team member profile |
| `DELETE` | `/api/team/<id>` | Remove team member |
| `POST` | `/api/ai/analyze` | Run AI project health, task ranking & deadline forecasts |
| `POST` | `/api/ai/chat` | Send query to conversational AI assistant |
| `GET` | `/api/reports` | Retrieve filtered reports and delayed project audit |
| `GET` | `/api/export/<type>`| Download CSV (`projects`, `tasks`, `team`, `delayed`) |

---

## 🛡️ Database Constraints & Integrity
- All connections execute `PRAGMA foreign_keys = ON;`.
- Tables use `AUTOINCREMENT` primary keys and relational foreign keys (`ON DELETE CASCADE` for tasks and junction tables).
- SQL statements use parameterized placeholders (`?`) preventing SQL injection.
