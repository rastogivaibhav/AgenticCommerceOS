# ACOS Control Plane - User Onboarding Guide

**Get up and running with the ACOS Control Plane in 30 minutes**

## Table of Contents
1. [First Login](#first-login)
2. [Dashboard Overview](#dashboard-overview)
3. [Your First Workflow](#your-first-workflow)
4. [Running Your First Experiment](#running-your-first-experiment)
5. [Viewing Analytics](#viewing-analytics)
6. [Next Steps](#next-steps)

---

## First Login

### Step 1: Access the Application

Open your browser and navigate to your ACOS Control Plane URL:
- **Local Development:** `http://localhost:5173`
- **Production:** `https://yourdomain.com`

You should see the ACOS Control Plane login or home screen.

### Step 2: Familiarize with the Interface

The application has four main areas:

**Header** (top of screen)
- ACOS Control Plane logo on the left
- Theme toggle (sun/moon icon) on the right
- Mobile menu (hamburger icon) on smaller screens

**Sidebar** (left side)
- Navigation menu with three main sections:
  1. **Workflow Builder** - Create and manage workflows
  2. **Experiments** - Run A/B experiments
  3. **Analytics** - View performance dashboards
- Responsive design: collapses to mobile overlay on small screens

**Main Content Area** (center/right)
- Changes based on selected navigation item
- Responsive layout adjusts for mobile, tablet, and desktop

**Dark/Light Mode**
- Click the sun/moon icon in the header to toggle theme
- Your preference is automatically saved

---

## Dashboard Overview

### Home Page

When you first access ACOS Control Plane, you'll see the home page with:

**Header Section**
- Application title: "ACOS Control Plane"
- Subtitle: "Manage AI agent workflows and run experiments"
- Navigation menu with three items: Workflow Builder, Experiments, Analytics

**Navigation Pattern**
- Click any navigation item in the sidebar to switch views
- Current page is highlighted in the sidebar
- Active page state persists as you navigate

### Responsive Design

The interface adapts to your screen size:

**Mobile (375px-640px)**
- Hamburger menu button in header
- Single-column layout
- Touch-optimized buttons and controls
- Sidebar accessible via overlay menu

**Tablet (641px-1024px)**
- Two-column layout begins
- Sidebar remains visible
- Controls sized for touch interaction

**Desktop (1025px+)**
- Full three-column layout (sidebar, content, optional details)
- Sidebar always visible
- Mouse-optimized interactions

### Theme Preferences

**Dark Mode**
- Professional dark gray backgrounds
- White text for high contrast
- Accent colors remain vibrant
- Easier on eyes in low-light environments

**Light Mode**
- Clean white backgrounds
- Dark text for readability
- Subtle gray accents
- Ideal for print and bright environments

**Automatic Detection**
- On first visit, your system preference is detected
- If you have no saved preference, the app uses your OS setting
- Toggle with the sun/moon icon in the header to override

---

## Your First Workflow

### What is a Workflow?

A workflow is a sequence of steps that your AI agent follows. Each step performs a specific task:

- **Input** - Accept input data
- **Agent Call** - Call an AI agent with parameters
- **Data Transform** - Transform or process data
- **Decision** - Make conditional decisions
- **Output** - Return results

### Creating Your First Workflow

**Step 1: Navigate to Workflow Builder**

Click "Workflow Builder" in the sidebar. You'll see:

- **Empty Canvas** (center) - Where your workflow steps appear
- **Tool Panel** (left side) - Buttons to add different step types
- **Header** with save/deploy buttons

**Step 2: Add Your First Step**

Click the "Input" button in the Tool Panel. An "Input" step card appears on the canvas with:
- Step name (editable)
- Step type badge ("input")
- JSON configuration area

**Step 3: Configure the Step**

Click the input configuration area and add JSON (example):
```json
{
  "field_name": "user_query",
  "field_type": "string",
  "required": true
}
```

**Step 4: Add More Steps**

Click "Agent Call" button to add an agent call step. Configure it:
```json
{
  "agent_type": "search",
  "timeout": 30,
  "retries": 2
}
```

Continue adding steps following this pattern.

**Step 5: Save Your Workflow**

Click the "Save Draft" button in the header. Your workflow is saved locally.

### Workflow State

**Draft** - Your workflow is saved but not active
- You can edit and refine it
- No production runs use this version
- Save frequently with the "Save Draft" button

**Published** - Your workflow is ready for experiments and production
- Locked for editing
- Used by active experiments
- Click "Deploy" to publish a draft

### Example Simple Workflow

A common three-step workflow:

1. **Input Step**
   - Accepts user query
   - JSON: `{"field": "query", "type": "string"}`

2. **Agent Call Step**
   - Processes query with AI agent
   - JSON: `{"agent": "search", "timeout": 30}`

3. **Output Step**
   - Returns results
   - JSON: `{"format": "json", "include_metadata": true}`

---

## Running Your First Experiment

### What is an Experiment?

An experiment compares two versions (variants) of your workflow to see which performs better.

**Variant A** - Your original workflow configuration
**Variant B** - A modified version with different parameters

The system runs both versions with the same inputs and compares results.

### Creating Your First Experiment

**Step 1: Navigate to Experiments**

Click "Experiments" in the sidebar. You'll see:
- List of past experiments (if any)
- "Create Experiment" button
- Form for new experiment

**Step 2: Fill Experiment Details**

**Name Your Experiment**
- Enter a descriptive name
- Example: "Search Agent Speed Test"
- This helps you identify experiments later

**Select Workflow**
- Choose from your published workflows
- The dropdown shows all available workflows
- Only published workflows appear

**Step 3: Configure Sample Size**

Enter the number of test samples:
- Minimum: 10 (for quick testing)
- Recommended: 100 (for statistical significance)
- Larger samples give more reliable results

### Configure Variants

**Variant A Configuration**

This is typically your baseline. Example for a search workflow:
```json
{
  "search_depth": "standard",
  "timeout": 30,
  "include_sources": true
}
```

Click "+ Add Parameter" to add each configuration item.

**Variant B Configuration**

This is your test variant. Make specific changes:
```json
{
  "search_depth": "deep",
  "timeout": 60,
  "include_sources": false
}
```

Test one or two variables at a time for clear results.

**Step 4: Run Experiment**

Click "Run Experiment" button. The system will:

1. Start the experiment with your sample size
2. Run Variant A on the first half of samples
3. Run Variant B on the second half of samples
4. Show real-time progress

### Understanding Results

**Results Card Display**

After completion, you'll see:

**Variant A Score** - A card showing:
- Average score (0-100)
- Total runs performed
- Average cost per run

**Variant B Score** - A card showing:
- Average score (0-100)
- Total runs performed
- Average cost per run

**Winner** - The system automatically determines:
- Which variant had the higher score
- If the difference is statistically significant
- Recommendation: Deploy winner to production

### Example Experiment Flow

1. Create "Agent Timeout Test"
2. Select published "Search Workflow"
3. Set sample size to 50
4. Configure Variant A: timeout 30 seconds
5. Configure Variant B: timeout 60 seconds
6. Click "Run Experiment"
7. Wait for completion (typically 2-5 minutes)
8. Review results: Which timeout performed better?

---

## Viewing Analytics

### Analytics Dashboard

Click "Analytics" in the sidebar to access comprehensive performance metrics.

### Key Metrics Cards

The dashboard displays four primary metrics at the top:

**Total Runs**
- How many times workflows have executed
- Cumulative across all workflows
- Helpful for understanding usage

**Average Score**
- Mean performance score (0-100)
- Calculated from completed runs
- Higher is better

**Total Cost**
- Sum of all execution costs
- In your configured currency
- Helps with budget tracking

**Success Rate**
- Percentage of runs that completed successfully
- Example: 95% of runs succeeded
- Lower than 100% may indicate issues

### Charts and Graphs

**Daily Activity Line Chart**
- X-axis: Dates (last 7-30 days depending on data)
- Y-axis: Number of runs per day
- Hover over points to see exact values
- Helps identify usage patterns

**Workflow Performance Bar Chart**
- Shows performance comparison across workflows
- Each workflow has a bar
- Height represents average score
- Identifies best-performing workflows

### Metrics Table

Detailed table showing per-workflow metrics:

**Columns:**
- Workflow Name - Name of the workflow
- Status - Active/Inactive
- Total Runs - Number of executions
- Avg Score - Average performance
- Total Cost - Sum of costs
- Success Rate - % of successful runs

**Sorting:**
- Click column headers to sort
- Common sorts: highest score, highest cost, most runs

**Pagination:**
- Navigate between pages for large datasets
- Shows results per page (25, 50, 100)

### Exporting Data

**Export Button**
- Located at bottom right of dashboard
- Click to open export dialog

**Export Formats**
- **CSV** - For spreadsheets (Excel, Google Sheets)
- **JSON** - For API integration or data pipelines

**Exported Data Includes**
- All metrics table data
- Workflow names, scores, costs, success rates
- Timestamp for audit trail
- Filename format: `analytics-data-YYYY-MM-DD.csv`

### Using Analytics

**Identify Issues**
- Low success rate indicates problems
- Check specific workflow's metrics
- Review recent runs for errors

**Optimize Costs**
- High total cost suggests expensive operations
- Compare costs per workflow
- Adjust parameters in experiments

**Track Trends**
- Daily activity shows usage patterns
- Performance charts reveal top workflows
- Use data to plan improvements

---

## Common User Flows

### Flow 1: Create and Test a Workflow

1. **Navigate** to Workflow Builder
2. **Add** Input, Agent Call, Output steps
3. **Configure** each step with JSON parameters
4. **Save** as draft
5. **Review** in editor
6. **Deploy** to make it live

Time: 5-10 minutes

### Flow 2: Run an A/B Experiment

1. **Navigate** to Experiments
2. **Create** new experiment
3. **Select** published workflow
4. **Configure** Variant A (baseline)
5. **Configure** Variant B (test)
6. **Set** sample size (50-100)
7. **Run** experiment
8. **Review** results
9. **Deploy** winner (if applicable)

Time: 10-15 minutes (depending on sample size)

### Flow 3: Monitor Performance

1. **Navigate** to Analytics
2. **View** metrics cards
3. **Review** daily activity chart
4. **Compare** workflow performance
5. **Analyze** metrics table for issues
6. **Export** data for reporting

Time: 5-10 minutes

---

## Tips and Best Practices

### Workflow Design

**Keep Steps Simple**
- Each step should do one thing
- Complex workflows are harder to debug
- Use Data Transform steps to prepare inputs

**Use Meaningful Names**
- Instead of "Step 1", use "Fetch User Data"
- Helps others understand your workflows
- Makes analytics dashboards clearer

**Test Incrementally**
- Add one step at a time
- Save frequently with "Save Draft"
- Test each addition before adding more

### Experiments

**Control One Variable**
- Change only one parameter between variants
- Multiple changes make results unclear
- Example: test timeout OR search depth, not both

**Use Adequate Samples**
- 10 samples: Quick testing only
- 50 samples: Good for most cases
- 100+ samples: For critical decisions

**Document Your Tests**
- Use descriptive experiment names
- Include what you're testing in the name
- Example: "Search Timeout Test v2" instead of "Test 2"

### Analytics

**Regular Reviews**
- Check analytics weekly
- Look for unexpected trends
- Investigate success rate drops

**Export for Records**
- Export weekly/monthly
- Store in documentation system
- Useful for reporting and compliance

**Benchmark Performance**
- Track average score over time
- Compare against previous periods
- Set performance targets

---

## Keyboard Navigation

ACOS Control Plane supports keyboard navigation for accessibility:

**Navigation**
- `Tab` - Move focus between elements
- `Shift+Tab` - Move focus backward
- `Enter` - Activate buttons and links
- `Escape` - Close dialogs and menus

**Theme Toggle**
- `Alt+T` - Toggle between dark and light modes

**Forms**
- `Tab` - Move between form fields
- `Space` - Check/uncheck checkboxes
- `Enter` - Submit forms

---

## Getting Help

### If You're Stuck

1. **Check** the navigation items - Are you in the right section?
2. **Review** the sidebar - Does it show what you expect?
3. **Check** theme - Can you read the text? Try toggling light mode
4. **Refresh** the page - Sometimes UI state needs reset

### Common Issues

**"I can't see my workflow after saving"**
- Check sidebar - Are you on Workflow Builder?
- Refresh the page with Ctrl+R (or Cmd+R on Mac)
- Check browser console for errors

**"Export button is disabled"**
- Navigate to Analytics page
- Scroll to bottom of dashboard
- Export button appears after metrics load

**"Dark mode looks strange"**
- Try toggling theme twice
- Clear browser cache and refresh
- Try different browser if issue persists

### Documentation

- **[README.md](./README_COMPLETE.md)** - Product overview and features
- **[USER_GUIDE.md](./USER_GUIDE.md)** - Detailed feature documentation
- **[API.md](./API.md)** - API endpoint reference for developers
- **[TESTING.md](./TESTING.md)** - How to run tests
- **[INSTALLATION.md](./INSTALLATION.md)** - Setup instructions
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Production deployment guide

---

## Next Steps

### For Business Analysts

1. **Learn Workflows** - Understand workflow structure and parameters
2. **Create Baseline** - Design your first workflow
3. **Run Experiments** - Test different configurations
4. **Analyze Results** - Use analytics to inform decisions

### For Production Engineers

1. **Review API** - Check [API.md](./API.md) for endpoint details
2. **Set Up Monitoring** - Configure alerts on success rate and cost
3. **Schedule Exports** - Set up regular data exports
4. **Plan Scaling** - Use analytics to forecast needs

### For Executives

1. **Review Dashboard** - Check analytics for high-level metrics
2. **Monitor Costs** - Track total cost trends
3. **Track Success Rate** - Ensure system reliability
4. **Export Reports** - Use monthly exports for stakeholder reporting

---

**Questions?** Review the relevant documentation file or contact support.

**Last Updated:** March 22, 2026
**Version:** 1.0.0
