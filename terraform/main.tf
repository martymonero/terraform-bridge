terraform {
  required_providers {
    xcloud = {
      source = "terraform.local/dev/xcloud"
    }
  }
}

variable "xcloud_token" {
  sensitive = true
}

provider "xcloud" {
  endpoint        = "http://localhost:1337"
  poll_interval   = "30000ms"
  token           = var.xcloud_token
}

resource "xcloud_server" "server-47" {
  image           = "redhat-9.0"
  name            = "server-47"
  server_type     = "linux-large"
  datacenter      = "fra1"
}

