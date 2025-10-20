variable "database_password" {
  type      = string
  sensitive = true
}

variable "container_image" {
  type = string
}

variable "anthropic_api_key_secret_arn" {
  type = string
}

variable "zoho_client_secret_arn" {
  type = string
}

variable "app_secret_key_arn" {
  type = string
}

variable "alert_email" {
  type    = string
  default = ""
}
