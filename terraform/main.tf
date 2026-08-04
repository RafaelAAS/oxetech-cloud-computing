# ─── RESOURCE GROUP ───────────────────────────────────────────
resource "azurerm_resource_group" "nordmart" {
  name     = "${var.project}-rg"
  location = var.location

  tags = {
    project     = "NordMart"
    environment = "lab"
    managed_by  = "terraform"
  }
}

# ─── VIRTUAL NETWORK ──────────────────────────────────────────
resource "azurerm_virtual_network" "nordmart" {
  name                = "${var.project}-vnet"
  address_space       = ["10.10.0.0/16"]
  location            = azurerm_resource_group.nordmart.location
  resource_group_name = azurerm_resource_group.nordmart.name

  tags = {
    project = "NordMart"
  }
}

# Subnet pública — onde ficam as VMs
resource "azurerm_subnet" "public" {
  name                 = "${var.project}-subnet-public"
  resource_group_name  = azurerm_resource_group.nordmart.name
  virtual_network_name = azurerm_virtual_network.nordmart.name
  address_prefixes     = ["10.10.1.0/24"]
}

# Subnet privada — onde fica o banco
resource "azurerm_subnet" "private" {
  name                 = "${var.project}-subnet-private"
  resource_group_name  = azurerm_resource_group.nordmart.name
  virtual_network_name = azurerm_virtual_network.nordmart.name
  address_prefixes     = ["10.10.2.0/24"]

  delegation {
    name = "postgresql-delegation"
    service_delegation {
      name = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action"
      ]
    }
  }
}

# DNS Zone privada para o banco — permite que as VMs encontrem o banco pelo nome
resource "azurerm_private_dns_zone" "postgresql" {
  name                = "${var.project}.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.nordmart.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgresql" {
  name                  = "${var.project}-dns-link"
  private_dns_zone_name = azurerm_private_dns_zone.postgresql.name
  resource_group_name   = azurerm_resource_group.nordmart.name
  virtual_network_id    = azurerm_virtual_network.nordmart.id
  registration_enabled  = false
}

# ─── NETWORK SECURITY GROUPS ──────────────────────────────────

# NSG das VMs — aceita HTTP do load balancer e SSH só do seu IP
resource "azurerm_network_security_group" "vm" {
  name                = "${var.project}-nsg-vm"
  location            = azurerm_resource_group.nordmart.location
  resource_group_name = azurerm_resource_group.nordmart.name

  security_rule {
    name                       = "allow-http"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "allow-ssh"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "${var.my_ip}/32"
    destination_address_prefix = "*"
  }

  tags = { project = "NordMart" }
}

# NSG do banco — aceita PostgreSQL só das VMs (subnet pública)
resource "azurerm_network_security_group" "db" {
  name                = "${var.project}-nsg-db"
  location            = azurerm_resource_group.nordmart.location
  resource_group_name = azurerm_resource_group.nordmart.name

  security_rule {
    name                       = "allow-postgresql"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5432"
    source_address_prefix      = "10.10.1.0/24"
    destination_address_prefix = "*"
  }

  tags = { project = "NordMart" }
}

# Associa o NSG à subnet pública
resource "azurerm_subnet_network_security_group_association" "public" {
  subnet_id                 = azurerm_subnet.public.id
  network_security_group_id = azurerm_network_security_group.vm.id
}

# Associa o NSG à subnet privada
resource "azurerm_subnet_network_security_group_association" "private" {
  subnet_id                 = azurerm_subnet.private.id
  network_security_group_id = azurerm_network_security_group.db.id
}

# ─── SSH KEY ──────────────────────────────────────────────────
resource "azurerm_ssh_public_key" "nordmart" {
  name                = "${var.project}-ssh-key"
  resource_group_name = azurerm_resource_group.nordmart.name
  location            = azurerm_resource_group.nordmart.location
  public_key          = file("${path.module}/nordmart_key.pub")
}

# ─── VM web-a ─────────────────────────────────────────────────
resource "azurerm_public_ip" "vm_a" {
  name                = "${var.project}-ip-vm-a"
  resource_group_name = azurerm_resource_group.nordmart.name
  location            = azurerm_resource_group.nordmart.location
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = ["1"]
  tags                = { project = "NordMart" }
}

resource "azurerm_network_interface" "vm_a" {
  name                = "${var.project}-nic-vm-a"
  location            = azurerm_resource_group.nordmart.location
  resource_group_name = azurerm_resource_group.nordmart.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.public.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.vm_a.id
  }
}

resource "azurerm_linux_virtual_machine" "vm_a" {
  name                = "${var.project}-vm-a"
  resource_group_name = azurerm_resource_group.nordmart.name
  location            = azurerm_resource_group.nordmart.location
  size                = var.vm_size
  admin_username      = var.admin_username
  zone                = "1"

  network_interface_ids = [azurerm_network_interface.vm_a.id]

  admin_ssh_key {
    username   = var.admin_username
    public_key = azurerm_ssh_public_key.nordmart.public_key
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  tags = { project = "NordMart", role = "web" }
}

# ─── VM web-b ─────────────────────────────────────────────────
resource "azurerm_public_ip" "vm_b" {
  name                = "${var.project}-ip-vm-b"
  resource_group_name = azurerm_resource_group.nordmart.name
  location            = azurerm_resource_group.nordmart.location
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = ["2"]
  tags                = { project = "NordMart" }
}

resource "azurerm_network_interface" "vm_b" {
  name                = "${var.project}-nic-vm-b"
  location            = azurerm_resource_group.nordmart.location
  resource_group_name = azurerm_resource_group.nordmart.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.public.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.vm_b.id
  }
}

resource "azurerm_linux_virtual_machine" "vm_b" {
  name                = "${var.project}-vm-b"
  resource_group_name = azurerm_resource_group.nordmart.name
  location            = azurerm_resource_group.nordmart.location
  size                = var.vm_size
  admin_username      = var.admin_username
  zone                = "2"

  network_interface_ids = [azurerm_network_interface.vm_b.id]

  admin_ssh_key {
    username   = var.admin_username
    public_key = azurerm_ssh_public_key.nordmart.public_key
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  tags = { project = "NordMart", role = "web" }
}

# ─── LOAD BALANCER ────────────────────────────────────────────
resource "azurerm_public_ip" "lb" {
  name                = "${var.project}-ip-lb"
  resource_group_name = azurerm_resource_group.nordmart.name
  location            = azurerm_resource_group.nordmart.location
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = { project = "NordMart" }
}

resource "azurerm_lb" "nordmart" {
  name                = "${var.project}-lb"
  location            = azurerm_resource_group.nordmart.location
  resource_group_name = azurerm_resource_group.nordmart.name
  sku                 = "Standard"

  frontend_ip_configuration {
    name                 = "frontend"
    public_ip_address_id = azurerm_public_ip.lb.id
  }

  tags = { project = "NordMart" }
}

resource "azurerm_lb_backend_address_pool" "nordmart" {
  name            = "${var.project}-backend-pool"
  loadbalancer_id = azurerm_lb.nordmart.id
}

resource "azurerm_lb_probe" "http" {
  name            = "http-probe"
  loadbalancer_id = azurerm_lb.nordmart.id
  protocol        = "Http"
  port            = 80
  request_path    = "/health"
}

resource "azurerm_lb_rule" "http" {
  name                           = "http-rule"
  loadbalancer_id                = azurerm_lb.nordmart.id
  protocol                       = "Tcp"
  frontend_port                  = 80
  backend_port                   = 80
  frontend_ip_configuration_name = "frontend"
  backend_address_pool_ids       = [azurerm_lb_backend_address_pool.nordmart.id]
  probe_id                       = azurerm_lb_probe.http.id
}

resource "azurerm_network_interface_backend_address_pool_association" "vm_a" {
  network_interface_id    = azurerm_network_interface.vm_a.id
  ip_configuration_name   = "internal"
  backend_address_pool_id = azurerm_lb_backend_address_pool.nordmart.id
}

resource "azurerm_network_interface_backend_address_pool_association" "vm_b" {
  network_interface_id    = azurerm_network_interface.vm_b.id
  ip_configuration_name   = "internal"
  backend_address_pool_id = azurerm_lb_backend_address_pool.nordmart.id
}

# ─── POSTGRESQL ───────────────────────────────────────────────
resource "azurerm_postgresql_flexible_server" "nordmart" {
  name                          = "${var.project}-db"
  resource_group_name           = azurerm_resource_group.nordmart.name
  location                      = azurerm_resource_group.nordmart.location
  version                       = "14"
  delegated_subnet_id           = azurerm_subnet.private.id
  private_dns_zone_id           = azurerm_private_dns_zone.postgresql.id
  administrator_login           = var.db_admin_username
  administrator_password        = var.db_admin_password
  zone                          = "1"
  storage_mb                    = 32768
  sku_name                      = "B_Standard_B1ms"
  backup_retention_days         = 7
  geo_redundant_backup_enabled  = false
  public_network_access_enabled = false

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgresql]

  tags = { project = "NordMart" }
}

resource "azurerm_postgresql_flexible_server_database" "nordmart" {
  name      = "nordmart"
  server_id = azurerm_postgresql_flexible_server.nordmart.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# ─── STORAGE ACCOUNT ──────────────────────────────────────────
resource "azurerm_storage_account" "nordmart" {
  name                     = "${var.project}storage2024"
  resource_group_name      = azurerm_resource_group.nordmart.name
  location                 = azurerm_resource_group.nordmart.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"

  blob_properties {
    versioning_enabled = false
  }

  tags = { project = "NordMart" }
}

resource "azurerm_storage_container" "nordmart" {
  name                  = "nordmart-files"
  storage_account_name  = azurerm_storage_account.nordmart.name
  container_access_type = "private"
}

# ─── AZURE MONITOR ────────────────────────────────────────────
resource "azurerm_monitor_action_group" "nordmart" {
  name                = "${var.project}-action-group"
  resource_group_name = azurerm_resource_group.nordmart.name
  short_name          = "nordmart"
  tags                = { project = "NordMart" }
}

resource "azurerm_monitor_metric_alert" "cpu_vm_a" {
  name                = "${var.project}-cpu-alert-vm-a"
  resource_group_name = azurerm_resource_group.nordmart.name
  scopes              = [azurerm_linux_virtual_machine.vm_a.id]
  description         = "Alerta quando CPU da VM-a passar de 80%"
  severity            = 2

  criteria {
    metric_namespace = "Microsoft.Compute/virtualMachines"
    metric_name      = "Percentage CPU"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = azurerm_monitor_action_group.nordmart.id
  }

  tags = { project = "NordMart" }
}
