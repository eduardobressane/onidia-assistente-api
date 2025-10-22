# AWS S3

# Configurar regra (caso não esteja configurada)

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadForPublicFolder",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::NOME_DO_SEU_BUCKET/public/*"
    }
  ]
}

No AWS Console:

Vá em S3 → seu bucket → Permissions (Permissões)
Role até Block public access (bucket settings)
Clique em Edit
Desmarque todas as opções de “Block all public access”
Confirme digitando confirm

Ainda em Permissions → Bucket Policy, insira:

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadForPublicFolder",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::NOME_DO_SEU_BUCKET/public/*"
    }
  ]
}