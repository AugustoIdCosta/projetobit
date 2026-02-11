terraform {
  required_providers {
    kind = {
      source = "tehcyx/kind"
      version = "0.2.0"
    }
    helm = {
      source = "hashicorp/helm"
      version = "2.12.1"
    }
  }
}

provider "kind" {}

# 1. CRIA O CLUSTER (O "Hardware")
resource "kind_cluster" "crypto_cluster" {
  name = "crypto-tracker-cluster"
  node_image = "kindest/node:v1.27.3"
  wait_for_ready = true
}

# 2. CONFIGURA O HELM (Para instalar ferramentas dentro do cluster novo)
provider "helm" {
  kubernetes {
    host = kind_cluster.crypto_cluster.endpoint
    client_certificate     = kind_cluster.crypto_cluster.client_certificate
    client_key             = kind_cluster.crypto_cluster.client_key
    cluster_ca_certificate = kind_cluster.crypto_cluster.cluster_ca_certificate
  }
}

# 3. INSTALA O ARGOCD (O "Gerente de Deploy")
resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  namespace        = "argocd"
  create_namespace = true
  version          = "5.46.7"

  depends_on = [kind_cluster.crypto_cluster]

  # Desliga SSL forçado para facilitar acesso local
  set {
    name  = "server.extraArgs"
    value = "{--insecure}"
  }
}

# 4. INSTALA PROMETHEUS + GRAFANA (O "Monitoramento")
resource "helm_release" "monitoramento" {
  name       = "stack-monitoramento"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = "monitoring"
  create_namespace = true

  depends_on = [kind_cluster.crypto_cluster]
}