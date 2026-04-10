Document Q&A API

This is a REST API that allows users to upload text documents and ask natural language questions about them. Documents are stored persistently and can be queried at any time.

The core use case is document search and comprehension. Reading through a lengthy document to find a specific piece of information is slow and error-prone. This system lets you ask a plain English question — "what are the payment terms?" or "when does the contract expire?" — and get a direct answer pulled from the document. If the answer isn't there, the system says so rather than guessing.

The backend is built with FastAPI and Python, with SQLite handling document storage via SQLAlchemy. AI question-answering is handled by Anthropic's Claude Haiku model, which is prompted to answer strictly from the provided document content, preventing hallucinated responses.
