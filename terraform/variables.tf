# vim: ft=terraform

variable "server_id" {
  type = string
}
variable "ssh_key_name" {
  description = "Name of the SSH keypair to inject in the instance"
  type = string
  default = "default"
}
variable "ssh_key_file" {
  description = "SSH keypair to inject in the instance"
  type = string
  default = "~/.ssh/id_ed25519.pub"
}

variable "base_template_name" {
  description = "Image to boot nodes from"
  default     = "ubuntu2004-server_64"
}

variable "ovh_endpoint" {
  type = string
  default = "ovh-eu"
}

variable "ovh_application_key" {
  type = string
}

variable "ovh_application_secret" {
  type = string
}

variable "ovh_consumer_key" {
  type = string
}
