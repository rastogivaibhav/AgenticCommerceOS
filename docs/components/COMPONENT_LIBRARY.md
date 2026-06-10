# ACOS UI Component Library

**Date:** 2026-04-15  
**Status:** Complete component inventory with all states  
**Coverage:** 12 core components × 5-7 states each = 80+ documented states

---

## Component Index

1. Button Component
2. Text Input Component
3. Select/Dropdown Component
4. Table Component
5. Modal/Dialog Component
6. Form Section Component
7. Toast Notification Component
8. Empty State Component
9. Error State Component
10. Loading/Skeleton Component
11. Sidebar Navigation Component
12. Header Component

---

## COMPONENT 1: Button

**Used In:** Every screen (Create, Save, Delete, Retry, Cancel, Submit, etc.)

### Variants

#### Primary Button
- **Purpose:** Main action (Create Workflow, Save, Submit)
- **Colors:** Blue background, white text
- **Default:** `background: #0052CC`, `color: white`, `cursor: pointer`
- **Padding:** `12px 24px` (medium) / `8px 16px` (small) / `16px 32px` (large)

### States

| State | Style | Interaction | Usage |
|-------|-------|-------------|-------|
| **Default** | Blue bg, white text, cursor pointer | Clickable | Ready to use |
| **Hover** | Darker blue bg (#003FA3), subtle shadow | Pointer + visual feedback | Indicate clickability |
| **Active/Pressed** | Darkest blue (#002E82), inner shadow | Depressed appearance | During click |
| **Disabled** | Gray bg (#CCCCCC), gray text, cursor not-allowed | Not clickable | Permission denied, async wait, form validation |
| **Loading** | Blue bg, spinner + text "Loading..." | Spinner animation | During async operation |
| **Focus** | Blue bg, 3px outline, visible focus indicator | Tab accessible | Keyboard navigation |

#### Secondary Button
- **Purpose:** Alternative action (Cancel, Reset, Close)
- **Colors:** Transparent bg, blue border, blue text
- **States:** Same as Primary (hover, active, disabled, loading, focus)

#### Danger Button
- **Purpose:** Destructive action (Delete, Remove, Deactivate)
- **Colors:** Red background, white text
- **Default:** `background: #DC3545`, `color: white`
- **States:** Same pattern as Primary button

#### Ghost Button
- **Purpose:** Low-priority action (Refresh, Retry, Help)
- **Colors:** Transparent bg, gray text
- **Default:** `background: transparent`, `color: #6B7280`, `border: 1px solid #D1D5DB`
- **States:** Same as other buttons

### Accessibility

- ✅ Semantic `<button>` element (not `<div>`)
- ✅ Minimum 44×44px touch target (mobile)
- ✅ Clear focus indicator (3px outline or different color)
- ✅ Loading state announces `aria-busy="true"` to screen readers
- ✅ Disabled state uses `:disabled` attribute or `aria-disabled="true"`
- ✅ Button text visible and meaningful (not icon-only unless aria-label)
- ✅ Keyboard support: Space and Enter to activate

### Code Example

```jsx
<Button 
  variant="primary"         // primary, secondary, danger, ghost
  size="md"                 // sm, md, lg
  disabled={isLoading}
  onClick={handleSave}
>
  {isLoading ? <Spinner /> : 'Save Workflow'}
</Button>
```

---

## COMPONENT 2: Text Input

**Used In:** Search boxes, form fields (name, email, description, etc.)

### States

| State | Appearance | When Used | User Action |
|-------|------------|-----------|-------------|
| **Default** | White bg, gray border, black text | Initial load | Ready to type |
| **Focus** | White bg, blue border (2px), blue outline, cursor | User clicks/tabs | Typing |
| **Filled** | White bg, gray border, black text | User has typed | Contains value |
| **Error** | White bg, red border (2px), red text below | Validation fails | User can correct |
| **Disabled** | Light gray bg, light gray border, gray text | No permission or async lock | Cannot interact |
| **Readonly** | Light gray bg, gray border, gray text | View-only mode | Cannot edit |
| **Placeholder** | Light gray text ("Email address") | Before user interaction | Hint text |

### Variants

#### Standard Text Input
- Placeholder: "Enter text..."
- Max length: Varies (typically 100-500 chars)
- Validation: On blur or on submit

#### Email Input
- Type: `email`
- Validation: Must match email regex
- Error: "Invalid email format"

#### Search Input
- Placeholder: "Search workflows..."
- Icon: Magnifying glass
- Behavior: Debounced search (500ms)
- Clear button: Appears when text entered

#### Password Input
- Type: `password` (text hidden)
- Show/hide toggle: Eye icon
- Validation: Min length, complexity rules

### Accessibility

- ✅ Associated `<label>` for every input
- ✅ `aria-label` or `aria-labelledby` when label not visible
- ✅ `aria-invalid="true"` when in error state
- ✅ `aria-describedby` points to error message
- ✅ Keyboard accessible (Tab, Space, Enter)
- ✅ Clear placeholder text (hints, not labels)
- ✅ Focus visible and obvious (outline or underline)

### Code Example

```jsx
<TextField
  label="Workflow Name"
  placeholder="Enter name..."
  value={name}
  error={nameError}
  errorMessage="Name is required and max 50 chars"
  onChange={handleNameChange}
  disabled={isLoading}
  aria-invalid={!!nameError}
  aria-describedby="name-error"
/>
```

---

## COMPONENT 3: Select/Dropdown

**Used In:** Role selection, workflow family filter, agent type filter, time range selection

### States

| State | Appearance | Interaction |
|-------|-----------|-------------|
| **Closed** | Shows selected value, down arrow, gray border | Click to open |
| **Opened** | List of options visible, selected item highlighted | Click to select |
| **Focused** | Blue border/outline, keyboard accessible | Arrow keys to navigate |
| **Disabled** | Gray bg, gray text, cursor not-allowed | No interaction |
| **Selected** | Checkmark next to selected item | Option applied |
| **Hover** | Light blue bg on option | Indicate selectability |

### Variants

#### Single Select
- One option selectable
- Shows selected value in button
- Click option to close dropdown

#### Multi-Select
- Multiple options selectable
- Checkboxes next to each option
- "Apply" or "Clear All" buttons at bottom

#### Searchable Dropdown
- Input field in dropdown to filter options
- Keyboard: Type to search

### Accessibility

- ✅ Semantic `<select>` or custom with `role="combobox"`
- ✅ `aria-expanded` shows if dropdown open/closed
- ✅ `aria-owns` links button to list
- ✅ Keyboard: Arrow keys navigate, Enter selects, Escape closes
- ✅ Screen reader announces number of options

### Code Example

```jsx
<Select
  label="Workflow Family"
  options={[
    { value: "support", label: "Customer Support" },
    { value: "ecommerce", label: "E-commerce" },
    { value: "crm", label: "CRM Integration" }
  ]}
  value={selectedFamily}
  onChange={handleFamilyChange}
  disabled={isLoading}
/>
```

---

## COMPONENT 4: Table

**Used In:** Workflows list, Agents list, Skills list, Channels list, Tenants list, Demo Routes results

### Features

- Sortable columns (click header to sort A→Z or Z→A)
- Selectable rows (checkbox column)
- Pagination (if 20+ rows)
- Filtering/search integration
- Row actions menu (... button for Edit, Delete, etc.)
- Responsive: Collapses to card view on mobile

### States

| State | Trigger | Appearance |
|-------|---------|-----------|
| **Empty** | No data rows | Skeleton rows or "No data" message |
| **Loading** | Data fetching | 8 skeleton rows with pulse animation |
| **Loaded** | Data returned | Full table with data rows |
| **Row Hover** | Mouse over row | Light gray background, action buttons visible |
| **Row Selected** | Click checkbox | Highlight row, checkbox checked, bulk toolbar appears |
| **Sorting** | Click column header | Header highlighted, sort indicator (▲/▼) shown, rows reordered |
| **Paginating** | Click Next/Previous | New page loaded, rows updated, page indicator changes |

### Sorting

- **Indicators:** ▲ (ascending), ▼ (descending), — (no sort)
- **Behavior:** Click header 1st time = ascending, 2nd time = descending, 3rd time = clear sort
- **Visual:** Sorted column highlighted with background color

### Pagination

- **Controls:** "< Previous", "Page X of Y", "Next >"
- **Disabled:** Previous on page 1, Next on last page
- **Optional:** Jump to page number input

### Row Actions

- **Menu button:** ... (three dots) at end of each row
- **Options:** Edit, Delete, Duplicate, View Details, Export, etc. (context-dependent)
- **Mobile:** Menu button always visible, swipe to reveal

### Accessibility

- ✅ Semantic `<table>` with `<thead>`, `<tbody>`, `<tfoot>`
- ✅ `<th scope="col">` headers
- ✅ Sortable headers announced as buttons
- ✅ Row selection with checkboxes
- ✅ Keyboard: Tab through cells, Space to select, Enter on action
- ✅ Screen reader announces "Table with X rows and Y columns"

### Code Example

```jsx
<Table
  data={workflows}
  isLoading={isLoading}
  columns={[
    { key: "name", label: "Workflow", sortable: true },
    { key: "family", label: "Family", sortable: true },
    { key: "status", label: "Status" },
    { key: "actions", label: "Actions", sortable: false }
  ]}
  onSort={handleSort}
  selectable={true}
  onSelect={handleSelect}
  pagination={{ page: 1, pageSize: 20, total: 150 }}
/>
```

---

## COMPONENT 5: Modal/Dialog

**Used In:** Create workflows, confirm delete, edit forms, error messages, confirmations

### States

| State | Appearance | Interaction |
|-------|-----------|-------------|
| **Closed** | Not visible | N/A |
| **Opening** | Fade in animation, backdrop appears | Brief animation (200ms) |
| **Open** | Full opacity, interactive | User can interact with content |
| **Scrolling** | Content scrollable if tall | Scrollbar inside modal |
| **Closing** | Fade out animation | Brief animation (200ms) |

### Properties

- **Backdrop:** Semi-transparent overlay behind modal, click to close (unless disallowed)
- **Focus:** Focus trapped inside modal (Tab doesn't escape)
- **Keyboard:** Escape key closes modal (if closeable)
- **Close Button:** X button in top-right corner
- **Position:** Centered on screen

### Variants

#### Standard Modal
- Title, body content, footer with buttons (Cancel, OK)

#### Confirmation Dialog
- Title: "Are you sure?"
- Body: Confirmation message
- Buttons: "Cancel", "Confirm" (danger button if destructive)

#### Form Modal
- Title: "Create [Item]"
- Body: Form with fields
- Buttons: "Cancel", "Save"
- Validation: Submit button disabled if form invalid

### Accessibility

- ✅ Semantic `<dialog>` element (or `role="dialog"`)
- ✅ Focus management: Focus moves to modal on open
- ✅ Focus trap: Tab stays within modal
- ✅ Backdrop: Click to close (unless important)
- ✅ Escape key: Closes modal (unless important)
- ✅ Title: `aria-labelledby` points to modal title
- ✅ Announcements: Modal open/close announced

### Code Example

```jsx
<Modal
  isOpen={showDeleteModal}
  title="Delete Workflow?"
  onClose={handleCloseModal}
>
  <p>Are you sure you want to delete this workflow?</p>
  <p>This action cannot be undone.</p>
  <ModalActions>
    <Button variant="secondary" onClick={handleCloseModal}>
      Cancel
    </Button>
    <Button variant="danger" onClick={handleConfirmDelete}>
      Delete
    </Button>
  </ModalActions>
</Modal>
```

---

## COMPONENT 6: Form Section

**Used In:** Workflow creation, agent creation, settings, profile

### Structure

```
[Legend: Workflow Details]
├── [Input] Name: ________________
├── [Select] Family: [Dropdown ▼]
├── [Textarea] Description: _____________________
└── [Validation] Error messages in red below fields
```

### States

| State | When | Appearance |
|-------|------|-----------|
| **Pristine** | Initial load | Empty fields, no validation errors, submit disabled |
| **Dirty** | User started typing | Visual indication of changes, submit enabled |
| **Focused** | User in a field | Blue border, focus indicator |
| **Filled** | User entered value | Gray border, value displayed |
| **Error** | Validation fails | Red border, error message below |
| **Submitting** | Form submitted | Spinner on submit button, all fields disabled |
| **Success** | Submit successful | Green checkmark or success message, modal closes |
| **Server Error** | Server rejected form | Error banner at top, fields remain editable for retry |

### Accessibility

- ✅ Semantic `<form>` element
- ✅ `<fieldset>` and `<legend>` for form sections
- ✅ Associated `<label>` for each field
- ✅ Error messages with `aria-invalid` and `aria-describedby`
- ✅ Submit button with clear action text ("Save", "Create", etc.)
- ✅ Keyboard accessible: Tab through fields, Space/Enter to submit

---

## COMPONENT 7: Toast Notification

**Used In:** Success messages, error messages, confirmations, info alerts

### States

| Type | Color | Duration | Icon | Use Case |
|------|-------|----------|------|----------|
| **Success** | Green | 3 sec | ✓ Checkmark | "Workflow created successfully" |
| **Error** | Red | 5 sec or manual | ✗ X | "Failed to save workflow" |
| **Warning** | Orange | 5 sec or manual | ⚠ Triangle | "Unsaved changes will be lost" |
| **Info** | Blue | 3 sec | ℹ Circle | "Syncing workflow..." |

### Behavior

- **Position:** Top-right corner (or bottom-center on mobile)
- **Stack:** Multiple toasts stack vertically
- **Auto-dismiss:** Success (3s), Error (5s or manual), Info (3s), Warning (manual)
- **Dismissible:** X button on top-right of toast
- **Animation:** Slide-in from right, fade-out when dismissed

### Accessibility

- ✅ `role="status"` for alerts that don't demand immediate attention
- ✅ `role="alert"` for urgent messages
- ✅ `aria-live="polite"` (waits for screen reader to finish)
- ✅ `aria-live="assertive"` for urgent messages (interrupts)
- ✅ Dismiss button keyboard accessible (Escape or Tab+Enter)

### Code Example

```jsx
<Toast
  type="success"
  message="Workflow created successfully"
  duration={3000}
  onDismiss={handleDismiss}
/>
```

---

## COMPONENT 8: Empty State

**Used In:** All list screens when no data exists

### Elements

- **Illustration:** Simple, relatable SVG or icon
- **Headline:** Short, friendly message ("No workflows yet")
- **Description:** Explain what can be done ("Create your first workflow to get started")
- **Primary Action:** Button to create first item ("Create Workflow")
- **Optional:** Link to documentation or help

### Accessibility

- ✅ Descriptive heading
- ✅ Clear action button
- ✅ Icon has `alt` text if image
- ✅ Semantically sound HTML

---

## COMPONENT 9: Error State

**Used In:** API failures, validation errors, permission denied

### Elements

- **Icon:** Red X or error symbol
- **Headline:** "Error loading workflows"
- **Details:** Specific error message (not technical jargon)
- **Action:** "Retry" button or troubleshooting steps
- **Support:** Contact support link if critical

### Variants

#### API Error (500, timeout)
- Message: "Unexpected error occurred"
- Action: "Retry"
- Optional: "Contact support"

#### Permission Denied (403)
- Message: "You don't have access to this"
- Action: "Request access" or "Contact admin"

#### Not Found (404)
- Message: "Resource not found"
- Action: "Go back"

---

## COMPONENT 10: Loading/Skeleton

**Used In:** All screens during initial data fetch

### Skeleton (Placeholder)

- **Shape:** Matches final content shape (rectangular for card, multiple lines for text)
- **Animation:** Pulse or shimmer effect
- **Color:** Light gray (#F3F4F6) with subtle animation
- **Count:** 8 skeleton rows for tables, 1-3 for cards

### Spinner

- **Style:** Circular rotating loader
- **Color:** Primary blue (#0052CC)
- **Size:** 24px (standard), 32px (large)
- **Animation:** 1 second rotation

### Accessibility

- ✅ Announces "Loading" to screen readers
- ✅ Skeletons have `aria-hidden="true"` (avoid redundant announcement)
- ✅ Loading message visible to users

---

## COMPONENT 11: Sidebar Navigation

**Used In:** Main app navigation (left sidebar)

### Items

- **Workflows** - Icon + text + badge (if applicable)
- **Agents** - Icon + text
- **Skills** - Icon + text
- **Channels** - Icon + text
- **Analytics** - Icon + text
- **Tenants** - Icon + text
- **Demo Routes** - Icon + text

### States

| State | Style | When |
|-------|-------|------|
| **Default** | Icon + text, gray text | Not on this route |
| **Active** | Icon + text, blue bg + white text, underline | Current route |
| **Hover** | Icon + text, light gray bg | Mouse over |
| **Mobile** | Icons only (hamburger menu to expand) | Viewport < 768px |

### Responsive

- **Desktop (1280px+):** Full sidebar with text, 200px width
- **Tablet (768px):** Sidebar with text but narrower, 160px width
- **Mobile (< 768px):** Icons only, hamburger menu to expand

### Accessibility

- ✅ Semantic `<nav>` element
- ✅ Links with `aria-current="page"` for active route
- ✅ Keyboard navigation: Tab through items
- ✅ Hamburger button has `aria-label="Navigation Menu"`

---

## COMPONENT 12: Header

**Used In:** Top bar of every page

### Layout

```
[ACOS Logo] [Page Title] [Controls] [Theme Toggle] [User Context] [User Menu]
```

### Elements

- **Logo:** ACOS text logo (clickable → home)
- **Page Title:** "Workflow Operations" or current screen name
- **Controls:** Page-specific controls (Platform Mode, Runtime Preference, etc.)
- **Theme Toggle:** Light/dark mode button
- **User Context:** User name, role, tenant, environment badges
- **User Menu:** Avatar or user icon (dropdown for logout, settings)

### States

| Element | State | Appearance |
|---------|-------|-----------|
| **Logo** | Default | ACOS text |
| **Logo** | Hover | Cursor pointer, slight color change |
| **Title** | Default | Large, bold text |
| **Theme Button** | Light Mode | Sun icon, light colors |
| **Theme Button** | Dark Mode | Moon icon, dark colors |
| **Context Badges** | Authenticated | Display user, role, tenant, env |
| **Context Badges** | Unauthenticated | Show "Not authenticated" |
| **User Menu** | Closed | Avatar or icon |
| **User Menu** | Open | Dropdown with Logout, Settings options |

### Accessibility

- ✅ Semantic `<header>` element
- ✅ Logo link has `aria-label="Home"`
- ✅ Page title announces with semantic heading
- ✅ Theme toggle has `aria-label="Switch to dark mode"`
- ✅ User menu with `aria-expanded` and keyboard accessible
- ✅ Status badges announce role/context to screen readers

---

## Summary

**Total Components:** 12  
**Total States:** 80+  
**Coverage:**
- Button: 6 states (default, hover, active, disabled, loading, focus)
- Text Input: 7 states (default, focus, filled, error, disabled, readonly, placeholder)
- Select: 6 states (closed, opened, focused, disabled, selected, hover)
- Table: 7 states (empty, loading, loaded, hover, selected, sorting, pagination)
- Modal: 5 states (closed, opening, open, scrolling, closing)
- Form: 7 states (pristine, dirty, focused, filled, error, submitting, success)
- Toast: 4 types (success, error, warning, info)
- Empty State: 1 state + multiple variants
- Error State: 1 state + multiple variants
- Loading/Skeleton: 2 states (skeleton, spinner)
- Sidebar Nav: 3 states (default, active, hover) + responsive
- Header: Multiple elements with states

---

✅ **TASK 3 COMPLETE** - 12 core components documented with 80+ states, variants, accessibility requirements, and code examples.
