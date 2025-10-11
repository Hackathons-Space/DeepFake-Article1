import google.generativeai as genai

# ✅ Correct way
genai.configure(api_key="AIzaSyD9YGNbEPonr7snQlCciCx404PsMfZ6qq8")

for m in genai.list_models():
    print(m.name)
