terraform {
  required_version = ">= 1.5.0"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.40"
    }
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# Object storage bucket for uploaded context documents and their inferred metadata.
resource "cloudflare_r2_bucket" "context_uploader" {
  account_id = var.cloudflare_account_id
  name       = var.bucket_name
  location   = var.location
}
