"""Example script to test LLM service independently."""
import asyncio
from src.services.llm_service import llm_service


async def test_evaluation():
    """Test post evaluation with sample content."""
    
    # Sample post content
    test_post = """
    🚀 Запускаем новую функцию в приложении!
    
    Теперь вы можете делиться постами прямо из нашего приложения в социальные сети.
    Мы добавили поддержку:
    • ВКонтакте
    • Telegram
    • WhatsApp
    
    Попробуйте прямо сейчас! 👇
    """
    
    print("🧪 Testing post evaluation...")
    print(f"Post content:\n{test_post}\n")
    print("=" * 60)
    
    # Evaluate
    results = await llm_service.evaluate_post(
        content=test_post,
        image_url=None
    )
    
    # Print results
    print("\n📊 Evaluation Results:")
    print("=" * 60)
    
    for result in results:
        status = "✅" if result.success else "❌"
        print(f"\n{status} {result.model_name}")
        if result.success:
            print(f"   Score: {result.score}/10")
            print(f"   Comment: {result.comment[:200]}...")
        else:
            print(f"   Error: {result.error}")
    
    # Format response
    print("\n" + "=" * 60)
    print("📝 Formatted Response:")
    print("=" * 60)
    response = llm_service.format_evaluation_response(results)
    print(response)
    
    # Cleanup
    await llm_service.close()


if __name__ == "__main__":
    asyncio.run(test_evaluation())
