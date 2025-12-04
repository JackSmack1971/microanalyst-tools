import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import { analyzeToken } from './services/api';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (token) => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeToken(token);
      setData(result);
    } catch (err) {
      console.error(err);
      setError(`Failed to analyze token '${token}'. Please check the symbol and try again.`);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dashboard
      data={data}
      loading={loading}
      error={error}
      onSearch={handleSearch}
    />
  );
}

export default App;
