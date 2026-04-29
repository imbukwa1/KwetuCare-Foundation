import { render, screen } from '@testing-library/react';
import App from './App';

test('renders Kwetu Care login screen', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
});
