# Subir a aplicação
uvicorn main:app --reload

# ENV

APP_NAME=Onidia Assistente API
DEBUG=True

MONGO_URL=mongodb://root:password@127.0.0.1:27017
MONGO_DB=onidia

DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=user
DB_PASS=password
DB_NAME=database
ENABLE_SQL_LOG=1

REDIS_URL=redis://127.0.0.1:6379/0

SECRET_KEY=secret_key

AWS_ACCESS_KEY_ID=access_key_id
AWS_SECRET_ACCESS_KEY=secret_access_key
S3_BUCKET_NAME=bucket
S3_REGION=region