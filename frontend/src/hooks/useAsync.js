import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Reusable async execution hook.
 * Handles loading status, results caching, and memory leaks on unmount.
 */
export function useAsync(asyncFunction, immediate = true, dependencies = []) {
  const [status, setStatus] = useState('idle');
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  
  const isMounted = useRef(true);
  
  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const execute = useCallback(async (...args) => {
    if (isMounted.current) {
      setStatus('pending');
      setError(null);
    }
    
    try {
      const result = await asyncFunction(...args);
      if (isMounted.current) {
        setData(result);
        setStatus('success');
      }
      return result;
    } catch (err) {
      if (isMounted.current) {
        setError(err);
        setStatus('error');
      }
      throw err;
    }
  }, [asyncFunction]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);

  return {
    status,
    data,
    error,
    execute,
    isLoading: status === 'pending' || status === 'idle',
    isSuccess: status === 'success',
    isError: status === 'error'
  };
}
