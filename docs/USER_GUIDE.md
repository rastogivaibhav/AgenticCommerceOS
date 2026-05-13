# ACOS Control Plane - User Guide

## Introduction

The ACOS Control Plane is a production-grade workflow orchestration platform designed to manage complex agentic workflows, run A/B experiments, and monitor system performance in real-time.

## Getting Started

### Accessing the Control Plane

1. Navigate to your ACOS Control Plane instance URL (typically `http://localhost:5173` for local development)
2. Authenticate using your API key or OAuth credentials
3. You'll land on the Agents dashboard by default

## Core Features

### 1. Agents Management

**Location:** Navigation → Agents

#### View Agents
- The agents page displays all available agents in your system
- Each agent shows:
  - Name and description
  - Current status (active/inactive)
  - Last activity timestamp
  - Associated skills count

#### Create New Agent
1. Click "Create Agent" button in the top-right
2. Enter agent details:
   - **Name** (required): Unique identifier for the agent
   - **Description** (optional): What this agent does
   - **Type**: Select agent category (Worker, Supervisor, Analyst, etc.)
3. Click "Save" to create the agent
4. The agent will appear in the list and be available for workflows

#### Update Agent
1. Click on an agent to open its detail view
2. Edit any field (description, status, configuration)
3. Click "Save Changes" to persist updates

### 2. Skills Management

**Location:** Navigation → Skills

#### Browse Available Skills
- View all skills available in your system
- Each skill displays:
  - Name and description
  - Input/output parameters
  - Usage count and success rate
  - Last updated date

#### Create New Skill
1. Click "Create Skill" button
2. Define skill properties:
   - **Name** (required): Unique skill identifier
   - **Description** (required): What the skill does
   - **Input Schema** (JSON): Required parameters
   - **Output Schema** (JSON): Return value structure
3. Add implementation details if needed
4. Click "Save" to create the skill

#### Assign Skills to Agents
1. Go to the Agents page
2. Select an agent to edit
3. Click "Add Skill" under the Skills section
4. Choose available skills to assign
5. Save the agent configuration

### 3. Workflow Builder

**Location:** Navigation → Workflows

#### Create a New Workflow
1. Click "Create Workflow" button
2. Enter workflow metadata:
   - **Name** (required): Unique workflow identifier
   - **Description** (optional): Purpose and overview
   - **Family** (optional): Group workflows by category
3. Click "Next" to start building steps

#### Build Workflow Steps
1. You'll see the visual workflow canvas
2. Click "Add Step" to insert new steps
3. Choose step type from the menu:
   - **Agent Step**: Execute an agent action
   - **Decision Step**: Branch logic based on conditions
   - **Wait Step**: Pause for specified duration or event
   - **Loop Step**: Repeat a set of actions
   - **Aggregate Step**: Combine multiple streams

#### Configure Step Parameters
1. Click on a step to open the configuration panel on the right
2. Set parameters:
   - **Agent/Skill**: Select which agent or skill to execute
   - **Inputs**: Map workflow variables to step inputs
   - **Outputs**: Name the output variables
   - **Error Handling**: Define retry or fallback behavior
3. Click elsewhere to close the panel

#### Connect Steps
1. Hover over step outputs to reveal connector points
2. Drag from output to next step's input
3. Connection shows data flow through workflow

#### Save and Deploy
1. Click "Save Draft" to save without deploying
2. Drafts are not executable but can be edited
3. Click "Deploy Workflow" when ready:
   - This creates a versioned release
   - Previous versions remain available
   - All agents must be active to deploy
4. Deployed workflows appear as "Active"

#### Test Workflow
1. Click "Test Run" on an active workflow
2. Provide required inputs in the modal
3. Click "Execute" to run
4. View real-time execution progress
5. Results display in the "Output" tab

### 4. Running Experiments

**Location:** Navigation → Experiments

#### Understanding A/B Testing
- Compare two workflow variants (A and B)
- Measure which performs better by selected metric
- Results show statistical significance
- Each variant gets approximately equal traffic

#### Create New Experiment
1. Click "Create Experiment" button
2. Enter experiment details:
   - **Name** (required): Descriptive experiment name
   - **Workflow** (required): Select workflow to test
   - **Duration** (optional): How long to run (days/hours)
   - **Sample Size**: Number of runs per variant
3. Click "Next" to configure variants

#### Configure Variants
1. **Variant A (Control)**:
   - Keep this as your current/baseline version
   - Or modify parameters to test changes
2. **Variant B (Treatment)**:
   - Adjust parameters or select different agents
   - This is what you're testing against control
3. For each variant:
   - Select input parameters
   - Set values or ranges
   - Review the diff

#### Define Success Metrics
1. Choose metric to optimize for:
   - **Success Rate**: % of runs that complete successfully
   - **Response Time**: Median execution time
   - **Cost**: Total or per-run cost
   - **Score**: Custom scoring metric
2. Set target threshold (e.g., 5% improvement)
3. Choose confidence level (95% recommended)

#### Run Experiment
1. Review summary of experiment setup
2. Click "Start Experiment"
3. Experiment begins routing traffic to both variants
4. Monitor progress in real-time on the experiment page

#### Analyze Results
1. Go to experiment detail page
2. View key metrics:
   - Variant A vs B performance
   - Statistical significance (p-value)
   - Confidence interval
   - Recommended winner
3. Click "Export Results" for detailed data
4. If significant winner found:
   - Click "Promote Variant" to make it default
   - Or "Run Longer" to gather more data

### 5. Analytics Dashboard

**Location:** Navigation → Analytics

#### Key Metrics Overview
1. **Total Runs**: Cumulative workflow executions
2. **Success Rate**: Percentage of successful runs
3. **Average Cost**: Mean cost per run (if tracked)
4. **P50 Latency**: Median execution time

#### Trends and Charts
1. **Execution Trend**: Line chart of runs over time
2. **Success Rate Trend**: Success rate over time window
3. **Cost Trend**: Running cost analysis
4. **Top Workflows**: Bar chart of most-used workflows

#### Filtering and Drill-Down
1. Use date range selector at top
2. Filter by:
   - Workflow
   - Agent
   - Status (success/failed)
   - Environment (dev/staging/prod)
3. Click bars/lines to drill into details

#### Exporting Data
1. Click "Export Data" button (top-right)
2. Choose format:
   - CSV: For Excel/spreadsheet analysis
   - JSON: For API integration
   - PDF: For reports
3. Optionally select:
   - Metrics to include
   - Date range
   - Grouping (by day/week/month)
4. Download starts automatically

#### Real-Time Monitoring
1. Metrics update every 30 seconds
2. Charts show last 30 days by default
3. Enable "Live Mode" toggle for 5-second updates
4. Useful during experiments or high-traffic periods

### 6. Theme and Display Settings

#### Toggle Dark/Light Mode
1. Look for sun/moon icon in the top-right header
2. Click to toggle between light and dark themes
3. Your preference is automatically saved
4. Applies to all pages and components

#### Display Settings
1. Click settings icon (gear icon) in header
2. Options available:
   - **Compact View**: Reduced spacing for dense information
   - **Chart Type**: Switch between different visualization types
   - **Refresh Rate**: Adjust metric update frequency
   - **Default Timezone**: Set display timezone

## Workflow Execution Patterns

### Sequential Workflow
Agents execute in strict order, each waiting for previous to complete.

### Parallel Workflow
Multiple agents execute simultaneously, then results merge.

### Conditional Workflow
Execution path depends on previous step results.

### Looped Workflow
Steps repeat based on condition or count.

## Common Tasks

### Monitor Running Workflow
1. Go to Agents page
2. Look for agent with status "Running"
3. Click the agent to see active runs
4. View execution timeline and logs

### Rollback Workflow Version
1. Go to Workflows page
2. Click on workflow name to see versions
3. Find desired version in version history
4. Click "Rollback" to make it active
5. Confirm action

### Debug Failed Run
1. Go to Analytics > Runs
2. Filter by status "Failed"
3. Click on failed run to view details
4. View error logs and execution trace
5. Identify which step failed
6. Modify workflow and re-run

### Compare Experiments
1. Go to Experiments page
2. Select two experiments to compare
3. Click "Compare" button
4. View side-by-side metrics and charts
5. Use insights to inform next experiments

## Troubleshooting

### Workflow Won't Deploy
- Check that all referenced agents are active
- Verify all step inputs are properly configured
- Look for validation errors in the configuration panel
- Check agent and skill compatibility

### Experiment Running Slowly
- Increase sample size may slow results
- Wait for more data to achieve significance
- Check if both variants are receiving traffic
- Look at individual run performance metrics

### Can't Create Agent
- Agent name may already exist
- Check for required fields
- Verify no special characters in name
- Ensure proper permissions/access

### Missing Data in Analytics
- Some metrics take time to aggregate
- Check date range includes relevant period
- Verify workflows have actually executed
- Try refreshing the page

## Advanced Topics

### Custom Metrics
- Contact your administrator to add custom metrics
- Metrics are calculated from run data
- Can be used in experiment success criteria

### API Access
- Generate API keys in Settings > API Keys
- Use Bearer token in Authorization header
- See API documentation for endpoint details

### Integrations
- Connect external systems via webhooks
- Trigger workflows from external events
- Stream results to analytics platforms

## Support and Resources

- **Documentation**: Full API docs at `/api/docs`
- **Support**: Contact your platform administrator
- **Issues**: Report bugs through the feedback form
- **Feedback**: Help improve the platform via feature requests

## Release Notes

**Version 1.0.0** - Initial Release
- Core workflow builder functionality
- A/B experiment framework
- Real-time analytics dashboard
- Dark/light mode support
- API key authentication
- Full responsive design
