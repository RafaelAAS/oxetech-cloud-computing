variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  sensitive   = true
}

variable "client_id" {
  description = "Azure Service Principal App ID"
  type        = string
  sensitive   = true
}

variable "client_secret" {
  description = "Azure Service Principal Password"
  type        = string
  sensitive   = true
}

variable "tenant_id" {
  description = "Azure Tenant ID"
  type        = string
  sensitive   = true
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "westus2" 
}

variable "project" {
  description = "Project name prefix"
  type        = string
  default     = "nordmart"
}

variable "vm_size" {
  description = "VM size"
  type        = string
  default     = "Standard_B2ats_v2" 
}

variable "admin_username" {
  description = "VM admin username"
  type        = string
  default     = "nordadmin"
}

variable "db_admin_username" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "norddbadmin"
}

variable "db_admin_password" {
  description = "PostgreSQL admin password"
  type        = string
  sensitive   = true
}

variable "my_ip" {
  description = "Your public IP for SSH access (run: curl ifconfig.me)"
  type        = string
}