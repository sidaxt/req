import tiktoken
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
# encoding = tiktoken.encoding_for_model("GPT4o")
# encoding = tiktoken.get_encoding("GPT4o")
print("Token count:", len(encoding.encode("Hi there! How can I help you today?")))
print("Token count:", len(encoding.encode("Hello! How can I assist you today?")))
print("Token count:", len(encoding.encode("hello")))
print("Token count:", len(encoding.encode("hi")))

# num_tokens = 2  # For "role" and "content" keys
# for key, value in message.items():
#     num_tokens += len(encoding.encode(value))
# return num_tokens