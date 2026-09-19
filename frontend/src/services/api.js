import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const ingestUrl = async (url) => {
  const response = await axios.post(`${API_URL}/ingest/`, { url });
  return response.data;
};

export const getStats = async () => {
  const response = await axios.get(`${API_URL}/dashboard/stats`);
  return response.data;
};

export const getQueue = async () => {
  const response = await axios.get(`${API_URL}/dashboard/queue`);
  return response.data;
};

export const getConcepts = async () => {
  const response = await axios.get(`${API_URL}/dashboard/concepts`);
  return response.data;
};
