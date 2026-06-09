import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeAll } from 'vitest';
import Simulation from './Simulation';

vi.mock('../api/northstarAPI', () => ({
  getNorthstarRuns: vi.fn().mockResolvedValue({ runs: [{ id: 'run-1' }, { id: 'run-2' }] }),
  runNorthstarMessage: vi.fn().mockResolvedValue({ status: 'success' }),
}));

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
        {nodes.map((node) => (
          <div key={node.id} data-testid={`node-${node.id}`}>{node.data.label}</div>
        ))}
        {children}
      </div>
    ),
    Background: () => <div data-testid="rf-background" />,
    Controls: () => <div data-testid="rf-controls" />,
    MiniMap: () => <div data-testid="rf-minimap" />,
  };
});

describe('Simulation View Component', () => {
  it('renders the header and controls', () => {
    render(<Simulation />);
    expect(screen.getByText('Journey Planner & Run Monitor')).toBeInTheDocument();
    expect(screen.getByText('Captured Runs')).toBeInTheDocument();
    expect(screen.getByText('Create sample run')).toBeInTheDocument();
  });

  it('renders nodes from the default flow state', () => {
    render(<Simulation />);
    expect(screen.getByTestId('react-flow-mock')).toBeInTheDocument();
    expect(screen.getByText('Marketing (Acquisition)')).toBeInTheDocument();
    expect(screen.getByText('Discovery (Search/Browse)')).toBeInTheDocument();
    expect(screen.getByText('Customer Service')).toBeInTheDocument();
  });

  it('keeps the captured-runs monitor visible', () => {
    render(<Simulation />);
    const monitorButton = screen.getByText('Captured Runs');
    fireEvent.click(monitorButton);
    expect(screen.getByText(/latest runs:/i)).toBeInTheDocument();
  });
});
