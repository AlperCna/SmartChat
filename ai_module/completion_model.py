from transformers import pipeline

# Küçük ve hızlı bir model yükleyelim
generator = pipeline("text-generation", model="gpt2", max_length=50)

def complete_sentence(prompt):
    """
    Verilen başlangıç cümlesini devam ettirir.
    """
    results = generator(prompt, max_length=50, num_return_sequences=1)
    return results[0]["generated_text"]

# Test
if __name__ == "__main__":
    prompt = "Today is a beautiful day and"
    print("📝 Prompt:", prompt)
    print("✨ Completion:", complete_sentence(prompt))