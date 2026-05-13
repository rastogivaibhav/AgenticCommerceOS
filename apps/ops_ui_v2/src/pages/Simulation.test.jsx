import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeAll } from 'vitest';
import Simulation from './Simulation';

// React Flow requires ResizeObserver to be mocked in jsdom environments
beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

// Mock React Flow to avoid complex DOM SVG layout errors in JSDOM
vi.mock('reactflow', async () => {
  const actual = await vi.importActual('reactflow');
  return {
    ...actual,
    default: ({ children, nodes }) => (
      <div data-testid="react-flow-mock">
        {nodes.map(n => (
          <div key={n.id} data-testid={`node-${n.id}`}>{n.data.label}</div>
        ))}
        {children}
      </div>
    ),
    Background: () => <div data-testid="rf-background" />,
    Controls: () => <div data-testid="rf-controls" />,
    MiniMap: () => <div data-testid="rf-minimap" />
  };
});

describe('Simulation View Component', () => {
  it('renders the header and controls', () => {
    render(<Simulation />);
    expect(screen.getByText('Journey Planner & Simulation')).toBeInTheDocument();
    expect(screen.getByText('Builder')).toBeInTheDocument();
    expect(screen.getByText('Live Traffic')).toBeInTheDocument();
  });

  it('renders nodes from the default flow state', () => {
    render(<Simulation />);
    expect(screen.getByTestId('react-flow-mock')).toBeInTheDocument();
    
    // Check for specific node labels
    expect(screen.getByText('Marketing (Acquisition)')).toBeInTheDocument();
    expect(screen.getByText('Discovery (Search/Browse)')).toBeInTheDocument();
    expect(screen.getByText('Customer Service')).toBeInTheDocument();
  });

  it('toggles the mode from Builder to Live Traffic', () => {
    render(<Simulation />);
    
    // Default is builder mode, so toolbox displays
    expect(screen.getByText('Drag Agents')).toBeInTheDocument();
    expect(screen.getByText('Returns Bot')).toBeInTheDocument();

    const liveBtn = screen.getByText('Live Traffic');
    fireEvent.click(liveBtn);

    // Live mode removes the toolbox and adds an overlay banner
    expect(screen.queryByText('Drag Agents')).not.toBeInTheDocument();
    expect(screen.getByText('Live execution traffic flowing...')).toBeInTheDocument();
  });
});
