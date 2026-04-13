# ACOS Retail Capability Map

## Purpose

This document maps the current ACOS implementation to the retail operating capabilities it already supports, the capabilities it partially supports, and the gaps that are still mostly roadmap.

## Strategic Positioning

ACOS currently acts as:
- a retail workflow and operations layer
- a control plane for governed AI-assisted commerce execution
- a channel-aware service orchestration layer
- a thin integration layer across CRM and commerce systems

It does not try to replace the system of record for orders, CRM, loyalty, or catalog data.

## Capability Coverage By Domain

### 1. Discovery And Merchandising

Implemented today:
- natural-language shopper intake
- journey routing into `discovery`
- catalog recommendation and pricing/promotion assistance
- explanation generation through the runtime provider layer

Current systems used:
- local catalog/product data
- ADK runtime provider layer

Current maturity:
- usable in the shopper runtime
- still lighter than the service-flow and ops-plane portions of the platform

### 2. Basket And Purchase Support

Implemented today:
- purchase-family routing
- pricing, promotions, loyalty, and checkout guidance in the coded shopper journey runtime
- workflow family and version tracking on purchase-related runs

Current systems used:
- local commerce plugins
- ADK runtime provider layer

Current maturity:
- functional as guided assistance
- not yet a deeply integrated checkout orchestration platform

### 3. Fulfillment And Post-Purchase

Implemented today:
- order status flows
- post-purchase workflow family
- Shopify order lookup through connector nodes
- channel-facing “where is my order” style support
- notification of operators through configured channel targets

Current systems used:
- Shopify Admin API
- channel bindings and demo routes

Current maturity:
- one of the strongest current slices in the repository

### 4. Service Recovery And Escalation

Implemented today:
- service-family workflows
- Salesforce contact and case operations
- human escalation node execution
- CRM case persistence
- incident and rollback surfaces in the ops API

Current systems used:
- Salesforce REST API
- CRM customer and case tables
- workflow executor human nodes

Current maturity:
- strong demo and sandbox support
- partial live support depending on connector credentials and runtime environment

### 5. Loyalty And Customer Growth

Implemented today:
- loyalty balance and tier awareness
- engagement workflow family
- loyalty-related demo routes
- CRM segmentation and preferred-channel context

Current systems used:
- `loyalty_points`
- `crm_customers`
- shopper runtime and demo routes

Current maturity:
- useful as part of assisted journeys
- not yet a full CRM/campaign automation product

### 6. Omnichannel Service Entry

Implemented today:
- WhatsApp inbound verification and outbound messaging
- Telegram bot probing, pairing, and outbound messaging
- sender approval workflow
- route inference from inbound messages
- scan-to-start or pair-code channel onboarding

Current systems used:
- WhatsApp Cloud API
- Telegram Bot API
- channel binding/sender/pairing tables

Current maturity:
- a real implemented slice, even though many deployments will still run in sandbox or preview mode until configured

### 7. Operator And Commerce Team Support

Implemented today:
- workflow registry and editor
- agents and skills pages
- analytics views
- run inspection and replay
- approval, promotion, rollback, and archive controls
- channel and demo route operations
- incident endpoints and audit views

Current systems used:
- `ops-api`
- `ops_ui_v2`
- workflow, run, audit, and analytics endpoints

Current maturity:
- this is the most developed part of ACOS today

## Systems Of Record Versus ACOS

### Systems Of Record ACOS Integrates With

- Shopify for commerce/order/product context
- Salesforce for contact and case context
- WhatsApp and Telegram for channel transport

### Systems ACOS Owns Directly

- workflow definitions and versions
- workflow promotions
- operational runs and traces
- channel onboarding state
- operator-facing agent and skill registry records
- local CRM/demo routing state

## Current Retail Personas Served

The current implementation best serves:
- ecommerce operations
- service and support operations
- platform engineers
- workflow authors
- operators managing channel demos and incident flows

It partially serves:
- merchandising
- loyalty/CRM teams

It does not yet deeply serve:
- store operations
- supply chain operations
- payments and fraud teams

## Current Capability Heat Map

### Strongest Areas

- governed workflow operations
- service and post-purchase retail demos
- connector-backed order and CRM context
- channel onboarding and dispatch
- run persistence, replay, and operator visibility

### Emerging Areas

- shopper discovery and purchase assistance
- agent and skill registry maturity
- environment-aware promotion governance
- analytics and experiment surfaces

### Still Early Or Missing

- inventory and fulfillment promise integrations
- payment and fraud workflows
- richer CRM/CDP synchronization
- regional or brand-specific operating models
- full omnichannel production hardening

## Recommended Interpretation Of Current Scope

The most accurate reading of the code today is:

ACOS already provides a real retail service-operations slice, especially for order support and governed workflow operations, while discovery, purchase, and broader omnichannel capabilities are present but less mature.

## Near-Term Capability Direction

The most natural next steps from the current code are:
- deepen the order-support and service slice into a more complete live operational workflow
- expand workflow graph validation and policy enforcement
- make agent, skill, and connector registry behavior more production-grade
- extend retail coverage into richer fulfillment, returns, and loyalty operations
