# vim: ft=terraform

terraform {
  required_providers {
    ovh = {
      source  = "ovh/ovh"
      version = "~> 0.13.0"
    }
  }

  required_version = ">= 0.14.9"
}

provider "ovh" {
  endpoint           = var.ovh_endpoint
  application_key    = var.ovh_application_key
  application_secret = var.ovh_application_secret
  consumer_key       = var.ovh_consumer_key
}

data "ovh_dedicated_server" "server" {
  service_name = var.server_id
}

# data "ovh_dedicated_server_boots" "rescue" {
#   service_name = var.server_id
#   boot_type    = "rescue"
# }
# 
# data "ovh_dedicated_server_boots" "harddisk" {
#   service_name = var.server_id
#   boot_type    = "harddisk"
# }

resource "ovh_me_ssh_key" "key" {
  key_name = var.ssh_key_name
  key      = file(pathexpand(var.ssh_key_file))
  default  = true
}

resource "ovh_me_installation_template" "ubuntu" {
  base_template_name = var.base_template_name
  template_name      = "ubuntu"
  default_language   = "en"

  customization {
    ssh_key_name = ovh_me_ssh_key.key.key_name
  }
}

resource "ovh_me_installation_template_partition_scheme" "scheme" {
  template_name = ovh_me_installation_template.ubuntu.template_name
  name          = "ubuntu-partitions"
  priority      = 1
}


resource "ovh_me_installation_template_partition_scheme_partition" "root" {
  template_name = ovh_me_installation_template_partition_scheme.scheme.template_name
  scheme_name   = ovh_me_installation_template_partition_scheme.scheme.name
  mountpoint    = "/"
  filesystem    = "ext4"
  size          = 524288  # MB -> 512 Go
  order         = 1
  type          = "primary"
  raid          = null
  volume_name   = "root"
}

resource "ovh_me_installation_template_partition_scheme_partition" "data" {
  template_name = ovh_me_installation_template_partition_scheme.scheme.template_name
  scheme_name   = ovh_me_installation_template_partition_scheme.scheme.name
  mountpoint    = "/data"
  filesystem    = "ext4"
  size          = 0  # take the rest of space
  order         = 2
  type          = "primary"
  raid          = null
  volume_name   = "data"
}

resource "ovh_me_installation_template_partition_scheme_partition" "swap" {
  template_name = ovh_me_installation_template_partition_scheme.scheme.template_name
  scheme_name   = ovh_me_installation_template_partition_scheme.scheme.name
  mountpoint    = "swap"
  filesystem    = "swap"
  size          = 8192  # MB -> 8 Go
  order         = 3
  type          = "primary"
  raid          = null
  volume_name   = "swap"
}



resource "ovh_dedicated_server_install_task" "server_install" {
  service_name      = data.ovh_dedicated_server.server.service_name
  template_name     = ovh_me_installation_template.ubuntu.template_name
  partition_scheme_name = ovh_me_installation_template_partition_scheme.scheme.name
  // bootid_on_destroy = data.ovh_dedicated_server_boots.rescue.result[0]

  details {
    custom_hostname = var.server_id
    no_raid = true
    use_distrib_kernel = false  # TODO enable ?
  }
}


# resource "ovh_dedicated_server_update" "server_on_rescue" {
#   service_name = data.ovh_dedicated_server.server.service_name
#   boot_id      = data.ovh_dedicated_server_boots.harddisk.result[0]
#   monitoring   = true
#   state        = "ok"
# }

# resource "ovh_dedicated_server_reboot_task" "server_reboot" {
#   service_name = data.ovh_dedicated_server_boots.rescue.service_name
# 
#   keepers = [
#     ovh_dedicated_server_update.server_on_rescue.boot_id,
#   ]
# }

output "ip_address" {
  value = data.ovh_dedicated_server.server.ip
}

output "ip_blocks" {
  value = data.ovh_dedicated_server.server.ips
}
