variable "cloudflare_account_id" {
  type        = string
  description = "Cloudflare account ID that owns the R2 bucket."
}

variable "cloudflare_api_token" {
  type        = string
  sensitive   = true
  description = "Cloudflare API token with R2 read/write permissions. Provide via TF_VAR_cloudflare_api_token, never hardcode."
}

variable "bucket_name" {
  type        = string
  default     = "atlas-people-context-uploader"
  description = "Name of the R2 bucket used to store uploaded documents and inferred metadata."
}

variable "location" {
  type        = string
  default     = "WEUR"
  description = "R2 bucket location hint (e.g. WNAM, ENAM, WEUR, EEUR, APAC)."
}
