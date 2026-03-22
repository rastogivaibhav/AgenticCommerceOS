# ACOS Control Plane - User Guide

**Complete feature walkthrough for workflow management, experimentation, and analytics**

## Table of Contents
1. [Interface Overview](#interface-overview)
2. [Workflow Builder](#workflow-builder)
3. [Experiments](#experiments)
4. [Analytics Dashboard](#analytics-dashboard)
5. [Dark Mode / Theme Management](#dark-mode--theme-management)
6. [Responsive Design](#responsive-design)
7. [Data Export](#data-export)
8. [Advanced Features](#advanced-features)

---

## Interface Overview

### Application Layout

When you first open ACOS Control Plane, you'll see this interface:

```
┌─────────────────────────────────────────────────────────────┐
│ ACOS Control Plane                                    🌙 ≡  │  Header
├────────────────────┬─────────────────────────────────────────┤
│                    │                                         │
│  Workflow Builder  │                                         │
│  ✓ Experiments    │         Main Content Area               │
│    Analytics       │         (Changes based on               │
│                    │          selected section)               │
│                    │                                         │
│                    │                                         │
│                    │                                         │
└────────────────────┴─────────────────────────────────────────┘
   Sidebar             Content Panel
```

**Header Components**
- Left: "ACOS Control Plane" logo/title
- Center: Current page title
- Right: Theme toggle (🌙 moon = dark mode, ☀️ sun = light mode)
- Far right (mobile): Hamburger menu (≡)

**Sidebar Navigation**
- **Workflow Builder** - Create and manage AI workflows
- **Experiments** - Run A/B experiments
- **Analytics** - View performance dashboards
- Active section highlighted with blue underline

**Main Content Area**
- Displays the selected section's content
- Responsive: adjusts for mobile, tablet, desktop
- Scrollable when content exceeds viewport

---

## Workflow Builder

### Overview

The Workflow Builder is your visual editor for creating AI agent workflows. Instead of writing code, you click buttons to add steps, then configure each with JSON parameters.

### Visual Layout

```
┌──────────────────────────────────────────────────────────┐
│ Workflow Builder                      Save Draft │ Deploy │
├─────────────┬────────────────────────────────────────────┤
│             │                                            │
│  + Input    │                                            │
│  + Agent    │      Canvas Area                           │
│    Call     │      (Your workflow steps appear here)     │
│  + Data     │                                            │
│    Trans    │   ┌──────────┐                            │
│  + Decision │   │ Input    │                            │
│  + Output   │   └──────────┘                            │
│             │                                            │
└─────────────┴────────────────────────────────────────────┘
  Tool Panel    Main Canvas
```

### Components

**Tool Panel (Left Side)**
Contains five buttons to add workflow steps:
- **+ Input** - Add input step
- **+ Agent Call** - Add agent call step
- **+ Data Transform** - Add data transform step
- **+ Decision** - Add conditional step
- **+ Output** - Add output step

**Main Canvas (Center)**
- Grid layout where your workflow steps appear
- Each step is a draggable card
- Step cards show name, type, and configuration

**Action Buttons (Top Right)**
- **Save Draft** - Saves your workflow as draft
- **Deploy** - Publishes workflow for production use

### Step Types and Configuration

#### 1. Input Step

Accepts data input to your workflow.

**Visual Representation:**
```
┌─────────────┐
│   Input     │
│  (name)     │
│             │
│ JSON Config │
└─────────────┘
```

**Configuration Example:**
```json
{
  "field_name": "user_query",
  "field_type": "string",
  "required": true,
  "default_value": null
}
```

**Parameters:**
- `field_name` - Name of input field
- `field_type` - Type: string, number, boolean, object
- `required` - Whether input is mandatory
- `default_value` - Default if not provided

#### 2. Agent Call Step

Calls an AI agent with specified parameters.

**Visual Representation:**
```
┌─────────────┐
│ Agent Call  │
│  (name)     │
│             │
│ JSON Config │
└─────────────┘
```

**Configuration Example:**
```json
{
  "agent_type": "search",
  "agent_id": "search-001",
  "timeout": 30,
  "retries": 2,
  "parameters": {
    "depth": "standard",
    "include_sources": true
  }
}
```

**Parameters:**
- `agent_type` - Type of agent: search, summarize, analyze, generate
- `agent_id` - Specific agent instance
- `timeout` - Max seconds to wait
- `retries` - How many times to retry on failure
- `parameters` - Agent-specific configuration

#### 3. Data Transform Step

Transforms or processes data between steps.

**Visual Representation:**
```
┌─────────────┐
│ Data Trans  │
│  (name)     │
│             │
│ JSON Config │
└─────────────┘
```

**Configuration Example:**
```json
{
  "transformation_type": "map",
  "input_field": "raw_results",
  "output_field": "processed_results",
  "mapping": {
    "title": "$.title",
    "score": "$.confidence",
    "source": "$.source_url"
  }
}
```

**Parameters:**
- `transformation_type` - Operation type: map, filter, aggregate, merge
- `input_field` - Field to transform
- `output_field` - Field to write results to
- `mapping` - Field mapping rules (JSONPath or similar)

#### 4. Decision Step

Makes conditional decisions with branching.

**Visual Representation:**
```
┌─────────────┐
│  Decision   │
│  (name)     │
│             │
│ JSON Config │
└─────────────┘
```

**Configuration Example:**
```json
{
  "condition_field": "score",
  "condition_type": "greater_than",
  "condition_value": 0.7,
  "true_action": "continue",
  "false_action": "retry"
}
```

**Parameters:**
- `condition_field` - Field to check
- `condition_type` - Type: equal, greater_than, less_than, contains, starts_with
- `condition_value` - Value to compare against
- `true_action` - What to do if true: continue, output, retry, fail
- `false_action` - What to do if false: continue, output, retry, fail

#### 5. Output Step

Returns final results from workflow.

**Visual Representation:**
```
┌─────────────┐
│   Output    │
│  (name)     │
│             │
│ JSON Config │
└─────────────┘
```

**Configuration Example:**
```json
{
  "output_format": "json",
  "include_metadata": true,
  "fields": [
    "result",
    "score",
    "execution_time"
  ],
  "error_handling": "return_error"
}
```

**Parameters:**
- `output_format` - Format: json, xml, csv, plain_text
- `include_metadata` - Include timing and execution info
- `fields` - Specific fields to include
- `error_handling` - How to handle errors: return_error, return_null, fail

### Creating a Workflow

**Step-by-Step Process:**

1. **Click "+ Input" button**
   - New Input step appears on canvas
   - Editable name field shows "Input"

2. **Configure the Input step**
   - Click on the JSON configuration area
   - A text input appears
   - Paste or type your configuration JSON
   - Example:
   ```json
   {
     "field_name": "search_query",
     "field_type": "string",
     "required": true
   }
   ```

3. **Click "+ Agent Call" button**
   - New Agent Call step appears below Input
   - Step name is editable

4. **Configure the Agent Call step**
   - Click JSON configuration
   - Add agent configuration:
   ```json
   {
     "agent_type": "search",
     "timeout": 30,
     "parameters": {
       "search_depth": "standard"
     }
   }
   ```

5. **Add more steps as needed**
   - Continue adding Data Transform, Decision, or Output steps
   - Configure each step with relevant JSON

6. **Save as Draft**
   - Click "Save Draft" button
   - Workflow is saved locally
   - You can continue editing

7. **Deploy to Production**
   - Click "Deploy" button
   - Workflow becomes available for experiments
   - Locked from further editing until new version

### Step Naming Best Practices

**Good Names:**
- "Fetch User Data" - Descriptive, clear purpose
- "Check Score Threshold" - Indicates what decision does
- "Format Results" - Clear transformation purpose
- "Return JSON Output" - Obvious what happens

**Avoid:**
- "Step 1", "Step 2" - Not descriptive
- "Agent" - Too vague
- "x" or "temp" - Non-meaningful names

### Workflow Status

**Workflow States:**

- **Editing (Draft)** - Unsaved changes to workflow
  - Save button shows "Save Draft"
  - Can edit all steps freely

- **Saved Draft** - Workflow saved but not published
  - All steps visible
  - Can edit and save again
  - Not used in production

- **Published** - Workflow deployed to production
  - Used by active experiments
  - Cannot edit directly
  - Create new version to modify

### Common Workflow Patterns

**Pattern 1: Simple Sequential Processing**
```
Input → Agent Call → Output
```
Best for: Simple tasks with single agent

**Pattern 2: Multi-Agent with Decision**
```
Input → Agent Call 1 → Decision → Agent Call 2 → Output
```
Best for: Conditional workflows that branch based on results

**Pattern 3: Data Processing Pipeline**
```
Input → Agent Call → Data Transform → Data Transform → Output
```
Best for: Complex data preparation and transformation

**Pattern 4: Retry Loop**
```
Input → Agent Call → Decision (success?) → Output (yes) or Retry (no)
```
Best for: Robust error handling with automatic retries

---

## Experiments

### What Experiments Do

Experiments compare two versions (Variant A and Variant B) of a workflow to determine which performs better.

**Use Cases:**
- Test if longer timeouts improve quality
- Compare different agent types for same task
- Validate parameter changes before deployment
- A/B test different data transformation approaches

### Experiments Interface

```
┌──────────────────────────────────────────────────────┐
│ Experiments              [Create Experiment Button]  │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Recent Experiments:                                  │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Search Timeout Test                    Results  │ │
│ │ Workflow: Search                                │ │
│ │ Samples: 100   Status: Complete                 │ │
│ └─────────────────────────────────────────────────┘ │
│                                                      │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Agent Type Comparison                  Results  │ │
│ │ Workflow: Analysis                              │ │
│ │ Samples: 50    Status: Complete                 │ │
│ └─────────────────────────────────────────────────┘ │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Creating an Experiment

**Step 1: Click "Create Experiment"**

Experiment form appears with fields:
- Experiment name
- Workflow selection
- Sample size configuration
- Variant A configuration
- Variant B configuration

```
┌────────────────────────────────────┐
│  Create New Experiment              │
├────────────────────────────────────┤
│                                    │
│ Experiment Name:                   │
│ [Search Timeout Test          ]    │
│                                    │
│ Select Workflow:                   │
│ [Dropdown: Search]                 │
│                                    │
│ Sample Size:                       │
│ [100                           ]   │
│                                    │
│ Variant A Configuration:           │
│ {                                  │
│   "timeout": 30,                   │
│   "retries": 2                     │
│ }                                  │
│                                    │
│ + Add Parameter                    │
│                                    │
│ Variant B Configuration:           │
│ {                                  │
│   "timeout": 60,                   │
│   "retries": 2                     │
│ }                                  │
│                                    │
│ + Add Parameter                    │
│                                    │
│              [Run Experiment]      │
│                                    │
└────────────────────────────────────┘
```

**Step 2: Name Your Experiment**

Enter descriptive name in "Experiment Name" field:
- Examples: "Search Timeout Test", "Agent Type Comparison", "Data Transform v2"
- Use consistent naming for easy tracking

**Step 3: Select Workflow**

Click workflow dropdown and choose from your published workflows:
- Only published workflows appear
- Draft workflows cannot be selected
- If no workflows available, publish one first

**Step 4: Set Sample Size**

Enter number of test samples:
- Minimum: 10 (for quick tests)
- Recommended: 50-100 (for reliable results)
- Maximum: 1000+ (for statistical rigor)

Number of samples determines:
- How long experiment takes
- How reliable results are
- How much data is processed

### Configuring Variants

**Variant A (Baseline)**

This is typically your current/baseline configuration.

Click in the Variant A configuration area and enter JSON:
```json
{
  "timeout": 30,
  "search_depth": "standard",
  "include_sources": true,
  "retry_on_failure": true
}
```

**Variant B (Test)**

This is what you're testing against baseline.

Change one or two parameters:
```json
{
  "timeout": 60,
  "search_depth": "standard",
  "include_sources": true,
  "retry_on_failure": true
}
```

In this example, only `timeout` changed (30 → 60).

**Tips:**
- Change only ONE variable per experiment for clarity
- Keep everything else identical between variants
- Use meaningful parameter names
- Multiple changes make results ambiguous

### Running Experiment

**Click "Run Experiment" Button**

Progress appears showing:
- Current step (Variant A, Variant B, Analysis)
- Sample progress (e.g., "42 of 100 samples")
- Elapsed time
- Estimated time remaining

```
┌──────────────────────────────┐
│ Experiment Running            │
├──────────────────────────────┤
│                              │
│ Status: Running Variant A    │
│                              │
│ Progress: ████████░░░░░░░░░░ │
│           42 of 100 samples   │
│                              │
│ Elapsed: 2m 15s              │
│ Estimated: 4m 30s remaining  │
│                              │
└──────────────────────────────┘
```

### Experiment Results

When complete, results show:

```
┌────────────────────────────────────┐
│  Search Timeout Test - Results      │
├────────────────────────────────────┤
│                                    │
│  Variant A Score:        Variant B Score:
│  ┌──────────────┐        ┌──────────────┐
│  │ Score: 78.5  │        │ Score: 82.1  │
│  │              │        │              │
│  │ Runs: 50     │        │ Runs: 50     │
│  │ Avg Cost: $2 │        │ Avg Cost: $2 │
│  └──────────────┘        └──────────────┘
│                                    │
│           ✅ Winner: Variant B     │
│     (Statistically significant)    │
│                                    │
│ [Export Results]  [Save Config]    │
│                                    │
└────────────────────────────────────┘
```

**Results Include:**

For each variant:
- **Score** - Primary metric (0-100)
- **Runs Completed** - Number of samples executed
- **Average Cost** - Cost per run
- **Success Rate** - % of runs that succeeded

**Winner Determination:**
- System compares average scores
- Determines if difference is statistically significant
- Shows recommendation (if confident)
- Shows confidence level if not obvious

### Using Results

**If Winner is Clear**
- Variant B clearly better
- Consider deploying B's configuration
- Update your workflows with winning parameters

**If Results are Close**
- Difference is minimal
- Other factors may matter (cost, reliability)
- Consider running larger experiment
- Or choose based on secondary metrics

**Export Results**
- Click "Export Results" button
- Choose CSV or JSON format
- Save for documentation and reporting

---

## Analytics Dashboard

### Dashboard Overview

The Analytics dashboard displays comprehensive metrics about your workflows.

```
┌──────────────────────────────────────────────────────────┐
│ Analytics                                                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ Total    │  │ Avg      │  │ Total    │  │ Success  ││
│  │ Runs     │  │ Score    │  │ Cost     │  │ Rate     ││
│  │ 1,234    │  │ 81.5     │  │ $2,340   │  │ 97%      ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
│                                                          │
│  Daily Activity                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 300 ┤                    ╱╲                         │ │
│  │ 200 ├──────╱╲──────────╱  ╲──────────╱╲────────   │ │
│  │ 100 ├                                             │ │
│  │   0 └────────────────────────────────────────────  │ │
│  │     M  T  W  T  F  S  S  M  T  W  T  F  S  S      │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Workflow Performance                                    │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 100 │ ██ ██ ██                                    │ │
│  │  80 │ ██ ██ ██                                    │ │
│  │  60 │ ██ ██ ██ ██                                │ │
│  │  40 │ ██ ██ ██ ██                                │ │
│  │  20 │ ██ ██ ██ ██                                │ │
│  │   0 └─────────────────────────────────────────  │ │
│  │     S  S  A  D                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Metrics by Workflow                    [Export Data] │ │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Name    │ Runs │ Avg Score │ Cost  │ Success %    │ │
│  │─────────┼──────┼───────────┼───────┼──────────────│ │
│  │ Search  │ 456  │ 82.1      │ $1.20 │ 98%          │ │
│  │ Analysis│ 234  │ 78.5      │ $0.80 │ 95%          │ │
│  │ Summarize│ 544 │ 85.2      │ $0.60 │ 99%          │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Key Metrics Cards

Four metric cards at the top of dashboard:

#### 1. Total Runs

**Shows:** How many times workflows have executed

```
┌──────────────┐
│ Total Runs   │
│              │
│    1,234     │
│              │
│ Cumulative   │
└──────────────┘
```

**What it means:**
- Count of all workflow executions
- Includes successful and failed runs
- Resets never (cumulative metric)
- Helps understand usage volume

#### 2. Average Score

**Shows:** Mean performance score (0-100)

```
┌──────────────┐
│ Avg Score    │
│              │
│    81.5      │
│              │
│ Higher better│
└──────────────┘
```

**What it means:**
- Average of all run scores
- Scale: 0-100 (higher is better)
- Calculated from completed runs only
- Good indicator of overall quality

#### 3. Total Cost

**Shows:** Sum of all execution costs

```
┌──────────────┐
│ Total Cost   │
│              │
│  $2,340      │
│              │
│ USD (or local)
└──────────────┘
```

**What it means:**
- Sum of costs for all runs
- Helps track spending
- Use for budget forecasting
- Identify expensive workflows

#### 4. Success Rate

**Shows:** Percentage of successful runs

```
┌──────────────┐
│ Success Rate │
│              │
│     97%      │
│              │
│ Higher better│
└──────────────┘
```

**What it means:**
- % of runs that completed successfully
- Failed runs reduce this percentage
- <90% may indicate issues
- Track over time for trends

### Daily Activity Chart

Line chart showing runs per day over time.

**How to Read:**
- X-axis: Dates (left to right is older to newer)
- Y-axis: Number of runs on that day
- Each point: Number of runs that day
- Line connects points to show trend

**What it shows:**
- Usage patterns (peak days, quiet days)
- Trends (growing, steady, declining usage)
- Spikes (large deployments or events)
- Gaps (no activity)

**Example Analysis:**
- Growing line left-to-right: Increasing adoption
- Spiky pattern: Event-driven usage
- Flat line: Consistent, steady usage

### Workflow Performance Chart

Bar chart comparing average scores across workflows.

**How to Read:**
- X-axis: Workflow names
- Y-axis: Average score (0-100)
- Bar height: That workflow's average score
- Higher bar: Better performing workflow

**What it shows:**
- Which workflows perform best
- Which workflows need improvement
- Relative performance comparison
- Quick visual of quality differences

**Example:**
- Tall bar: High-quality workflow
- Short bar: May need optimization
- Even heights: Similar quality across workflows

### Metrics Table

Detailed table showing per-workflow metrics.

**Columns:**

| Column | Meaning |
|--------|---------|
| Workflow Name | Name of the workflow |
| Status | Active or Inactive |
| Total Runs | Number of executions |
| Avg Score | Average performance (0-100) |
| Total Cost | Sum of all costs |
| Success Rate | % of successful runs |

**Sorting:**

Click any column header to sort by that column:
- First click: Sort ascending (A→Z, 0→100)
- Second click: Sort descending (Z→A, 100→0)
- Third click: Return to default order

**Example Sorts:**
- By Avg Score: Find best/worst performers
- By Total Cost: Find most expensive workflows
- By Success Rate: Find unreliable workflows

### Understanding the Data

**High Avg Score (80+)**
- Workflow performing well
- Quality output
- Good candidate for production

**Low Avg Score (<60)**
- Workflow may have issues
- Consider investigation
- May need parameter adjustment

**Low Success Rate (<90%)**
- Failures occurring frequently
- Check workflow configuration
- Review error logs

**High Total Cost**
- Expensive operations
- May be timeout/retry heavy
- Consider optimization

### Exporting Data

**Export Button Location:**
- Bottom right of dashboard
- Visible after metrics load
- Available on Analytics page only

**Export Process:**

1. Scroll to bottom of dashboard
2. Click "Export Data" button
3. Dialog appears with format options
4. Select CSV or JSON
5. File downloads automatically

**Export Formats:**

**CSV Format:**
- Spreadsheet-compatible
- Opens in Excel, Google Sheets
- Good for data analysis
- Filename: `analytics-data-2026-03-22.csv`

**JSON Format:**
- Machine-readable format
- Good for API integration
- Preserves data types
- Filename: `analytics-data-2026-03-22.json`

**What's Included:**
- All workflow metrics
- Names, scores, costs, success rates
- Timestamp of export
- Current date/time

---

## Dark Mode / Theme Management

### Theme Toggle Location

Theme toggle button is in the top-right corner of header:
- **🌙 Moon icon** - Currently in light mode
- **☀️ Sun icon** - Currently in dark mode

Click the icon to toggle between themes.

### Dark Mode Appearance

**Colors Change:**
- Backgrounds: Dark gray (#1a1a1a) instead of white
- Text: White (#ffffff) instead of black
- Accents: Colors remain vibrant
- Cards: Dark with subtle borders

**Visual Effect:**
- Professional, sleek appearance
- Easier on eyes in low light
- Preserves readability
- Good for evening use

### Light Mode Appearance

**Colors:**
- Backgrounds: Pure white (#ffffff)
- Text: Dark gray/black (#1a1a1a)
- Accents: Full saturation colors
- Cards: White with subtle shadows

**Visual Effect:**
- Clean, minimal appearance
- High contrast for readability
- Good for bright environments
- Suitable for printing

### Theme Persistence

Your theme preference is automatically saved:
- Toggle theme once
- Your choice is remembered
- Next visit uses your selected theme
- Saved in browser's localStorage

### Automatic Detection

If you haven't selected a theme:
1. System checks your OS setting
2. Mac/Windows dark mode: App loads dark
3. Mac/Windows light mode: App loads light
4. Applies only on first visit (before you select)

### Examples

**Dark Mode Interface:**
```
┌─────────────────────────────────────────┐
│ ACOS Control Plane                  ☀️  │  Dark gray bg
├─────────────────────────────────────────┤
│                                         │
│ ▌ Workflow Builder                      │  Dark
│   Experiments                           │  sidebar
│   Analytics                             │
│                                         │
│                                         │
│          DARK CONTENT AREA              │  Dark
│          (White text on dark)           │  main
│                                         │  area
│                                         │
└─────────────────────────────────────────┘
```

**Light Mode Interface:**
```
┌─────────────────────────────────────────┐
│ ACOS Control Plane                  🌙  │  White bg
├─────────────────────────────────────────┤
│                                         │
│ ▌ Workflow Builder                      │  White
│   Experiments                           │  sidebar
│   Analytics                             │
│                                         │
│                                         │
│          LIGHT CONTENT AREA             │  White
│          (Dark text on white)           │  main
│                                         │  area
│                                         │
└─────────────────────────────────────────┘
```

---

## Responsive Design

### What Responsive Design Means

The application automatically adjusts its layout based on your screen size:
- Same content
- Different arrangement
- Optimized for readability
- Touch-friendly on mobile

### Mobile Layout (375px - 640px)

**Example: iPhone SE (375px wide)**

```
┌─────────────────┐
│ ACOS Control ≡ 🌙│  Header (compact)
├─────────────────┤
│                 │
│  [Full width    │
│   content]      │
│                 │
│                 │
│                 │
│                 │
│                 │
│                 │
│                 │
└─────────────────┘
```

**Features:**
- Hamburger menu (≡) shows/hides sidebar
- Full-width content area
- Single column layout
- Touch-optimized buttons (larger targets)
- Sidebar appears as overlay when opened

**Navigation:**
- Click ≡ hamburger to open sidebar
- Click item to navigate
- Sidebar closes after selecting
- Keeps screen uncluttered

### Tablet Layout (641px - 1024px)

**Example: iPad (768px wide)**

```
┌──────────────────────────────────────┐
│ ACOS Control Plane            🌙      │
├──────────────┬──────────────────────┤
│ Workflow     │                      │
│ Builder      │  Main Content Area   │
│ Experiments  │  (Two-column)        │
│ Analytics    │                      │
│              │                      │
│              │                      │
│              │                      │
└──────────────┴──────────────────────┘
```

**Features:**
- Sidebar always visible
- Two-column layout begins
- More space for content
- Headers and cards optimized for tablet viewing
- Touch still primary interaction

**Navigation:**
- Click sidebar items directly
- No overlay needed
- Full sidebar visible always

### Desktop Layout (1025px+)

**Example: Desktop (1280px wide)**

```
┌────────────────────────────────────────────────────────┐
│ ACOS Control Plane                               🌙     │
├──────────┬──────────────────────┬─────────────────────┤
│          │                      │                     │
│ Sidebar  │ Main Content Area    │ Optional Details    │
│          │                      │ (Charts, Tables)    │
│ Workflow │                      │                     │
│ Builder  │                      │                     │
│          │                      │                     │
│ Exper    │                      │                     │
│ iments   │                      │                     │
│          │                      │                     │
│ Analytics│                      │                     │
│          │                      │                     │
└──────────┴──────────────────────┴─────────────────────┘
```

**Features:**
- Three-column layout available
- Sidebar always visible
- Spacious content area
- Details panel (optional)
- Full feature set visible
- Mouse-optimized controls

**Navigation:**
- Click sidebar items
- All content visible without scrolling (if space permits)
- Full navigation always accessible

### Responsive Elements

**Buttons Adapt Size:**
- Mobile: Large (44px+ height) for thumb tapping
- Tablet: Medium (36px)
- Desktop: Standard (32px)

**Text Sizing:**
- Mobile: Larger for readability
- Tablet: Medium
- Desktop: Can be smaller (more space)

**Form Fields:**
- Mobile: Full width for easy input
- Tablet: Wider
- Desktop: Multiple columns possible

**Charts and Tables:**
- Mobile: Vertical scroll, single metric
- Tablet: Slightly wider columns
- Desktop: Multiple metrics visible

### Testing Responsive Design

**On Your Computer:**
1. Open browser DevTools (F12 or Cmd+Option+I)
2. Click responsive design mode (Cmd+Shift+M)
3. Select device preset:
   - iPhone SE (375x667)
   - iPad (768x1024)
   - Desktop (1280x800)
4. Observe how layout changes

**Real Device:**
- Open on your phone/tablet
- Rotate device (portrait → landscape)
- Layout should adapt smoothly
- All functions should work

---

## Data Export

### When to Export

Export data when you need to:
- Create reports for stakeholders
- Archive analytics for compliance
- Perform advanced analysis in Excel/spreadsheet
- Share data with team members
- Back up metrics

### How to Export

**From Analytics Dashboard:**

1. Scroll to bottom of dashboard
2. Click "Export Data" button
3. Dialog opens with format options
4. Select CSV or JSON
5. File downloads to your computer

**Export Dialog:**
```
┌──────────────────────────────┐
│ Export Analytics Data        │
├──────────────────────────────┤
│                              │
│ Choose export format:        │
│                              │
│ ◉ CSV (Excel-compatible)    │
│ ○ JSON (Machine-readable)   │
│                              │
│   [Cancel]      [Export]     │
│                              │
└──────────────────────────────┘
```

### CSV Format

**Best for:** Excel, Google Sheets, data analysis

**File looks like:**
```
Workflow Name,Status,Total Runs,Avg Score,Total Cost,Success Rate
Search,Active,456,82.1,1234.56,98
Analysis,Active,234,78.5,890.12,95
Summarize,Active,544,85.2,1256.80,99
```

**Opening in Excel:**
1. Download CSV file
2. Open Excel
3. File → Open
4. Select the CSV file
5. Data appears in columns
6. Ready to analyze or print

### JSON Format

**Best for:** API integration, data pipelines, developers

**File looks like:**
```json
{
  "export_date": "2026-03-22T15:30:00Z",
  "workflows": [
    {
      "name": "Search",
      "status": "Active",
      "total_runs": 456,
      "avg_score": 82.1,
      "total_cost": 1234.56,
      "success_rate": 0.98
    }
  ]
}
```

**Using in Code:**
```javascript
// Load JSON file
fetch('analytics-data.json')
  .then(res => res.json())
  .then(data => {
    data.workflows.forEach(workflow => {
      console.log(workflow.name, workflow.avg_score);
    });
  });
```

### From Experiments

**Export Experiment Results:**

1. Navigate to Experiments
2. Click on completed experiment
3. Results display with data
4. Click "Export Results"
5. Choose CSV or JSON
6. File downloads

**CSV Experiment Format:**
```
Variant,Avg Score,Total Runs,Avg Cost,Success Rate
Variant A,78.5,50,2.00,95
Variant B,82.1,50,2.10,98
```

---

## Advanced Features

### Keyboard Shortcuts

**Navigation:**
- `Tab` - Move between interactive elements
- `Shift+Tab` - Move backward
- `Enter` - Activate buttons, submit forms
- `Escape` - Close dialogs

**Theme:**
- `Alt+T` - Toggle dark/light mode

**Forms:**
- `Tab` - Next field
- `Shift+Tab` - Previous field
- `Space` - Check/uncheck boxes
- `Enter` - Submit form

### Accessibility Features

**Screen Reader Support:**
- All buttons have labels
- Form fields have descriptions
- Images have alt text
- Navigation landmarks present

**Keyboard Navigation:**
- All functions accessible via keyboard
- No mouse required
- Tab order logical
- Focus visible at all times

**Color Contrast:**
- Dark and light modes both WCAG AA compliant
- Text readable by users with color blindness
- Sufficient contrast ratios throughout

### Browser Support

**Fully Supported:**
- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Features by Browser:**
- Modern CSS: All browsers
- ES2020 JavaScript: All browsers
- LocalStorage: All browsers (with fallback)
- Responsive: All browsers
- Dark mode detection: All modern browsers

### Performance

**Load Time:**
- Page loads: <2 seconds
- Charts render: <1 second
- Data export: <5 seconds
- Experiments run: 2-5 minutes (varies by sample size)

**Tips for Best Performance:**
- Use modern browser
- Close unnecessary tabs
- Ensure good internet connection
- Clear browser cache periodically

---

**Questions?** Review [ONBOARDING.md](./ONBOARDING.md) for step-by-step guides or contact support.

**Last Updated:** March 22, 2026
**Version:** 1.0.0
