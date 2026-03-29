import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the search view', () => {
  render(<App />);
  expect(screen.getByText(/Job Assistant/i)).toBeInTheDocument();
  expect(screen.getByText(/Search jobs/i)).toBeInTheDocument();
});
