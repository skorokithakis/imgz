terraform {
  backend "s3" {
    bucket = "terraformstate.stochastic.io"
    key    = "imgz/terraform.tfstate"
    region = "eu-central-1"
  }
}

variable "cloudflare_email" {}
variable "cloudflare_api_key" {}

variable ipv6_ip { default = "2a01:4f8:1c0c:6109::1" }
variable ipv4_ip { default = "195.201.40.251" }
variable domain { default = "imgz.org" }
variable zone { default = "03a5ad171d3bccca251801f877714030" }

provider "cloudflare" {
  version = "~> 2.0"
  email = "${var.cloudflare_email}"
  api_key = "${var.cloudflare_api_key}"
}

resource "cloudflare_record" "v6_root" {
  zone_id=var.zone
  type="AAAA"
  name="@"
  proxied="true"
  value="${var.ipv6_ip}"
}

resource "cloudflare_record" "v6_www" {
  zone_id=var.zone
  type="AAAA"
  name="www"
  proxied="true"
  value="${var.ipv6_ip}"
}

resource "cloudflare_record" "root" {
  zone_id=var.zone
  type="A"
  name="@"
  proxied="true"
  value="${var.ipv4_ip}"
}

resource "cloudflare_record" "www" {
  zone_id=var.zone
  type="A"
  name="www"
  proxied="true"
  value="${var.ipv4_ip}"
}

resource "cloudflare_page_rule" "cache_images" {
  zone_id = var.zone
  target = "https://imgz.org/i*"
  priority = 1

  actions {
    browser_cache_ttl = 16070400
    cache_level = "cache_everything"
    edge_cache_ttl = 2419200
  }
}

