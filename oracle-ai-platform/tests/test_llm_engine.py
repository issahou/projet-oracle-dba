# src/llm_engine.py
import ollama

class LLMEngine:
    def __init__(self, model="llama2", use_mock=False):
        self.model = model
        self.use_mock = use_mock

    def generate(self, prompt: str, variables: dict = None) -> str:
        # injecter les variables dans le prompt
        if variables:
            prompt = prompt.format(**variables)

        if self.use_mock:
            # Retour simulé pour les tests unitaires
            return f"[MOCK RESPONSE] {prompt}"

        # Appel réel à Ollama
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        # Extraire le texte de la réponse
        return response["message"]["content"]

    def assess_security(self, config: dict) -> dict:
        if self.use_mock:
            # Retour simulé pour les tests unitaires
            return {"SCORE": 85, "DETAILS": "Mocked security assessment"}

        prompt = f"Analyse la sécurité de cette configuration: {config}"
        response = self.generate(prompt)
        # Exemple de parsing simplifié
        return {"SCORE": 70, "DETAILS": response}
