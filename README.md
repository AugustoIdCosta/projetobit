# Crypto Tracker

Aplicação demo que monitora o preço do Bitcoin e grava o histórico em PostgreSQL. O projeto é dividido em três camadas principais:

- **API Flask** (`app/api`): expõe a rota `/history` para consultar os registros salvos e realiza o bootstrap do schema.
- **Worker** (`app/worker`): busca o preço atual via CoinGecko a cada 30 segundos e insere no banco.
- **Infraestrutura** (`infra` e `k8s`): provisiona um cluster Kind gerenciado por Terraform, instala Argo CD + stack Prometheus/Grafana via Helm e aplica os manifestos Kubernetes dos serviços.

## Tech Stack

- Python 3.11, Flask, psycopg2, Requests
- PostgreSQL 16
- Docker + Docker Compose (imagens customizadas para API e worker)
- Kind + Terraform + Helm
- Kubernetes (Deployments, Services, Secrets)
- Argo CD e kube-prometheus-stack para observabilidade

## Estrutura do Repositório

```
app/
  api/
    Dockerfile
    main.py
    requirements.txt
  worker/
    Dockerfile
    main.py
    requirements.txt
infra/
  main.tf           # Provisiona cluster Kind e instala ArgoCD + monitoring via Helm
k8s/
  api.yaml          # Deployment + Service da API
  worker.yaml       # Deployment do worker
  secrets.yaml      # DATABASE_URL usado pelos pods
docker-compose.yml  # Placeholder para futuros usos locais
```

## Pré-requisitos

1. Docker & Docker Compose
2. Terraform >= 1.6
3. kubectl
4. Kind
5. Conta no Docker Hub (ou registry compatível) caso deseje publicar as imagens `augusto-idalgo/crypto-api` e `augusto-idalgo/crypto-worker`.

## Build das Imagens

Dentro de cada pasta de serviço:

```bash
# API
cd app/api
python -m pip install -r requirements.txt  # opcional para uso local
docker build -t augusto-idalgo/crypto-api:v1 .

# Worker
cd ../worker
docker build -t augusto-idalgo/crypto-worker:v1 .
```

Publique em um registry acessível ao cluster, se necessário:

```bash
docker push augusto-idalgo/crypto-api:v1
docker push augusto-idalgo/crypto-worker:v1
```

## Provisionando o Cluster (Terraform + Kind)

```bash
cd infra
terraform init
terraform apply
```

O `main.tf` atual:

1. Baixa os providers `kind` e `helm`.
2. Cria um cluster Kind chamado `crypto-tracker-cluster`.
3. Configura o provider Helm para falar com o novo cluster.
4. Instala Argo CD (`argocd` namespace) com `server.extraArgs = --insecure` para facilitar o acesso local.
5. Instala `kube-prometheus-stack` no namespace `monitoring`.

Após o `apply`, valide o acesso:

```bash
kubectl get nodes
kubectl get pods -A
```

## Aplicando os manifestos da aplicação

```bash
# Certifique-se de estar no contexto kubeconfig criado pelo Kind
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/api.yaml
kubectl apply -f k8s/worker.yaml
```

> Dica: ajuste os nomes das imagens nos YAMLs caso versione novas tags.

## Configurações Importantes

- `DATABASE_URL`: string no formato `postgresql://USER:PASS@HOST:PORT/DB` consumida tanto pela API quanto pelo worker.
- A API garante que a tabela `registro_valores` exista ao subir (via `ensure_schema`).
- O worker insere registros na tabela `prices` (verifique o nome da tabela desejada antes de rodar em produção).

## Próximos Passos

- Popular `docker-compose.yml` para um ambiente local completo.
- Adicionar pipelines de CI/CD usando Argo CD ou GitHub Actions.
- Expandir dashboards do Grafana e alertas do Prometheus conforme as métricas disponibilizadas.

Ficou com dúvidas ou quer contribuir? Abra uma issue ou envie um PR! 🚀
