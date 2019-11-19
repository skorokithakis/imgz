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

resource "cloudflare_record" "mg" {
  zone_id=var.zone
  type="CNAME"
  name="email.mail"
  value="eu.mailgun.org"
}

resource "cloudflare_record" "spf" {
  zone_id=var.zone
  type="TXT"
  name="mail"
  value="v=spf1 include:eu.mailgun.org ~all"
}

resource "cloudflare_record" "mx_domainkey" {
  zone_id=var.zone
  type="TXT"
  name="pic._domainkey.mail"
  value="k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA6m6Fr5fmS9pVGiKOgEG57MnR/r/FtLaUdG93u7rC+HIiqjeUPMwPx4Aya7TDAE03/p4BQdZ5w3WQpowsLp7tzSnNhVLAe8jiMzCJ610qEO7j/ys5TeI9SPt1nGaccLbhCcawz3T0KKV4sHrKxsZOnayDuuj3QMhVJn4AbzX7JYrbrg3NfP/d8fWztmBk2/ZvjWeYh25KoSoJ9KusQNqPbOP6ACIx9VWDgtfpcBNPFQoVk/iVhwuLrk2bR4PFQP8wyhcoJA3GDK3vWJ1xO+ddAx+LCihVRswpgQobe33WVzjtiRHn8aaadDOi1AF5xl0gOWEM9qasZ6Y8J5JU2O0lVQIDAQAB"
}

resource "cloudflare_record" "mxa" {
  zone_id=var.zone
  type="MX"
  name="mail"
  priority="10"
  value="mxa.eu.mailgun.org"
}

resource "cloudflare_record" "mxb" {
  zone_id=var.zone
  type="MX"
  name="mail"
  priority="10"
  value="mxb.eu.mailgun.org"
}


resource "cloudflare_page_rule" "cache_images" {
  zone_id = var.zone
  target = "https://imgz.org/*.*"
  priority = 1

  actions {
    browser_cache_ttl = 16070400
    cache_level = "cache_everything"
    edge_cache_ttl = 2419200
  }
}

