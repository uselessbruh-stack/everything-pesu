import { useState, useEffect, useCallback } from 'react';

/**
 * Reusable async data-fetching hook.
 * @param {Function} asyncFn  — Function that returns a Promise
 * @param {boolean}  immediate — Fire on mount?
 */
export function useAsync(asyncFn, immediate = true) {
  const [state, setState] = useState({
    status: immediate ? 'pending' : 'idle',
    data: null,
    error: null,
  });

  const execute = useCallback(async () => {
    setState({ status: 'pending', data: null, error: null });
    try {
      const data = await asyncFn();
      setState({ status: 'success', data, error: null });
      return data;
    } catch (error) {
      const message =
        error?.response?.data?.detail || error.message || 'Something went wrong';
      setState({ status: 'error', data: null, error: message });
      throw error;
    }
  }, [asyncFn]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return { ...state, execute, isLoading: state.status === 'pending' };
}
