env:
	python3 -m venv fastapi-env
	source fastapi-env/bin/activate

setup:
	python3 -m pip install pip install fastapi[all]
	# fastapi uvicorn sqlalchemy psycopg2-binary pydantic[dotenv] python-multipart

run:
	fastapi dev main.py
