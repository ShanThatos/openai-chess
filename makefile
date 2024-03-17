update:
	git pull

start:
	poetry install
	poetry run python -u main.py

cf:
	cloudflared tunnel run --cred-file cf_creds.json --url 0.0.0.0:8086 chess.shanthatos.dev