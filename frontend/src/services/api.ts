const API_URL = import.meta.env.VITE_API_URL;

export async function askQuestion(question: string): Promise<{ answer: string; sources: string[] }> {
  const response = await fetch(`${API_URL}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}