import React from 'react';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, test, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { LoginPage } from '../src/pages/LoginPage';

const login = vi.hoisted(() => vi.fn());
vi.mock('../src/context/AuthContext', () => ({ useAuth: () => ({ login }) }));
afterEach(() => {
  cleanup();
  login.mockReset();
});

test('customers can sign in by using labeled controls', async () => {
  login.mockResolvedValue({ role: 'CUSTOMER' });
  render(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/customer" element={<h1>Customer dashboard</h1>} />
      </Routes>
    </MemoryRouter>,
  );
  const user = userEvent.setup();
  await user.type(screen.getByLabelText('Email Address'), 'driver@example.com');
  await user.type(screen.getByLabelText('Password'), 'test-password-123');
  await user.click(screen.getByRole('button', { name: 'Sign In to Network' }));
  expect(login).toHaveBeenCalledWith({
    email: 'driver@example.com',
    password: 'test-password-123',
  });
  expect(await screen.findByRole('heading', { name: 'Customer dashboard' })).toBeTruthy();
});
