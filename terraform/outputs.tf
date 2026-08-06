output "load_balancer_ip" {
  description = "IP público do Load Balancer"
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

output "resource_group" {
  description = "Nome do Resource Group"
  value       = azurerm_resource_group.nordmart.name
}