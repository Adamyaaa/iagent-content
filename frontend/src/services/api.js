import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const ingestUrl = async (url, platform) => {
  const response = await axios.post(`${API_URL}/ingest/`, { url, source_platform: platform });
  return response.data;
};

export const ingestUpload = async (file, platform) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_platform', platform);
  const response = await axios.post(`${API_URL}/ingest/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
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

export const deleteQueueItem = async (queueId) => {
  const response = await axios.delete(`${API_URL}/dashboard/queue/${queueId}`);
  return response.data;
};

export const getConcepts = async () => {
  const response = await axios.get(`${API_URL}/dashboard/concepts`);
  return response.data;
};
