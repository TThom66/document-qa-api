import logging
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
client = anthropic.Anthropic()

def answer_question(document_content: str, question: str) -> str:
    logger.info(f"Sending question to Claude: {question[:50]}...")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system="You are a helpful assistant. Answer questions based only on the document provided. If the answer isn't in the document, say so.",
        messages=[
            {
                "role": "user",
                "content": f"Document:\n{document_content}\n\nQuestion: {question}"
            }
        ]
    )

    answer = response.content[0].text
    logger.info("Received response from Claude")
    return answer
