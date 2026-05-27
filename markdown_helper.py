import re

def markdown_to_html(text: str) -> str:
    """
    Преобразует базовую Markdown-разметку в HTML.
    Поддерживает: **жирный**, *курсив*, `моноширинный`.
    """
    # Экранируем спецсимволы HTML
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # Жирный **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Курсив *text* (не пересекается с жирным)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    # Моноширинный `text`
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text
