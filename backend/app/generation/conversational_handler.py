import re
from typing import Optional, Tuple


class ConversationalHandler:
    """
    Intelligent conversational classifier for handling greetings, small talk,
    gratitude, and assistant capability questions without running heavy document retrieval.
    """

    GREETINGS_PATTERN = re.compile(
        r"^(hi|hello|hey|heyy|heya|howdy|hola|namaste|greetings|good\s+(morning|afternoon|evening|day)|sup|what\'?s\s+up)(\s+there)?[\.!\?]*$",
        re.IGNORECASE,
    )

    HOW_ARE_YOU_PATTERN = re.compile(
        r"^(how\s+are\s+you|how\s+are\s+you\s+doing|how\s+do\s+you\s+do|how\'?s\s+it\s+going)[\.!\?]*$",
        re.IGNORECASE,
    )

    CAPABILITIES_PATTERN = re.compile(
        r"^(who\s+are\s+you|what\s+can\s+you\s+do|what\s+do\s+you\s+do|how\s+can\s+you\s+help(\s+me)?|what\s+is\s+your\s+name|what\s+is\s+this(\s+app)?|help)[\.!\?]*$",
        re.IGNORECASE,
    )

    THANKS_PATTERN = re.compile(
        r"^(thanks|thank\s+you|thank\s+you\s+so\s+much|thanks\s+a\s+lot|appreciate\s+it|thx)[\.!\?]*$",
        re.IGNORECASE,
    )

    BYE_PATTERN = re.compile(
        r"^(bye|goodbye|see\s+you|cya|see\s+ya|have\s+a\s+(good|nice)\s+day|exit|quit)[\.!\?]*$",
        re.IGNORECASE,
    )

    def check_conversational_intent(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Checks if the query is a conversational greeting/pleasantry.
        Returns: (is_conversational, response_text)
        """
        clean_q = query.strip()
        if not clean_q:
            return True, "Hello! How can I help you analyze your documents today?"

        # 1. Greetings (Hi, Hello, Hey, etc.)
        if self.GREETINGS_PATTERN.match(clean_q):
            return True, (
                "Hello! 👋 I'm your Multimodal RAG Assistant. "
                "How can I help you regarding your documents today? "
                "Feel free to ask questions about the text, structured tables, or diagrams and figures in your uploaded files!"
            )

        # 2. How are you
        if self.HOW_ARE_YOU_PATTERN.match(clean_q):
            return True, (
                "I'm doing well and ready to assist you! 😊 "
                "What would you like to explore or find in your documents today?"
            )

        # 3. Capabilities / Identity
        if self.CAPABILITIES_PATTERN.match(clean_q):
            return True, (
                "I am an enterprise **Multimodal Document AI Assistant**. 🚀\n\n"
                "Here is how I can assist you:\n"
                "- 📄 **Document Understanding**: Ask questions about your uploaded PDFs, PPTX slide decks, DOCX files, and images.\n"
                "- 📊 **Tables & Structured Data**: Query financial tables, rows, columns, and data comparisons.\n"
                "- 🖼️ **Visual Artifacts & Diagrams**: Explain technical architectures, flowcharts, graphs, and figures with original page citations.\n"
                "- 🎯 **Grounded Answers**: Provide accurate, hallucination-free answers backed by exact source references.\n\n"
                "What topic or document would you like to start with?"
            )

        # 4. Gratitude (Thanks, Thank you)
        if self.THANKS_PATTERN.match(clean_q):
            return True, (
                "You're very welcome! 😊 Let me know if you need any more answers, table summaries, or diagram explanations from your documents."
            )

        # 5. Farewells (Bye, Goodbye)
        if self.BYE_PATTERN.match(clean_q):
            return True, (
                "Goodbye! 👋 Feel free to return anytime you need help analyzing or exploring your documents. Have a great day!"
            )

        return False, None


conversational_handler = ConversationalHandler()
