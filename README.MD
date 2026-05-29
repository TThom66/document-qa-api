## Document Q&A API

This is a REST API that allows users to upload text documents and ask natural language questions about them. Documents are stored persistently and can be queried at any time.

A simple HTML frontend is also included for convenience.

The core use case is document search and comprehension. Reading through a lengthy document to find a specific piece of information is slow and error-prone. This system lets you ask a plain English question — "what are the payment terms?" or "when does the contract expire?" — and get a direct answer pulled from the document. If the answer isn't there, the system says so rather than guessing. There is also a template feature that allows you to ask multiple questions about a document at once without needing to enter them in one at a time.

The backend is built with FastAPI and Python, with PostgreSQL handling document storage in production via SQLAlchemy and SQLite for local development. AI question-answering is handled by Anthropic's Claude Haiku model, which is prompted to answer strictly from the provided document content, preventing hallucinated responses. The API itself is hosted through Railway to reduce server costs. Template questions are processed in parallel using asyncio, significantly reducing response time for multi-question templates. 

## Getting Started

**For general use:** Download index.html and open it in your browser. Make sure it is pointed at https://web-production-7a386e.up.railway.app

**For API access:** 
1. Visit `https://web-production-7a386e.up.railway.app/docs`
2. Create an account through the `/auth/register` endpoint
3. Log in through the `/auth/token` endpoint using the Authorize button.