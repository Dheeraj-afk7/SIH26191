/**
 * SIH26191 Central HTTP Client Wrapper
 */

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      'Accept': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errBody = await response.json();
      if (errBody?.detail) {
        errorDetail = typeof errBody.detail === 'string' ? errBody.detail : JSON.stringify(errBody.detail);
      }
    } catch {
      // Body is not JSON
    }
    throw new ApiError(`API Request failed (${response.status}): ${errorDetail}`, response.status);
  }

  return response.json();
}
