import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  uploadDocument,
  deleteDocument,
  sendChatMessage,
  getDocuments,
  getChatSessions,
  getChatMessages,
  isAuthenticated,
  loginUser,
  registerUser,
  getCurrentUser,
  logoutUser,
} from "./services/api";


// =========================================================
// Types
// =========================================================

interface UploadedDocument {
  document_id: number;
  filename: string;
  file_type: string;
  text_length: number | null;
  chunk_count: number;
  created_at: string;
}

interface ChatSource {
  document_id: number;
  chunk_id: number;
  chunk_index: number;
  filename?: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
}

interface ChatSession {
  session_id: number;
  title: string;
  created_at: string;
  message_count: number;
}

interface CurrentUser {
  id: number;
  email: string;
  created_at: string;
}


// =========================================================
// App
// =========================================================

function App() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // =========================================================
  // Authentication
  // =========================================================

  const [authenticated, setAuthenticated] = useState(
    isAuthenticated()
  );

  const [authMode, setAuthMode] = useState<
    "login" | "register"
  >("login");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [currentUser, setCurrentUser] =
    useState<CurrentUser | null>(null);

  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(
    null
  );


  // =========================================================
  // Documents
  // =========================================================

  const [documents, setDocuments] =
    useState<UploadedDocument[]>([]);

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] =
    useState<string | null>(null);

  const [documentsLoading, setDocumentsLoading] =
    useState(true);

  const [deletingDocumentId, setDeletingDocumentId] =
  useState<number | null>(null);


  // =========================================================
  // Chat
  // =========================================================

  const [question, setQuestion] = useState("");
  const [messages, setMessages] =
    useState<ChatMessage[]>([]);

  const [sending, setSending] = useState(false);
  const [chatError, setChatError] =
    useState<string | null>(null);


  // =========================================================
  // Chat Sessions
  // =========================================================

  const [chatSessions, setChatSessions] =
    useState<ChatSession[]>([]);

  const [chatSessionsLoading, setChatSessionsLoading] =
    useState(true);

  const [chatHistoryError, setChatHistoryError] =
    useState<string | null>(null);

  const [sessionId, setSessionId] =
    useState<number | undefined>(undefined);


  // =========================================================
  // Verify existing authentication
  // =========================================================

  useEffect(() => {
    if (!isAuthenticated()) {
      setAuthenticated(false);
      setDocumentsLoading(false);
      setChatSessionsLoading(false);
      return;
    }

    const verifyAuthentication = async () => {
      try {
        const user = await getCurrentUser();

        setCurrentUser(user);
        setAuthenticated(true);
      } catch {
        logoutUser();
        setAuthenticated(false);
        setCurrentUser(null);
      }
    };

    verifyAuthentication();
  }, []);

  useEffect(() => {
  messagesEndRef.current?.scrollIntoView({
    behavior: "smooth",
  });
}, [messages, sending]);

  // =========================================================
  // Load application data
  // =========================================================

  useEffect(() => {
    if (!authenticated) {
      return;
    }

    const loadInitialData = async () => {
      try {
        setDocumentsLoading(true);
        setChatSessionsLoading(true);

        const [
          documentResult,
          sessionResult,
        ] = await Promise.all([
          getDocuments(),
          getChatSessions(),
        ]);

        setDocuments(documentResult);
        setChatSessions(sessionResult);
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Failed to load application data.";

        setUploadError(message);
        setChatHistoryError(message);
      } finally {
        setDocumentsLoading(false);
        setChatSessionsLoading(false);
      }
    };

    loadInitialData();
  }, [authenticated]);


  // =========================================================
  // Login
  // =========================================================

  const handleLogin = async () => {
    const trimmedEmail = email.trim();

    if (!trimmedEmail || !password) {
      setAuthError(
        "Please enter your email and password."
      );
      return;
    }

    setAuthError(null);
    setAuthLoading(true);

    try {
      await loginUser(
        trimmedEmail,
        password
      );

      const user = await getCurrentUser();

      setCurrentUser(user);
      setAuthenticated(true);

      setEmail("");
      setPassword("");
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Login failed.";

      setAuthError(message);
    } finally {
      setAuthLoading(false);
    }
  };


  // =========================================================
  // Register
  // =========================================================

  const handleRegister = async () => {
    const trimmedEmail = email.trim();

    if (!trimmedEmail || !password) {
      setAuthError(
        "Please enter an email and password."
      );
      return;
    }

    if (password.length < 6) {
      setAuthError(
        "Password must contain at least 6 characters."
      );
      return;
    }

    setAuthError(null);
    setAuthLoading(true);

    try {
      await registerUser(
        trimmedEmail,
        password
      );

      // Automatically switch to login after registration.
      setAuthMode("login");

      setPassword("");

      setAuthError(
        "Registration successful. Please log in."
      );
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Registration failed.";

      setAuthError(message);
    } finally {
      setAuthLoading(false);
    }
  };


  // =========================================================
  // Logout
  // =========================================================

  const handleLogout = () => {
    logoutUser();

    setAuthenticated(false);
    setCurrentUser(null);

    setDocuments([]);
    setChatSessions([]);
    setMessages([]);
    setSessionId(undefined);

    setQuestion("");

    setUploadError(null);
    setChatError(null);
    setChatHistoryError(null);

    setEmail("");
    setPassword("");
    setAuthError(null);

    setAuthMode("login");
  };


  // =========================================================
  // Authentication Form
  // =========================================================

  const handleAuthSubmit = (
    event: React.FormEvent
  ) => {
    event.preventDefault();

    if (authMode === "login") {
      handleLogin();
    } else {
      handleRegister();
    }
  };


  // =========================================================
  // Upload Document
  // =========================================================

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };


  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setUploadError(null);
    setUploading(true);

    try {
      await uploadDocument(file);

      const updatedDocuments =
        await getDocuments();

      setDocuments(updatedDocuments);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to upload document.";

      setUploadError(message);
    } finally {
      setUploading(false);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  // =========================================================
// Delete Document
// =========================================================

const handleDeleteDocument = async (documentId: number) => {
  const document = documents.find(
    (item) => item.document_id === documentId
  );

  if (!document || deletingDocumentId !== null) {
    return;
  }

  const confirmed = window.confirm(
    `Are you sure you want to delete "${document.filename}"?`
  );

  if (!confirmed) {
    return;
  }

  setUploadError(null);
  setDeletingDocumentId(documentId);

  try {
    await deleteDocument(documentId);

    setDocuments((currentDocuments) =>
      currentDocuments.filter(
        (item) => item.document_id !== documentId
      )
    );
  } catch (error) {
    console.error("Failed to delete document:", error);

    const message =
      error instanceof Error
        ? error.message
        : "Failed to delete document.";

    setUploadError(message);
  } finally {
    setDeletingDocumentId(null);
  }
};


  // =========================================================
  // Send Chat Message
  // =========================================================

  const handleSendMessage = async () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || sending) {
      return;
    }

    setChatError(null);

    const userMessage: ChatMessage = {
      role: "user",
      content: trimmedQuestion,
    };

    setMessages((current) => [
      ...current,
      userMessage,
    ]);

    setQuestion("");
    setSending(true);

    try {
      const result = await sendChatMessage(
        trimmedQuestion,
        sessionId
      );

      setSessionId(result.session_id);

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: result.answer,
        sources: result.sources,
      };

      setMessages((current) => [
        ...current,
        assistantMessage,
      ]);

      const updatedSessions =
        await getChatSessions();

      setChatSessions(updatedSessions);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to send message.";

      setChatError(message);
    } finally {
      setSending(false);
    }
  };


  // =========================================================
  // Load Previous Conversation
  // =========================================================

  const handleSelectChat = async (
    selectedSessionId: number
  ) => {
    if (sending) {
      return;
    }

    setChatError(null);
    setChatHistoryError(null);

    try {
      const history =
        await getChatMessages(
          selectedSessionId
        );

      const restoredMessages: ChatMessage[] =
        history.map((message) => ({
          role: message.role,
          content: message.content,
          sources: message.sources,
        }));

      setMessages(restoredMessages);
      setSessionId(selectedSessionId);
      setQuestion("");
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to load conversation.";

      setChatHistoryError(message);
    }
  };


  // =========================================================
  // New Chat
  // =========================================================

  const handleNewChat = () => {
    setMessages([]);
    setQuestion("");
    setChatError(null);
    setChatHistoryError(null);
    setSessionId(undefined);
  };


  // =========================================================
  // Enter Key
  // =========================================================

  const handleQuestionKeyDown = (
    event: React.KeyboardEvent<HTMLInputElement>
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      handleSendMessage();
    }
  };


  // =========================================================
  // Format Session Date
  // =========================================================

  const formatSessionDate = (
    createdAt: string
  ) => {
    const date = new Date(createdAt);

    return date.toLocaleString([], {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };


  // =========================================================
  // Login / Register UI
  // =========================================================

  if (!authenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-white">

        <div className="w-full max-w-md">

          <div className="mb-8 text-center">

            <div className="mb-4 text-5xl">
              🤖
            </div>

            <h1 className="text-3xl font-bold">
              IntelliDocs AI
            </h1>

            <p className="mt-2 text-sm text-slate-400">
              Document Intelligence & RAG Assistant
            </p>

          </div>


          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-7 shadow-xl">

            <div className="mb-6 flex rounded-lg bg-slate-800 p-1">

              <button
                type="button"
                onClick={() => {
                  setAuthMode("login");
                  setAuthError(null);
                }}
                className={
                  authMode === "login"
                    ? "flex-1 rounded-md bg-white px-4 py-2 text-sm font-semibold text-slate-900"
                    : "flex-1 rounded-md px-4 py-2 text-sm text-slate-400 hover:text-white"
                }
              >
                Login
              </button>

              <button
                type="button"
                onClick={() => {
                  setAuthMode("register");
                  setAuthError(null);
                }}
                className={
                  authMode === "register"
                    ? "flex-1 rounded-md bg-white px-4 py-2 text-sm font-semibold text-slate-900"
                    : "flex-1 rounded-md px-4 py-2 text-sm text-slate-400 hover:text-white"
                }
              >
                Register
              </button>

            </div>


            <form
              onSubmit={handleAuthSubmit}
              className="space-y-4"
            >

              <div>

                <label className="mb-2 block text-sm font-medium text-slate-300">
                  Email
                </label>

                <input
                  type="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  placeholder="you@example.com"
                  autoComplete="email"
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none placeholder:text-slate-600 focus:border-slate-500"
                />

              </div>


              <div>

                <label className="mb-2 block text-sm font-medium text-slate-300">
                  Password
                </label>

                <input
                  type="password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="••••••••"
                  autoComplete={
                    authMode === "login"
                      ? "current-password"
                      : "new-password"
                  }
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none placeholder:text-slate-600 focus:border-slate-500"
                />

              </div>


              {authError && (
                <div className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-slate-300">
                  {authError}
                </div>
              )}


              <button
                type="submit"
                disabled={authLoading}
                className="w-full rounded-lg bg-white px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {authLoading
                  ? "Please wait..."
                  : authMode === "login"
                    ? "Login"
                    : "Create Account"}
              </button>

            </form>

          </div>

        </div>

      </div>
    );
  }


  // =========================================================
  // Main Application UI
  // =========================================================

  return (
    <div className="min-h-screen bg-slate-950 text-white">

      {/* Header */}

<header className="flex min-h-16 items-center justify-between gap-3 border-b border-slate-800 px-4 sm:px-6">
        <div>

          <h1 className="text-xl font-bold">
            IntelliDocs AI
          </h1>

          <p className="text-xs text-slate-400">
            Document Intelligence & RAG Assistant
          </p>

        </div>


        <div className="flex items-center gap-2 sm:gap-4">

          {currentUser && (
            <div className="hidden text-right sm:block">

              <p className="text-sm font-medium text-slate-200">
                {currentUser.email}
              </p>

              <p className="text-xs text-slate-500">
                Authenticated user
              </p>

            </div>
          )}


          <button
            onClick={handleNewChat}
            className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-slate-900 hover:bg-slate-200"
          >
            + New Chat
          </button>


          <button
            onClick={handleLogout}
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            Logout
          </button>

        </div>

      </header>


      <div className="flex h-[calc(100vh-4rem)]">

        {/* =================================================
            Sidebar
        ================================================= */}

        <aside className="hidden w-72 shrink-0 overflow-y-auto border-r border-slate-800 p-5 md:block">

          {/* Documents */}

          <div className="mb-8">

            <h2 className="mb-3 text-sm font-semibold text-slate-300">
              Documents
            </h2>


            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileChange}
              className="hidden"
            />


            <button
              onClick={handleUploadClick}
              disabled={uploading}
              className="w-full rounded-lg border border-dashed border-slate-700 px-4 py-6 text-sm text-slate-400 transition hover:border-slate-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {uploading
                ? "Uploading..."
                : "Upload Document"}
            </button>


            {uploadError && (
              <div className="mt-3 rounded-lg border border-red-900 bg-red-950/40 p-3 text-xs text-red-300">
                {uploadError}
              </div>
            )}


            <div className="mt-4 space-y-2">

              {documentsLoading ? (

                <div className="rounded-lg bg-slate-900 px-4 py-3 text-sm text-slate-500">
                  Loading documents...
                </div>

              ) : documents.length === 0 ? (

                <div className="rounded-lg bg-slate-900 px-4 py-3 text-sm text-slate-500">
                  No documents uploaded
                </div>

              ) : (

                documents.map((document) => (

<div
  key={document.document_id}
  className="rounded-lg bg-slate-900 p-3"
>
  <div className="flex items-start gap-3">

    <div className="min-w-0 flex-1">
      <p className="truncate text-sm font-medium text-slate-200">
        {document.filename}
      </p>

      <p className="mt-1 text-xs text-slate-500">
        {document.chunk_count} chunks
      </p>
    </div>

    <button
      type="button"
      onClick={() =>
        handleDeleteDocument(document.document_id)
      }
      disabled={deletingDocumentId !== null}
      title="Delete document"
      aria-label={`Delete ${document.filename}`}
      className="shrink-0 rounded-md px-2 py-1 text-xs text-slate-500 transition hover:bg-red-950/60 hover:text-red-400 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {deletingDocumentId === document.document_id
        ? "..."
        : "🗑️"}
    </button>

  </div>
</div>

                ))

              )}

            </div>

          </div>


          {/* Chat History */}

          <div>

            <h2 className="mb-3 text-sm font-semibold text-slate-300">
              Chat History
            </h2>


            {chatHistoryError && (
              <div className="mb-3 rounded-lg border border-red-900 bg-red-950/40 p-3 text-xs text-red-300">
                {chatHistoryError}
              </div>
            )}


            {chatSessionsLoading ? (

              <div className="rounded-lg bg-slate-900 px-4 py-3 text-sm text-slate-500">
                Loading conversations...
              </div>

            ) : chatSessions.length === 0 ? (

              <div className="rounded-lg bg-slate-900 px-4 py-3 text-sm text-slate-500">
                No conversations yet
              </div>

            ) : (

              <div className="space-y-2">

                {chatSessions.map((session) => (

                  <button
                    key={session.session_id}
                    onClick={() =>
                      handleSelectChat(
                        session.session_id
                      )
                    }
                    disabled={sending}
                    className={
                      session.session_id === sessionId
                        ? "w-full rounded-lg border border-slate-600 bg-slate-800 p-3 text-left transition"
                        : "w-full rounded-lg bg-slate-900 p-3 text-left transition hover:bg-slate-800"
                    }
                  >

                    <p className="truncate text-sm font-medium text-slate-200">
                      {session.title}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      {session.message_count} messages
                    </p>

                    <p className="mt-1 text-xs text-slate-600">
                      {formatSessionDate(
                        session.created_at
                      )}
                    </p>

                  </button>

                ))}

              </div>

            )}

          </div>

        </aside>


        {/* =================================================
            Main Chat
        ================================================= */}

        <main className="flex flex-1 flex-col">

          {/* Messages */}

         <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">

            {messages.length === 0 ? (

              <div className="flex h-full items-center justify-center">

                <div className="max-w-2xl text-center">

                  <div className="mb-6 text-5xl">
                    🤖
                  </div>

                  <h2 className="mb-3 text-3xl font-bold">
                    Welcome to IntelliDocs AI
                  </h2>

                  <p className="text-slate-400">
                    Upload your documents and ask questions
                    using AI-powered semantic search and RAG.
                  </p>

                </div>

              </div>

            ) : (

<div className="mx-auto w-full max-w-4xl space-y-6">

                {messages.map((message, index) => (

                  <div
                    key={index}
                    className={
                      message.role === "user"
                        ? "flex justify-end"
                        : "flex justify-start"
                    }
                  >

                    <div
                      className={
                        message.role === "user"
? "max-w-[90%] rounded-2xl bg-white px-4 py-3 text-sm text-slate-900 sm:max-w-[80%]"
: "max-w-[90%] rounded-2xl bg-slate-900 px-4 py-3 text-sm leading-6 text-slate-200 sm:max-w-[80%]"
                      }
                    >

                     <div className="space-y-2 leading-7 text-slate-200">
  <ReactMarkdown
    remarkPlugins={[remarkGfm]}
    components={{
      h1: ({ children }) => (
        <h1 className="text-xl font-bold text-white">
          {children}
        </h1>
      ),
      h2: ({ children }) => (
        <h2 className="text-lg font-bold text-white">
          {children}
        </h2>
      ),
      h3: ({ children }) => (
        <h3 className="text-base font-semibold text-white">
          {children}
        </h3>
      ),
      p: ({ children }) => (
        <p className="leading-7">
          {children}
        </p>
      ),
      ul: ({ children }) => (
        <ul className="list-disc space-y-1 pl-5">
          {children}
        </ul>
      ),
      ol: ({ children }) => (
        <ol className="list-decimal space-y-1 pl-5">
          {children}
        </ol>
      ),
      li: ({ children }) => (
        <li>{children}</li>
      ),
      strong: ({ children }) => (
        <strong className="font-semibold text-white">
          {children}
        </strong>
      ),
      code: ({ children }) => (
        <code className="rounded bg-slate-800 px-1.5 py-0.5 text-xs text-slate-200">
          {children}
        </code>
      ),
    }}
  >
    {message.content}
  </ReactMarkdown>
</div>

{message.role === "assistant" &&
  message.sources &&
  message.sources.length > 0 && (
    <div className="mt-5 border-t border-slate-700 pt-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-sm">📚</span>

        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Sources
        </p>

        <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] text-slate-500">
          {message.sources.length}
        </span>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        {message.sources.map((source, sourceIndex) => (
          <div
            key={`${source.document_id}-${source.chunk_id}`}
            className="group rounded-xl border border-slate-700/70 bg-slate-800/60 p-3 transition hover:border-slate-600 hover:bg-slate-800"
          >
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-700 text-sm">
                📄
              </div>

              <div className="min-w-0 flex-1">
                <p
  className="truncate text-xs font-semibold text-slate-200"
  title={source.filename || `Document #${source.document_id}`}
>
  {source.filename || `Document #${source.document_id}`}
</p>

                <p className="mt-1 text-[11px] text-slate-500">
                  Retrieved chunk {source.chunk_index}
                </p>
              </div>

              <span className="shrink-0 rounded-full bg-slate-700 px-2 py-1 text-[10px] font-medium text-slate-400">
                #{sourceIndex + 1}
              </span>
            </div>
          </div>
        ))}
      </div>

      <p className="mt-3 text-[11px] text-slate-600">
        Retrieved from your uploaded documents using semantic search.
      </p>
    </div>
  )}
                    </div>

                  </div>

                ))}


          {sending && (
  <div className="flex justify-start">
    <div className="rounded-2xl border border-slate-800 bg-slate-900 px-5 py-4">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 text-sm">
          🤖
        </div>

        <div>
          <p className="text-xs font-semibold text-slate-300">
            IntelliDocs AI
          </p>

          <div className="mt-1 flex items-center gap-1">
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
            <span className="ml-2 text-xs text-slate-500">
              Analyzing your documents...
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
)}

  <div ref={messagesEndRef} />


              </div>

            )}

          </div>


          {/* Chat Error */}
{chatError && (
  <div className="mx-auto mb-3 w-full max-w-4xl rounded-xl border border-red-900/70 bg-red-950/40 px-4 py-3">
    <div className="flex items-start gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-red-900/40 text-sm">
        ⚠️
      </div>

      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-red-300">
          AI service temporarily unavailable
        </p>

        <p className="mt-1 text-xs leading-5 text-red-400/80">
          {chatError}
        </p>

        <p className="mt-1 text-xs text-slate-500">
          Please try again later.
        </p>
      </div>

      <button
        type="button"
        onClick={() => setChatError(null)}
        className="shrink-0 rounded-md px-2 py-1 text-xs text-slate-500 transition hover:bg-red-900/30 hover:text-red-300"
        aria-label="Dismiss error"
      >
        ✕
      </button>
    </div>
  </div>
)}


          {/* Input */}

<div className="border-t border-slate-800 p-3 sm:p-5">

            <div className="mx-auto flex w-full max-w-4xl gap-2 sm:gap-3">

              <input
                type="text"
                value={question}
                onChange={(event) =>
                  setQuestion(event.target.value)
                }
                onKeyDown={handleQuestionKeyDown}
                disabled={sending}
                placeholder="Ask something about your documents..."
                className="min-w-0 flex-1 rounded-xl border border-slate-700 bg-slate-900 px-3 py-3 text-sm outline-none placeholder:text-slate-500 focus:border-slate-500 disabled:opacity-50 sm:px-4"
              />


              <button
                onClick={handleSendMessage}
                disabled={
                  !question.trim() || sending
                }
                className="shrink-0 rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-900 hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-50 sm:px-6"
              >
                {sending
                  ? "Sending..."
                  : "Send"}
              </button>

            </div>

          </div>

        </main>

      </div>

    </div>
  );
}


export default App;