output "bucket_name" {
  value       = cloudflare_r2_bucket.context_uploader.name
  description = "Name of the provisioned R2 bucket. Set this as R2_BUCKET_NAME in the backend env."
}

output "bucket_location" {
  value       = cloudflare_r2_bucket.context_uploader.location
  description = "Location hint the bucket was created in."
}
