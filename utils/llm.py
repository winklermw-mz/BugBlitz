import lmstudio as lms
import json
from model.case import PRIORITY_HIGH, PRIORITY_LOW, PRIORITY_NORMAL


def call_ai_model(requirement_text):
    model = lms.llm("qwen/qwen3-vl-4b")
    response = model.respond(
        {
            "messages":
            [
                {
                    "role": "system",
                    "content": get_system_prompt(),
                },
                {
                    "role": "user",
                    "content": f"Die Anforderung lautet: {requirement_text}"
                }
            ]
        }
    )
    return json.loads(str(response))

def get_system_prompt():
    return f"""
        Du bist ein Experte für Softwaretest und Qualitätssicherung.
        Deine Aufgabe ist es, aus einer gegebenen **Anforderung** eine Liste von 1 bis N detaillierten **Testfällen** zu generieren.

        Liefere die Testfälle ausschließlich als **JSON-Array** zurück. Das Format muss exakt dem folgenden Schema entsprechen.
        Weiteres Markup ist nicht erlaubt.
        
        Alle Tags werden mit einen Hashtag # markiert und werden durch Leerzeichen getrennt.
        
        JSON-SCHEMA:
        [
          {{
            "title": "Kurzer Titel des Testfalls (max. 150 Zeichen)",
            "summary": "Zusammenfassung des Testfalls",
            "precondition": "Notwendige Voraussetzungen (optional)",
            "postcondition": "Erwarteter Zustand nach erfolgreicher Ausführung (optional)",
            "priority": "Eine der erlaubten Prioritäten: "{PRIORITY_HIGH}", "{PRIORITY_NORMAL}", "{PRIORITY_LOW}"",
            "source": "Quelle, z.B. 'KI-Extraktion'",
            "tags": "Ein oder mehrere passende Hashtags, getrennt durch Leerzeichen, z.B. #testfall #ki",
            "steps": [
              {{
                "action": "Detaillierte durchzuführende Aktion",
                "expected_result": "Erwartetes Ergebnis dieser Aktion"
              }},
              {{
                "action": "Nächste Aktion...",
                "expected_result": "Nächstes erwartetes Ergebnis..."
              }}
            ]
          }},
          // ... Weitere Testfälle
        ]
        """