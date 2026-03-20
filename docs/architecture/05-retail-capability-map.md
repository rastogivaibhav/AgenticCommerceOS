# ACOS Retail Capability Map

## Purpose

This document grounds ACOS in the real retail operating model.

ACOS should not be treated as a generic AI workflow platform with retail-themed examples.
It should be defined as the orchestration and governance layer across retail commerce capabilities.

## Strategic Positioning

ACOS is not intended to replace every retail system of record.

Instead, ACOS should sit as:
- the orchestration layer across retail systems
- the AI control plane for governed automation
- the workflow and policy layer for customer and operator journeys
- the operational analytics and intervention surface for AI-assisted commerce

## Retail Value Chain Coverage

ACOS should support the following retail domains.

## 1. Discovery And Merchandising

Business capabilities:
- search and browse assistance
- product discovery
- recommendations
- promotions explanation
- assortment and category guidance
- campaign-aware personalization

Typical systems involved:
- PIM
- search platform
- content platform
- recommendation engine
- pricing and promotions services

ACOS role:
- orchestrate discovery journeys
- apply tenant and campaign policy
- explain recommendations and offers
- route intents to deterministic domain services

## 2. Basket And Purchase

Business capabilities:
- product selection support
- price and offer calculation
- basket assistance
- checkout orchestration
- payment handoff
- fraud or policy checks

Typical systems involved:
- pricing engine
- promotions engine
- cart service
- checkout platform
- payment gateway
- fraud tooling

ACOS role:
- coordinate basket-building and purchase support
- provide AI assistance around deterministic cart and price actions
- apply approval or policy rules for risky actions

## 3. Fulfillment And Promise

Business capabilities:
- availability checks
- fulfillment option explanation
- delivery promise communication
- store pickup support
- shipment tracking visibility

Typical systems involved:
- inventory service
- OMS
- WMS
- shipping and carrier integrations
- store systems

ACOS role:
- orchestrate customer and operator interactions around fulfillment
- expose promise logic and exceptions through governed workflows

## 4. Post-Purchase Service

Business capabilities:
- order status support
- cancellation handling
- change requests
- return and exchange initiation
- refund status
- complaint handling

Typical systems involved:
- OMS
- service platform or CRM
- returns platform
- payment and refund services
- logistics providers

ACOS role:
- orchestrate post-purchase workflows
- apply service policies and approval gates
- capture run history, handoffs, and outcome quality

## 5. Loyalty And Customer Growth

Business capabilities:
- loyalty status and benefits
- points earning and redemption
- referral management
- retention and win-back journeys
- customer value segmentation

Typical systems involved:
- loyalty platform
- CRM or CDP
- campaign management
- customer analytics

ACOS role:
- combine customer context, policy, and workflow orchestration
- manage governed AI-driven engagement journeys

## 6. Operator And Commerce Team Support

Business capabilities:
- incident investigation
- journey replay
- workflow tuning
- agent and skill governance
- campaign and pricing analysis
- escalation handling

Typical systems involved:
- control plane
- observability stack
- analytics tools
- ticketing or ITSM
- experimentation tooling

ACOS role:
- serve as the control plane for operational oversight and intervention

## Systems Of Record And Systems Of Intelligence

### Systems Of Record
These remain authoritative:
- PIM
- OMS
- payments
- WMS
- inventory
- CRM
- loyalty ledger

### Systems Of Intelligence
ACOS belongs here, but with governed write access:
- intent understanding
- workflow selection
- AI-assisted reasoning
- run evaluation
- experimentation support
- operator guidance

## Retail Persona Coverage

The platform should serve:
- ecommerce operations
- contact center operations
- merchandising
- loyalty and CRM teams
- platform engineering
- risk and compliance
- store or fulfillment operations where relevant

## Retail KPI Model

ACOS success should be measured against retail outcomes, not only platform health.

### Customer KPIs
- containment rate
- first-contact resolution
- service CSAT
- time to resolution
- delivery promise clarity

### Commercial KPIs
- conversion support rate
- average order value influence
- promotion uptake
- return rate influence
- loyalty redemption and retention impact

### Operational KPIs
- escalation rate
- replay volume
- manual override rate
- workflow failure rate
- run latency

### Financial KPIs
- cost per resolved interaction
- automation savings
- support cost avoidance
- margin protection through governed offers

## Retail Capability Heat Map

### Current Strength
- discovery support
- purchase guidance
- post-purchase and returns prototype
- run history and replay prototype

### Emerging Capability
- workflow governance
- control-plane operations
- policy-driven execution
- experiment and evaluation operations

### Missing But Strategic
- inventory and fulfillment promise
- payments and fraud governance
- CRM and CDP integration
- store operations support
- campaign-aware and merchandising workflows

## Recommended Retail Scope Sequence

### Phase 1
Digital commerce and service foundations:
- discovery
- purchase support
- order tracking
- returns
- loyalty

### Phase 2
Enterprise retail operating model:
- fulfillment promise
- customer care operations
- promotion and campaign governance
- experiment operations

### Phase 3
Omnichannel control plane:
- store operations
- cross-channel journeys
- advanced approval and exception handling
- brand and region operating models

## Architectural Implication

To fulfill the vision of an operating system behind AI-driven commerce, ACOS must be designed to orchestrate across the retail capability map rather than embed all business logic inside itself.

That means:
- deterministic integration with systems of record
- workflow and policy orchestration in ACOS
- clear operator control over execution and exceptions
