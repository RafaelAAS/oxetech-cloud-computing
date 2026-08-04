output "load_balancer_ip" {
  description = "IP público do Load Balancer (acesse a aplicação por aqui)"
  value       = azurerm_public_ip.lb.ip_address
}

output "vm_a_ip" {
  description = "IP público da VM web-a"
  value       = azurerm_public_ip.vm_a.ip_address
}

output "vm_b_ip" {
  description = "IP público da VM web-b"
  value       = azurerm_public_ip.vm_b.ip_address
}

output "database_host" {
  description = "Endereço do banco PostgreSQL"
  value       = azurerm_postgresql_flexible_server.nordmart.fqdn
}

output "database_name" {
  description = "Nome do banco"
  value       = azurerm_postgresql_flexible_server_database.nordmart.name
}

output "storage_account_name" {
  description = "Nome do Storage Account"
  value       = azurerm_storage_account.nordmart.name
}

output "resource_group" {
  description = "Nome do Resource Group"
  value       = azurerm_resource_group.nordmart.name
}
