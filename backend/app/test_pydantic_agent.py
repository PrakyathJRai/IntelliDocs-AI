import asyncio

from app.database import SessionLocal
from app.services.pydantic_agent_service import run_pydantic_agent


async def main():

    db = SessionLocal()

    try:
        result = await run_pydantic_agent(
            db=db,
            question="What is IntelliDocs AI?",
            top_k=5
        )

        print("\n=== Pydantic AI Result ===")
        print("Answer:")
        print(result.answer)

        print("\nSources:")
        print(result.sources)

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())