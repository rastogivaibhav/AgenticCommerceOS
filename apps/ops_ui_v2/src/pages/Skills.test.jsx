import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Skills from './Skills';

// Mock the Monaco Editor since JSDOM doesn't support the layout engine features it requires
vi.mock('@monaco-editor/react', () => {
  return {
    default: ({ value }) => <div data-testid="monaco-mock">{value}</div>
  };
});

describe('Skills View Component', () => {
  it('renders the core title and table structure', () => {
    render(<Skills />);
    expect(screen.getByText('Skill Library')).toBeInTheDocument();
    expect(screen.getByText('Browse and manage pluggable skills, API integrations, and utilities used by agents.')).toBeInTheDocument();
  });

  it('renders a list of available skills in the table', () => {
    render(<Skills />);
    expect(screen.getByText('Catalog Search')).toBeInTheDocument();
    expect(screen.getByText('Process Refund')).toBeInTheDocument();
  });

  it('opens the skill editor widget when a table row is clicked', () => {
    render(<Skills />);
    
    const skillRow = screen.getByText('Catalog Search').closest('tr');
    fireEvent.click(skillRow);

    // Widget should appear
    expect(screen.getByText('Skill Editor')).toBeInTheDocument();
    expect(screen.getByText(/Static Analysis/)).toBeInTheDocument();
    
    // Check if Monaco mock is rendered
    expect(screen.getByTestId('monaco-mock')).toBeInTheDocument();
  });
});
