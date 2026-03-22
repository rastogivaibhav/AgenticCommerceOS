import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Agents from './Agents';

describe('Agents View Component', () => {
  it('renders the core title and layout', () => {
    render(<Agents />);
    expect(screen.getByText('System Agents')).toBeInTheDocument();
    expect(screen.getByText('Monitor and manage the autonomous agents across diverse operational domains.')).toBeInTheDocument();
  });

  it('renders a list of agent cards', () => {
    render(<Agents />);
    // Verify an agent from the MOCK_AGENTS list is rendered
    expect(screen.getByText('Campaign Manager')).toBeInTheDocument();
    expect(screen.getByText('Returns Processor')).toBeInTheDocument();
  });

  it('opens the agent detail widget when an agent card is clicked', () => {
    render(<Agents />);
    
    // The widget shouldn't show "Agent Editor" initially
    const managerCard = screen.getByText('Campaign Manager').closest('tr');
    fireEvent.click(managerCard);

    // After click, the Editor Widget should appear showing details
    expect(screen.getByText('Agent Editor')).toBeInTheDocument();
    expect(screen.getByText('Associated Skills')).toBeInTheDocument();
  });
});
