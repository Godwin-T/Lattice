curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer lattice_X6RfoFDawb5eIEGSZphFElINEqnnkbeEErjGvbjtVGs" \
  -H "Content-Type: application/json" \
  -d '{
    "model":"openai/gpt-oss-20b",
    "provider":"groq",
    "messages":[{"role":"user","content":"Hello"}]
  }'
  
  
