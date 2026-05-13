# ACOS Design Library

## Purpose

This document defines the UX and design language for the ACOS control plane.

The goal is not to make ACOS look flashy.
The goal is to make operators trust, understand, and control AI-driven commerce workflows.

## Product Experience Principles

### 1. Control Before Decoration
The UI should communicate state, risk, and action clearly.

### 2. Dense But Legible
Enterprise users need meaningful information density without clutter.

### 3. Explain The System
Every important state should answer:
- what happened
- why it happened
- what can be done next

### 4. Design For Interruptions
Operators switch context often.
Views should preserve state and make recovery easy.

### 5. Make AI Behavior Inspectable
Agents, skills, policies, versions, and workflow steps must be visible, not implied.

## Primary Information Architecture

The control plane should be organized around these top-level areas:

### Overview
Fleet health, volume, failures, costs, and pending actions.

### Runs
Searchable execution history with timeline, filters, replay, and escalation context.

### Workflows
Definitions, versions, deployment status, and simulation entry points.

### Agents
Agent registry, roles, permitted skills, budgets, and status.

### Skills
Skill registry, schema, dependencies, and validation state.

### Policies
Rules, approvals, thresholds, and exceptions.

### Tenants
Tenant configuration, feature flags, quotas, and isolation settings.

## Canonical Page Types

### Inventory Page
Tabular list with filters, status, owner, last updated, and quick actions.

### Detail Page
Summary header, key metadata, timeline, tabs, and action rail.

### Editor Page
Draft-safe editing with validation, diff visibility, and publish controls.

### Review Page
Used for approvals, risk review, and rollout decisions.

### Operational Timeline
Event stream view for runs, failures, escalations, and step execution.

## Core Components

The design system should prioritize these components:

- app shell
- left navigation
- command bar
- page header with status and actions
- filter bar
- data table
- structured detail panel
- timeline
- diff viewer
- policy badge
- environment badge
- tenant badge
- step status pill
- empty state
- error state
- confirmation dialog
- approval drawer

## State Language

Use a consistent status vocabulary:

- Draft
- Validated
- Approved
- Active
- Paused
- Deprecated
- Running
- Succeeded
- Failed
- Escalated
- Awaiting Approval

## Visual Design Direction

### Overall Tone
Calm, operational, trustworthy, and modern.

### Color System
Use color semantically, not decoratively.

Recommended semantic roles:
- background
- surface
- surface-elevated
- border
- text-primary
- text-secondary
- accent
- success
- warning
- danger
- info

### Typography
Use a serious enterprise sans-serif with strong tabular data readability.
Prefer:
- headings with moderate character
- body text optimized for dense interfaces
- monospaced treatment for ids, versions, and payload snippets

### Motion
Subtle only.
Use motion to:
- confirm state transitions
- preserve orientation in detail transitions
- highlight newly arrived timeline events

Avoid decorative motion on operational pages.

## Interaction Patterns

### Mutations Must Feel Safe
For destructive or risky actions:
- show scope
- show affected environment and tenant
- show approval need
- show undo or replay path if available

### Tables Must Be Actionable
Rows should support:
- inspect
- compare versions
- replay
- filter by related entity

### Detail Views Must Explain Causality
A run detail page should clearly connect:
- input
- workflow version
- steps
- policy outcomes
- final result

## Accessibility Standards

Minimum standards:
- keyboard navigability for core flows
- visible focus states
- accessible names for actions
- sufficient contrast
- non-color status indicators
- readable responsive layouts down to laptop and tablet widths

## Content Design Rules

- prefer explicit system terms over marketing phrases
- write labels that reflect operator tasks
- avoid vague AI language such as "magic" or "superpowers" in primary workflows
- reserve aspirational language for marketing surfaces, not core operations

## Design Tokens

Recommended token groups:
- color
- typography
- spacing
- radius
- shadow
- border
- motion
- z-index

Tokens should be defined once and reused across the React control plane.

## Initial Design Priorities

The first real UI slices should focus on:

1. workflow inventory
2. run list and run detail timeline
3. workflow detail with version status
4. consistent app shell and filtering patterns

## Design Standard For Future Prompts

Every UI slice should:
- use the shared information architecture
- introduce reusable components instead of page-specific hacks
- reflect real backend data
- support enterprise operator tasks first
