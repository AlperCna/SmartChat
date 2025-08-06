# ai_module/style_adapter.py

def detect_style(receiver_username):
    """
    Konuşulan kişiye göre üslup belirler.
    """
    if not receiver_username:
        return "neutral"

    name = receiver_username.lower()

    # Resmi hitap (anne, öğretmen vs.)
    if name in ["anne", "mom", "mother", "teacher", "hocam"]:
        return "formal"

    # Samimi hitap (arkadaş, kanka vs.)
    if name in ["kanka", "bro", "buddy", "dostum"]:
        return "informal"

    return "neutral"


def adapt_style(text, style):
    """
    Cümleyi verilen üsluba göre uyarlar.
    """
    if style == "formal":
        # Baş harfi büyük yap, kısaltma ve argo kaldır
        return text.capitalize().replace("ya", "").replace("kanka", "").strip()

    elif style == "informal":
        # Daha samimi dil
        return text.lower().replace("merhaba", "selam").replace("selamlar", "selam")

    return text


# Test
if __name__ == "__main__":
    sample_text = "merhaba nasılsın"
    print("Formal:", adapt_style(sample_text, "formal"))
    print("Informal:", adapt_style(sample_text, "informal"))
    print("Neutral:", adapt_style(sample_text, "neutral"))
