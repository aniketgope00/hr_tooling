from google import genai


def get_gemini_response(prompt:str)->str:
    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text