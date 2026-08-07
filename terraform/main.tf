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

resource "azurerm_subnet" "public" {
  name                 = "${var.project}-subnet-public"
  resource_group_name  = azurerm_resource_group.nordmart.name
  virtual_network_name = azurerm_virtual_network.nordmart.name
  address_prefixes     = ["10.10.1.0/24"]
}

# ─── NETWORK SECURITY GROUPS ──────────────────────────────────
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
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = { project = "NordMart" }
}

resource "azurerm_subnet_network_security_group_association" "public" {
  subnet_id                 = azurerm_subnet.public.id
  network_security_group_id = azurerm_network_security_group.vm.id
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
  name                  = "${var.project}-vm-a"
  resource_group_name   = azurerm_resource_group.nordmart.name
  location              = azurerm_resource_group.nordmart.location
  size                  = var.vm_size
  admin_username        = var.admin_username
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
    sku       = "22_04-lts"
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
  name                  = "${var.project}-vm-b"
  resource_group_name   = azurerm_resource_group.nordmart.name
  location              = azurerm_resource_group.nordmart.location
  size                  = var.vm_size
  admin_username        = var.admin_username
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
    sku       = "22_04-lts"
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