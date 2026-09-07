const API_BASE_URL = "http://127.0.0.1:8000";


// =========================================================
// Authentication
// =========================================================

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  email: string;
  created_at: string;
}


// ---------------------------------------------------------
// Token Management
// ---------------------------------------------------------

const TOKEN_KEY = "intellidocs_access_token";

export function setAuthToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function removeAuthToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return getAuthToken() !== null;
}


// ---------------------------------------------------------
// Auth Headers
// ---------------------------------------------------------

function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken();

  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}


// =========================================================
// Register
// =========================================================

export async function registerUser(
  email: string,
  password: string
): Promise<UserResponse> {

  const response = await fetch(
    `${API_BASE_URL}/auth/register`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
      }),
    }
  );

  if (!response.ok) {
    let errorMessage = "Registration failed.";

    try {
      const errorData = await response.json();

      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(errorMessage);
  }

  return response.json();
}


// =========================================================
// Login
// =========================================================

export async function loginUser(
  email: string,
  password: string
): Promise<AuthResponse> {

  const response = await fetch(
    `${API_BASE_URL}/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
      }),
    }
  );

  if (!response.ok) {
    let errorMessage = "Login failed.";

    try {
      const errorData = await response.json();

      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(errorMessage);
  }

  const data: AuthResponse = await response.json();

  setAuthToken(data.access_token);

  return data;
}


// =========================================================
// Current User
// =========================================================

export async function getCurrentUser(): Promise<UserResponse> {

  const response = await fetch(
    `${API_BASE_URL}/auth/me`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  if (!response.ok) {
    let errorMessage = "Failed to fetch current user.";

    try {
      const errorData = await response.json();

      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(errorMessage);
  }

  return response.json();
}


// =========================================================
// Logout
// =========================================================

export function logoutUser(): void {
  removeAuthToken();
}


// =========================================================
// Document Upload
// =========================================================

export interface UploadResponse {
  message: string;
  document_id: number;
  filename: string;
  file_type: string;
  text_length: number;
  chunk_count: number;
  chunks: string[];
}

export async function uploadDocument(
  file: File
): Promise<UploadResponse> {

  const formData = new FormData();

  formData.append("file", file);

  const response = await fetch(
    `${API_BASE_URL}/documents/upload`,
    {
      method: "POST",
      headers: {
        ...getAuthHeaders(),
      },
      body: formData,
    }
  );

  if (!response.ok) {
    let errorMessage = "Failed to upload document.";

    try {
      const errorData = await response.json();

      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(errorMessage);
  }

  return response.json();
}


// =========================================================
// Chat
// =========================================================

export interface ChatSource {
  document_id: number;
  chunk_id: number;
  chunk_index: number;
}

export interface ChatResponse {
  session_id: number;
  question: string;
  answer: string;
  sources: ChatSource[];
}

export async function sendChatMessage(
  question: string,
  sessionId?: number
): Promise<ChatResponse> {

  const response = await fetch(
    `${API_BASE_URL}/chat/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify({
        question,
        top_k: 5,
        session_id: sessionId ?? null,
      }),
    }
  );

  if (!response.ok) {
    let errorMessage = "Failed to send message.";

    try {
      const errorData = await response.json();

      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(errorMessage);
  }

  return response.json();
}


// =========================================================
// Documents
// =========================================================

export interface DocumentResponse {
  document_id: number;
  filename: string;
  file_type: string;
  text_length: number | null;
  chunk_count: number;
  created_at: string;
}

export async function getDocuments(): Promise<DocumentResponse[]> {

  const response = await fetch(
    `${API_BASE_URL}/documents/`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  if (!response.ok) {
    let errorMessage = "Failed to fetch documents.";

    try {
      const errorData = await response.json();

      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(errorMessage);
  }

  return response.json();
}


// ---------------------------------------------------------
// Delete Document
// ---------------------------------------------------------

export async function deleteDocument(
  documentId: number
): Promise<{ message: string; document_id: number }> {

  const response = await fetch(
    `${API_BASE_URL}/documents/${documentId}`,
    {
      method: "DELETE",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  if (!response.ok) {
    let errorMessage = "Failed to delete document.";

    try {
      const errorData = await response.json();

      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(errorMessage);
  }

  return response.json();
}

// =========================================================
// Chat Sessions
// =========================================================

export interface ChatSession {
  session_id: number;
  title: string;
  created_at: string;
  message_count: number;
}

export interface ChatHistoryMessage {
  message_id: number;
  session_id: number;
  role: "user" | "assistant";
  content: string;
  sources: ChatSource[];
  created_at: string;
}


// ---------------------------------------------------------
// Get Chat Sessions
// ---------------------------------------------------------

export async function getChatSessions(): Promise<ChatSession[]> {

  const response = await fetch(
    `${API_BASE_URL}/chat/sessions/`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  if (!response.ok) {
    let errorMessage = "Failed to fetch chat sessions.";

    try {
      const errorData = await response.json();

      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(errorMessage);
  }

  return response.json();
}


// =========================================================
// Get Chat Messages
// =========================================================

export async function getChatMessages(
  sessionId: number
): Promise<ChatHistoryMessage[]> {

  const response = await fetch(
    `${API_BASE_URL}/chat/sessions/${sessionId}/messages`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    }
  );

  if (!response.ok) {
    let errorMessage = "Failed to fetch chat messages.";

    try {
      const errorData = await response.json();

      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(errorMessage);
  }

  return response.json();
}