import os
import traceback

from dotenv import load_dotenv
from google import genai

from ai.banking_ai import (
    get_balance,
    get_transactions
)


load_dotenv()


api_key = os.getenv(
    "GEMINI_API_KEY"
)


if not api_key:
    raise Exception(
        "GEMINI_API_KEY missing in .env file"
    )


client = genai.Client(
    api_key=api_key
)



def ask_gemini(message):

    try:

        text = message.lower()


        # Banking features

        if "balance" in text:
            return get_balance()


        if "transaction" in text or "history" in text:
            return get_transactions()



        response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=message
    )


        if response.text:
            return response.text


        return "I could not understand that."



    except Exception:
        return (
            "I'm unable to contact the AI service right now.\n\n"
            "You can still ask me about:\n"
            "• Deposits\n"
            "• Withdrawals\n"
            "• Transfers\n"
            "• Loans\n"
            "• Banking services"
        )