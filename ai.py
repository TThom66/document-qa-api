import asyncio
import anthropic
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
client = anthropic.Anthropic()

def answer_question(document_content: str, question: str) -> str:
    logger.info(f"Sending question to Claude: {question[:50]}...")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        system="""You are a helpful assistant. Answer questions based only 
            on the document provided. 

            Always structure your response in exactly this format:

            ANSWER:
            [Your answer here]

            SOURCES:
            [Quote the exact passages from the document that support your answer. 
            If multiple passages are relevant, number them: 1. "..." 2. "..."]

            If the answer isn't in the document, respond with:

            ANSWER:
            The document does not contain information about this topic.

            SOURCES:
            None""",
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

async def answer_question_async(
    document_content: str, 
    question: str
) -> dict:
    logger.info(f"Async question to Claude: {question[:50]}...")
    loop = asyncio.get_event_loop()
    answer = await loop.run_in_executor(
        None, 
        answer_question, 
        document_content, 
        question
    )
    return {"question": question, "answer": answer}