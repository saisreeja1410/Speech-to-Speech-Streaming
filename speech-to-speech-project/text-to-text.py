from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", api_key=gemini_api_key)

# Load the .txt file
with open("transcription2.txt", "r") as f:
    text = f.read()

# Define the prompt
prompt = PromptTemplate(
    template="Translate the following text into {target_language}:\n{text}",
    input_variables=["text", "target_language"],
)

output_parser = StrOutputParser()

llm_chain = LLMChain(
    llm=llm,
    prompt=prompt,
    output_parser=output_parser
)

# Define the target language
target_language = "Hindi"  # Replace with the desired language

# Run the translation

output = llm_chain.run(text=text, target_language=target_language)

# Print the translated text
print(output)

# Save the translated text to a .txt file
with open("hindi-translation.txt", "w", encoding="utf-8", errors="ignore") as f:
    f.write(str(output))

